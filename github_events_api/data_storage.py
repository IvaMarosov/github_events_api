import logging
from datetime import datetime
from typing import Sequence

import pandas as pd
from sqlmodel import Field, Session, SQLModel, create_engine, delete, select

from github_events_api.constants import SQLITE_URL

engine = create_engine(SQLITE_URL, echo=False)

log = logging.getLogger(__name__)


class Repository(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    owner: str
    full_name: str
    etag: str | None = Field(default=None)

    @classmethod
    def from_data(cls, data: dict, etag: str | None) -> "Repository":
        return Repository(
            id=int(data["id"]),
            name=data["name"],
            owner=data["owner"]["login"],
            full_name=data["full_name"],
            etag=etag,
        )


class Event(SQLModel, table=True):
    id: int = Field(primary_key=True)
    type: str = Field(nullable=False)
    actor_id: int = Field(nullable=False)
    repo_id: int = Field(nullable=False, foreign_key="repository.id")
    created_at: datetime

    @classmethod
    def from_data(cls, data: dict) -> "Event":
        return Event(
            id=int(data["id"]),
            type=data["type"],
            actor_id=data["actor"]["id"],
            repo_id=data["repo"]["id"],
            created_at=datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
        )


class Statistics(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True, description="Unique ID for statistics record."
    )
    repo_id: int = Field(
        nullable=False, foreign_key="repository.id", description="ID of repository."
    )
    event_type: str = Field(nullable=False, description="Type of event, e.g. WatchEvent.")
    avg_time_diff_secs: float | None = Field(
        nullable=True,
        description="Avg time difference between events of same type and repository. In seconds.",
    )

    @classmethod
    def from_df(cls, data: pd.Series) -> "Statistics":
        return Statistics(
            repo_id=data["repo_id"],
            event_type=data["type"],
            avg_time_diff_secs=data["avg_time_diff_secs"],
        )


def create_db_and_tables():
    """Start SQLite db and create tables defined by SQLModel."""
    SQLModel.metadata.create_all(engine)


def create_events(events_data: list[dict]) -> None:
    """Store events into db 'Event' table."""
    events = [Event.from_data(e) for e in events_data]
    with Session(engine) as session:
        count = 0
        for e in events:
            # verify that the event is not in the table already
            statement = select(Event).where(Event.id == e.id)
            results = session.exec(statement)
            if results.first():
                log.warn(f"Event with id={e.id} is already present in the database, skipping...")
            else:
                session.add(e)
                count += 1

        log.info(
            f"Adding {count} new events for repository {e.repo_id} into db. "
            f"Originally got {len(events)} in request to Github API."
        )
        session.commit()


def create_repository(repo_data: dict, etag: str | None) -> None:
    """Store repository information into 'Repository' table in db."""
    # get info about repository from single event
    repository = Repository.from_data(repo_data, etag)

    with Session(engine) as session:
        session.add(repository)
        session.commit()


def create_statistics(data: pd.DataFrame) -> None:
    """Store statistics into 'Statistics' db table."""
    stats = [Statistics.from_df(s) for _, s in data.iterrows()]
    with Session(engine) as session:
        for stat in stats:
            session.add(stat)
        session.commit()


def find_repository_by_full_name(repo_full_name: str) -> Repository | None:
    """
    Get single repository from 'Repository' table based on its full name.
    Full name is put together from repository owner and repository name.
    Return None if no repository found for given full name.

    Example:
        - owner: datamole-ai
        - name: edvart
        => full_name == datamole-ai/edvart
    """
    with Session(engine) as session:
        statement = select(Repository).where(Repository.full_name == repo_full_name)
        results = session.exec(statement)
        # assumption: there is only one repository for each full name
        # full name consist of repository owner and repository name
        repository = results.first()

        if repository is None:
            log.warn(
                f"No record for repository with full name '{repo_full_name}' found in database."
            )
            return None

        return repository


def find_repository_by_owner(repo_owner: str) -> Sequence[Repository] | None:
    """
    Get list of repositories based on their owner.
    Return None if no such repository found.
    """
    with Session(engine) as session:
        statement = select(Repository).where(Repository.owner == repo_owner)
        results = session.exec(statement).all()

        if results is None:
            log.warn(f"No record for repository owner '{repo_owner}' found in database.")
            return None

        return results


def find_repository_by_name(repo_name: str) -> Sequence[Repository] | None:
    """
    Get list of repositories based on repository name.
    Return None if no such repository found.
    """
    with Session(engine) as session:
        statement = select(Repository).where(Repository.name == repo_name)
        results = session.exec(statement).all()

        if results is None:
            log.warn(f"No record for repository name '{repo_name}' found in database.")
            return None

        return results


def find_all_events() -> list[Event]:
    """Get list of all events stored in 'Event' db table."""
    with Session(engine) as session:
        statement = select(Event)
        result = session.exec(statement)

        return list(result.all())


def find_all_stats() -> list[Statistics]:
    """Get list of statistics stored in 'Statistics' db table."""
    with Session(engine) as session:
        statement = select(Statistics)
        result = session.exec(statement)
        return list(result.all())


def find_stats_by_params(repo_owner: str, repo_name: str, event_type: str) -> list[Statistics]:
    """
    Get filtered list of statistics from 'Statistics' db table.
    User can filter by one or more parameters:
    - repository owner
    - repository name
    - event type

    If none of the parameters is filled, it returns list of all statistics in db.
    If both repo_owner and repo_name is defined, statistics will be filtered based on
    repository full name.
    """
    all_stats = find_all_stats()
    log.debug(f"Found {len(all_stats)} total statistics records.")

    repository = find_repository_by_full_name(f"{repo_owner}/{repo_name}")

    if repository is None:
        raise KeyError(f"There is no repository for owner: {repo_owner} and name: {repo_name}.")

    repo_stats = [s for s in all_stats if s.repo_id == repository.id]

    event_stats = [s for s in repo_stats if s.event_type == event_type]

    return event_stats


def update_repository_etag(repo_id: int, new_etag: str) -> None:
    """
    Update etag for repository based on the latest request to Github Events API.
    More info in
    https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28#about-github-events
    """
    with Session(engine) as session:
        statement = select(Repository).where(Repository.id == repo_id)
        results = session.exec(statement)
        repository = results.one()
        repository.etag = new_etag
        session.add(repository)
        session.commit()


def delete_statistics():
    """Delete records from Statistics table."""
    with Session(engine) as session:
        results = session.exec(delete(Statistics))
        session.commit()
        log.info(f"Deleted {results.rowcount} records from Statistics db table.")
