import numpy as np
import pandas as pd
import pytest

from github_events_api.calculations import (
    _calculate_rolling_average_time_diff,
    calculate_rolling_avg_time_diff_per_event_type,
    load_events_data_into_df,
)
from github_events_api.constants import EVENT_AVG_TIME_DIFF, EVENT_CREATED_AT, EVENT_TYPE
from github_events_api.data_storage import Event

datetime_format = "%Y-%m-%dT%H:%M:%SZ"
test_date = "2024-08-28T00:00:00Z"
event1 = Event.from_data(
    {
        "id": 1,
        "type": "WatchEvent",
        "actor": {"id": 11},
        "repo": {"id": 111},
        "created_at": test_date,
    }
)
event2 = Event.from_data(
    {
        "id": 2,
        "type": "CreateEvent",
        "actor": {"id": 12},
        "repo": {"id": 111},
        "created_at": test_date,
    }
)
events = [event1, event2]


@pytest.mark.parametrize(
    "file_name, event_type, expected",
    (
        ["events_over_500.csv", "WatchEvent", 141.86],
        ["events_7_days.csv", "IssueCommentEvent", 15027.12],
        ["events_one_per_type.csv", "WatchEvent", np.nan],
    ),
)
def test_calculate_rolling_average_time_diff(file_name, event_type, expected, test_data_file_path):
    df = pd.read_csv(test_data_file_path(file_name))
    df[EVENT_CREATED_AT] = pd.to_datetime(df[EVENT_CREATED_AT])
    events = df[df[EVENT_TYPE] == event_type]

    result = round(_calculate_rolling_average_time_diff(events), 2)
    np.testing.assert_equal(result, expected)


def test_load_events_into_df():
    result_df = load_events_data_into_df(events)
    expected_df = pd.DataFrame(
        [event1.model_dump(), event2.model_dump()],
    )
    assert all(result_df == expected_df)


@pytest.mark.parametrize(
    "file_name, exp_df_len, exp_nunique_events, exp_sum_avg_time_diff",
    (
        ["events_over_500.csv", 7, 7, 29512.47],
        ["events_7_days.csv", 1, 1, 15027.12],
        ["events_one_per_type.csv", 2, 2, 0],
    ),
)
def test_calculate_rolling_avg_time_diff_main(
    file_name, exp_df_len, exp_nunique_events, exp_sum_avg_time_diff, test_data_file_path
):
    df = pd.read_csv(test_data_file_path(file_name))
    df[EVENT_CREATED_AT] = pd.to_datetime(df[EVENT_CREATED_AT])
    avg_df = calculate_rolling_avg_time_diff_per_event_type(df)

    assert len(avg_df) == exp_df_len
    assert avg_df[EVENT_TYPE].nunique() == exp_nunique_events
    assert round(avg_df[EVENT_AVG_TIME_DIFF].sum(), 2) == exp_sum_avg_time_diff
