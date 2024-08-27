import logging
import os

from dotenv import load_dotenv

from github_events_api.data_storage import (
    create_db_and_tables,
    create_events,
    create_repository,
    find_repository_by_full_name,
    update_repository_etag,
)
from github_events_api.github_api import get_github_events_per_repo, get_repository_info

log = logging.getLogger(__name__)


def main():
    logging.info("Starting the process...")
    create_db_and_tables()

    load_dotenv(".env")
    personal_token = os.getenv("PERSONAL_TOKEN")

    # repo_owner = "IvaMarosov"
    # repo_name = "github_events_api"

    repo_owner = "facebookresearch"
    repo_name = "sapiens"

    # repo_owner = "linkedin"
    # repo_name = "Liger-Kernel"

    # repo_owner = "Permify"
    # repo_name = "permify"

    repo_full_name = f"{repo_owner}/{repo_name}"

    # check if repo is already present in "repositories" db table
    # if yes, get its etag to limit number of requests
    repo_record = find_repository_by_full_name(repo_full_name)
    if repo_record:
        repo_id = repo_record.id
        etag = repo_record.etag
    else:
        repo_info_response = get_repository_info(repo_owner, repo_name, personal_token)
        etag = None
        create_repository(repo_info_response, etag)
        repo_id = repo_info_response["id"]

    repo_events_response, new_etag = get_github_events_per_repo(
        repo_owner, repo_name, personal_token, etag
    )

    if repo_events_response:
        create_events(repo_events_response)
        update_repository_etag(repo_id, new_etag)


if __name__ == "__main__":
    main()
