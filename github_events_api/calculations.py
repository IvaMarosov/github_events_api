import numpy as np
import pandas as pd

from github_events_api.data_storage import Event


def load_events_data_into_df(events: list[Event]) -> pd.DataFrame:
    """Transform list of Events into dataframe for further analysis."""
    events_df = pd.DataFrame.from_records([e.model_dump() for e in events])
    events_df["created_at"] = pd.to_datetime(events_df["created_at"])

    return events_df


def _calculate_rolling_average_time_diff(events_group: pd.DataFrame) -> float:
    """
    Get average time difference between events of given group.
    Average is calculated over either last 7 days (starting from most recent date in the data) or
    500 events, which happens first.
    The result is in seconds.
    """
    # select relevant events
    # either last 7 days or 500 events, which one is sooner
    last_date = events_group["created_at"].max()
    start_date = last_date - pd.Timedelta(days=7)
    date_mask = events_group["created_at"] >= start_date

    eligable_events = events_group.loc[date_mask].head(500)
    # get time difference between events
    eligable_events["time_diff"] = eligable_events["created_at"].diff()

    return eligable_events["time_diff"].mean().total_seconds()


def calculate_rolling_avg_time_diff_per_event_type(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create dataframe with repository id, event type and calculated average time difference between
    events
    Get average time difference between events of same event type. Average is calculated over
    either last 7 days (starting from most recent date in the data) or 500 events, which happens
    first.
    """
    # sort events
    data = data.sort_values(by=["repo_id", "type", "created_at"])

    # get time diff between consecutive events
    avg_time_diff_secs = (
        data.groupby(["repo_id", "type"])
        .apply(lambda x: pd.Series({"avg_time_diff_secs": _calculate_rolling_average_time_diff(x)}))
        .reset_index()
    )

    # transform np.nan values in averages to None for later storage in db
    avg_time_diff_secs["avg_time_diff_secs"] = avg_time_diff_secs["avg_time_diff_secs"].replace(
        {np.nan: None}
    )

    return avg_time_diff_secs
