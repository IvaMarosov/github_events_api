import logging

from fastapi import FastAPI

from github_events_api.data_storage import (
    Statistics,
    find_all_stats,
    find_stats_by_params,
)

log = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def get_all_stats() -> list[Statistics]:
    return find_all_stats()


@app.get("/statistics/")
def get_stats_by_params(
    repo_owner: str | None = None, repo_name: str | None = None, event_type: str | None = None
) -> dict:
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
