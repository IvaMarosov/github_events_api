import logging
import os

from dotenv import load_dotenv

from github_events_api.calculations import (
    calculate_rolling_avg_time_diff_per_event_type,
    load_events_data_into_df,
)
from github_events_api.configuation import (
    limit_number_of_repos,
    load_repository_config,
)
from github_events_api.constants import PERSONAL_TOKEN
from github_events_api.data_storage import (
    create_db_and_tables,
    create_events,
    create_repository,
    create_statistics,
    delete_statistics,
    find_all_events,
    find_repository_by_full_name,
    update_repository_etag,
)
from github_events_api.github_api import get_github_events_per_repo, get_repository_info

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

REPOS_THRESHOLD = 5
REPOS_CONFIG = "repositories.yaml"


def main():
    logging.info("Starting the download process...")
    create_db_and_tables()

    # access personal token for requests to Github API
    load_dotenv(".env")
    personal_token = os.getenv(PERSONAL_TOKEN)

    # get list of repositories to collect info about
    config = load_repository_config(REPOS_CONFIG)
    repos = limit_number_of_repos(config, REPOS_THRESHOLD)

    for repo in repos:
        # check if repo is already present in "repositories" db table
        # if yes, get its etag to limit number of requests
        repo_record = find_repository_by_full_name(repo.full_name)
        if repo_record:
            repo_id = repo_record.id
            etag = repo_record.etag
        # if no, request repo info from GH API and store it into Repository db table
        else:
            repo_info_response = get_repository_info(repo, personal_token)
            etag = None
            create_repository(repo_info_response, etag)
            repo_id = repo_info_response["id"]

        # download events for given repository
        repo_events_response, new_etag = get_github_events_per_repo(repo, personal_token, etag)

        # if there are any events, store them into db
        if repo_events_response:
            create_events(repo_events_response)
            update_repository_etag(repo_id, new_etag)

    # whipe Statistics db table before adding new calculations
    delete_statistics()

    # calculate statistics and save them into db
    events = find_all_events()
    events_df = load_events_data_into_df(events)
    statistics = calculate_rolling_avg_time_diff_per_event_type(events_df)
    create_statistics(statistics)


if __name__ == "__main__":
    main()
