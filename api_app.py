import logging

from fastapi import FastAPI

from github_events_api.data_storage import (
    Statistics,
    find_all_stats,
    find_stats_by_params,
)

log = logging.getLogger(__name__)

API_TITLE = "AVG time between Github Events API"
API_DESCR = "This API will give you average time difference between consequtive "
"Github events of same type for given repository. The metric is in seconds."
API_VERSION = "1.0.0"

app = FastAPI(title=API_TITLE, description=API_DESCR, version=API_VERSION)


@app.get("/", response_model=list[Statistics])
def get_all_stats():
    return find_all_stats()


@app.get("/statistics/")
def get_stats_by_params(repo_owner: str, repo_name: str, event_type: str) -> dict:
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
