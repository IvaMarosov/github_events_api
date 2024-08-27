import logging

import yaml

log = logging.getLogger(__name__)


def open_config(file_path: str) -> list[dict]:
    """Open yaml configuration with list of repositories."""
    with open(file_path, "r") as f:
        yaml_config = yaml.safe_load(f)

    return yaml_config


def limit_number_of_repos(config: list[dict], threshold: int) -> list[dict]:
    """Get only defined number of repositories from configuration."""
    if len(config) > threshold:
        log.warn(
            f"Number of configured repositories {len(config)} is over the threshold {threshold}. "
            f"Limiting to first {threshold} repositories."
        )

        return config[:threshold]

    return config
