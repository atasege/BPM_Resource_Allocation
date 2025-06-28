import pandas as pd
import datetime

# code from Mr. Kunkler, slightly modified to keep zero durations
def start_end_event_log_all(event_log,
                            timestamp_name='time:timestamp',
                            start_label='start',
                            complete_label='complete'):
    
    starts = event_log[event_log['lifecycle:transition'] == start_label].copy()
    completes = event_log[event_log['lifecycle:transition'] == complete_label].copy()

    
    merged = pd.merge(
        starts,
        completes,
        on=['case:concept:name', 'concept:name', 'EventID'],
        suffixes=('_start', '_complete')
    )

    
    merged['time:timestamp_start'] = pd.to_datetime(merged['time:timestamp_start'])
    merged['time:timestamp_complete'] = pd.to_datetime(merged['time:timestamp_complete'])
    merged['duration'] = merged['time:timestamp_complete'] - merged['time:timestamp_start']
    merged['duration_seconds'] = merged['duration'] / pd.Timedelta(seconds=1)
    merged['duration_ms'] = merged['duration'] / pd.Timedelta(milliseconds=1)
    merged['duration_hours'] = merged['duration'] / pd.Timedelta(hours=1)

    
    merged = merged[merged['duration_seconds'] >= 0]

    
    merged = merged.sort_values(by=['case:concept:name', 'time:timestamp_start'])

    return merged


log_df = pd.read_csv('acr_Raw.csv')


starts = log_df[log_df['lifecycle:transition'] == 'start'].copy()
completes = log_df[log_df['lifecycle:transition'] == 'complete'].copy()

starts['event_index'] = (
    starts.sort_values(['time:timestamp'])
          .groupby(['case:concept:name', 'concept:name'])
          .cumcount()
)
completes['event_index'] = (
    completes.sort_values(['time:timestamp'])
             .groupby(['case:concept:name', 'concept:name'])
             .cumcount()
)

for df in [starts, completes]:
    df['EventID'] = (
        df['case:concept:name'].astype(str) + "_" +
        df['concept:name'].astype(str) + "_" +
        df['event_index'].astype(str)
    )


log_with_eventids = pd.concat([starts, completes], axis=0)


result_df = start_end_event_log_all(log_with_eventids)

# remove unnecessary time info (.00.00.00 etc)
result_df['time:timestamp_start'] = result_df['time:timestamp_start'].dt.strftime('%Y-%m-%d %H:%M:%S')
result_df['time:timestamp_complete'] = result_df['time:timestamp_complete'].dt.strftime('%Y-%m-%d %H:%M:%S')

# renaming so that it works with simulation model miner
result_df = result_df.rename(columns={
    'concept:name': 'Activity',
    'org:resource_start': 'Resource', 
    'case:concept:name': 'Case ID',
    'time:timestamp_start': 'Start Timestamp',
    'time:timestamp_complete': 'Complete Timestamp'
})

# Save
result_df.to_csv('acr_durations_zeros.csv', index=False)
print("Saved result to acr_durations_zeros.csv")
print(f"Columns in output: {result_df.columns.tolist()}")


