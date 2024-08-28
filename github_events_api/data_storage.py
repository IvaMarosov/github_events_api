import logging
from datetime import datetime

import pandas as pd
from sqlmodel import Field, Session, SQLModel, create_engine, select

SQLITE_FILENAME = "data/sql_model.db"
SQLITE_URL = f"sqlite:///{SQLITE_FILENAME}"

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
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(nullable=False)
    event_type: str = Field(nullable=False, foreign_key="repository.id")
    avg_time_diff_secs: float | None = Field(nullable=True)

    @classmethod
    def from_df(cls, data: pd.Series) -> "Statistics":
        return Statistics(
            repo_id=data["repo_id"],
            event_type=data["type"],
            avg_time_diff_secs=data["avg_time_diff_secs"],
        )


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_events(events_data: list[dict]) -> None:
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
    # get info about repository from single event
    repository = Repository.from_data(repo_data, etag)

    with Session(engine) as session:
        session.add(repository)
        session.commit()


def create_statistics(data: pd.DataFrame) -> None:
    stats = [Statistics.from_df(s) for _, s in data.iterrows()]
    with Session(engine) as session:
        for stat in stats:
            session.add(stat)
        session.commit()


def find_repository_by_full_name(repo_full_name: str) -> Repository | None:
    with Session(engine) as session:
        statement = select(Repository).where(Repository.full_name == repo_full_name)
        results = session.exec(statement)
        repository = results.first()

        if repository is None:
            log.info(f"No record for repository '{repo_full_name}' found in database.")
            return None

        return repository


def find_all_events() -> list[Event]:
    with Session(engine) as session:
        statement = select(Event)
        result = session.exec(statement)

        return list(result.all())


def update_repository_etag(repo_id: int, new_etag: str) -> None:
    with Session(engine) as session:
        statement = select(Repository).where(Repository.id == repo_id)
        results = session.exec(statement)
        repository = results.one()
        repository.etag = new_etag
        session.add(repository)
        session.commit()
