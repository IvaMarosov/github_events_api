import pytest

from github_events_api.configuation import (
    limit_number_of_repos,
    load_repository_config,
    open_config,
)


@pytest.mark.parametrize(
    "file_name, exp_len",
    [
        pytest.param("repo_config_under_5.yaml", 1, id="under_threshold"),
        pytest.param("repo_config_over_5.yaml", 5, id="over_threshold"),
    ],
)
def test_open_config(file_name, exp_len, test_data_file_path):
    result = open_config(test_data_file_path(file_name))

    assert len(result) == exp_len


@pytest.mark.parametrize(
    "file_name, exp_len, exp_first_owner, exp_first_name",
    [
        pytest.param("repo_config_under_5.yaml", 1, "owner_1", "name_1", id="under_threshold"),
        pytest.param("repo_config_over_5.yaml", 5, "owner_1", "name_1", id="over_threshold"),
    ],
)
def test_load_repository_config(
    file_name, exp_len, exp_first_owner, exp_first_name, test_data_file_path
):
    config_file = test_data_file_path(file_name)
    result = load_repository_config(config_file)

    assert len(result) == exp_len
    assert result[0].owner == exp_first_owner
    assert result[0].name == exp_first_name


@pytest.mark.parametrize(
    "file_name, exp_len",
    [
        pytest.param("repo_config_under_5.yaml", 1, id="under_threshold"),
        pytest.param("repo_config_over_5.yaml", 3, id="over_threshold"),
    ],
)
def test_limit_number_of_repos(file_name, exp_len, test_data_file_path):
    config_file = test_data_file_path(file_name)
    repos = load_repository_config(config_file)
    result = limit_number_of_repos(repos, threshold=3)

    assert len(result) == exp_len
