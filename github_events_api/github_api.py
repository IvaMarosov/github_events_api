import logging
import re

import requests
from requests.adapters import HTTPAdapter, Retry

log = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/"
GITHUB_API_REPOS_URL = f"{GITHUB_API_URL}/repos"


# Github API has default 30, max limit 100
PER_PAGE_EVENTS = 100


def _transform_etag(etag_str: str) -> str | None:
    """Remove 'W/' from etag string."""
    match = re.search(r'W/"(.+)"', etag_str)
    if match:
        return match.group(1)
    return None


def _retry_request(url: str, headers: dict, params: dict) -> requests.Response:
    """Rerun GET request to given url if failed with specified errors."""
    retry_strategy = Retry(
        total=4,  # max number of retries
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    # send request using the session object
    response = session.get(url=url, headers=headers, params=params)

    return response


def get_github_events_per_repo(
    repo_owner: str, repo_name: str, personal_token: str, last_etag: str | None
) -> tuple[list[dict] | None, str | None]:
    """
    Send get request to Github Events API endpoint. Include retries in case of errors which
    could be sensitive to load. "last_etag" serves to request only newly occured events for given
    repository. Handle pagination.

    :return:
    - tuple of
        - list of repository events or None if there are no new events
        - etag of the most recent request; None if no new events
    """
    url = f"{GITHUB_API_REPOS_URL}/{repo_owner}/{repo_name}/events"
    header = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {personal_token}",
        "If-None-Match": f'"{last_etag}"',
    }
    params = {"per_page": PER_PAGE_EVENTS}

    log.info(f"Sending request to get events info from {url}...")

    # send request using the session object
    response = _retry_request(url=url, headers=header, params=params)

    # handle no new events
    if response.status_code == 304:
        log.info(f"There are no new events for {repo_owner}/{repo_name} repository.")
        return None, None

    response.raise_for_status()
    responses_list = response.json()

    # pagination
    last_page_info = response.links.get("last")

    if last_page_info:
        last_page_url = last_page_info["url"]
        last_page_num = int(last_page_url.split("&page=")[1])
        for n in range(2, last_page_num + 1):
            next_response = _retry_request(
                url=f"{url}", headers=header, params={**params, "page": n}
            )
            next_response.raise_for_status()
            responses_list.extend(next_response.json())

    log.info(f"Received {len(responses_list)} records.")

    # capture etag from the first request == most recent events
    etag = _transform_etag(response.headers["ETag"])

    return responses_list, etag


def get_repository_info(repo_owner: str, repo_name: str, personal_token: str) -> dict:
    """Get information about repository through Github API."""
    url = f"{GITHUB_API_REPOS_URL}/{repo_owner}/{repo_name}"
    log.info(f"Sending request to get events info from {url}...")

    response = _retry_request(
        url=url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {personal_token}",
        },
        params={},
    )

    response.raise_for_status()

    return response.json()
