import logging
import os

from dotenv import load_dotenv

from github_events_api.configuation import limit_number_of_repos, open_config
from github_events_api.data_storage import (
    create_db_and_tables,
    create_events,
    create_repository,
    find_repository_by_full_name,
    update_repository_etag,
)
from github_events_api.github_api import get_github_events_per_repo, get_repository_info

log = logging.getLogger(__name__)

REPOS_THRESHOLD = 5


def main():
    logging.info("Starting the process...")
    create_db_and_tables()

    load_dotenv(".env")
    personal_token = os.getenv("PERSONAL_TOKEN")

    config = open_config("repositories.yaml")
    repos = limit_number_of_repos(config, REPOS_THRESHOLD)

    for repo in repos:
        repo_owner = repo["owner"]
        repo_name = repo["name"]
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
