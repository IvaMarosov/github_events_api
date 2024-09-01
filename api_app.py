import logging

from fastapi import FastAPI, HTTPException

from github_events_api.data_storage import (
    Statistics,
    check_database_exists,
    find_all_stats,
    find_stats_by_params,
)

log = logging.getLogger(__name__)

API_TITLE = "AVG time between Github Events API"
API_DESCR = "This API will give you average time difference between following "
"Github events of same type for given repository. The metric is in seconds."
API_VERSION = "1.0.0"

app = FastAPI(title=API_TITLE, description=API_DESCR, version=API_VERSION)


def verify_database():
    if not check_database_exists():
        raise HTTPException(status_code=500, detail="Database does not exist.")


@app.get("/", response_model=list[Statistics])
def get_all_stats():
    verify_database()
    return find_all_stats()


@app.get("/statistics/")
def get_stats_by_params(repo_owner: str, repo_name: str, event_type: str) -> dict:
    verify_database()
    log.debug(
        f"get_stats_by_params called with repo_owner={repo_owner}, repo_name={repo_name}, "
        f"event_type={event_type}"
    )
    stats = find_stats_by_params(
        repo_owner=repo_owner,
        repo_name=repo_name,
        event_type=event_type,
    )

    return {
        "query": {"repo_owner": repo_owner, "repo_name": repo_name, "event_type": event_type},
        "result": stats,
    }
