import logging

import pytest
import requests
import requests_mock

from github_events_api.configuation import RepositoryConfig
from github_events_api.github_api import (
    GITHUB_API_REPOS_URL,
    _transform_etag,
    get_github_events_per_repo,
    get_repository_info,
)

test_repo_config = RepositoryConfig(**{"owner": "test-owner", "name": "test-repo"})

test_date = "2024-08-28T00:00:00Z"
events_data = [
    {
        "id": 1,
        "type": "WatchEvent",
        "actor": {"id": 11},
        "repo": {"id": 111},
        "created_at": test_date,
    },
    {
        "id": 2,
        "type": "CreateEvent",
        "actor": {"id": 12},
        "repo": {"id": 111},
        "created_at": test_date,
    },
]


@pytest.mark.parametrize(
    "input_str, exp_result",
    [
        ("etag", None),
        ('W/"12345"', "12345"),
    ],
)
def test_transform_etag(input_str, exp_result):
    assert _transform_etag(input_str) == exp_result


@pytest.fixture(scope="module")
def mock_github_api():
    with requests_mock.Mocker() as m:
        yield m


def test_get_repository_info_success(mock_github_api):
    repo_data = {
        "id": 1,
        "name": "test-repo",
        "owner": {"login": "test-owner"},
        "full_name": "test_owner/test-repo",
    }
    mock_github_api.get(f"{GITHUB_API_REPOS_URL}/test-owner/test-repo", json=repo_data)

    result = get_repository_info(test_repo_config, "token")

    assert result == repo_data, f"Expected {repo_data}, but got {result}"
    assert mock_github_api.last_request.headers["Authorization"] == "Bearer token"


def test_get_repository_info_non_existent_repo(mock_github_api):
    mock_github_api.get(
        f"{GITHUB_API_REPOS_URL}/test-owner/test-repo", status_code=404, text="404 Client Error"
    )

    with pytest.raises(requests.HTTPError, match="404 Client Error"):
        get_repository_info(test_repo_config, "token")


def test_get_github_events_per_repo_success(mock_github_api):
    mock_github_api.get(
        f"{GITHUB_API_REPOS_URL}/test-owner/test-repo/events",
        json=events_data,
        headers={"ETag": 'W/"123"'},
    )

    result, etag = get_github_events_per_repo(test_repo_config, "token", None)

    assert result == events_data, f"Expected {events_data}, but got {result}"
    assert etag == "123"


def test_get_github_events_per_repo_no_new_data(mock_github_api, caplog):
    mock_github_api.get(f"{GITHUB_API_REPOS_URL}/test-owner/test-repo/events", status_code=304)

    with caplog.at_level(logging.INFO):
        result, etag = get_github_events_per_repo(test_repo_config, "token", 'W/"123"')

    assert result is None
    assert etag is None
    assert f"There are no new events for {test_repo_config.full_name} repository." in caplog.text
