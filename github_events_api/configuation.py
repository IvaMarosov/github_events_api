import logging

import yaml
from pydantic import BaseModel

log = logging.getLogger(__name__)


class RepositoryConfig(BaseModel):
    owner: str
    name: str


def open_config(file_path: str) -> list[dict]:
    """Open yaml configuration with list of repositories."""
    with open(file_path, "r") as f:
        yaml_config = yaml.safe_load(f)

    return yaml_config


def load_repository_config(file_path: str) -> tuple[RepositoryConfig, ...]:
    """Load repositories' configuration."""
    repos_config = open_config(file_path)

    return tuple([RepositoryConfig(**r) for r in repos_config])


def limit_number_of_repos(
    repos: tuple[RepositoryConfig, ...], threshold: int
) -> tuple[RepositoryConfig, ...]:
    """Get only defined number of repositories from configuration."""
    if len(repos) > threshold:
        log.warning(
            f"Number of configured repositories {len(repos)} is over the threshold {threshold}. "
            f"Limiting to first {threshold} repositories."
        )

        return repos[:threshold]

    return repos
