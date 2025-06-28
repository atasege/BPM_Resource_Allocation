import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from collections import defaultdict

def analyze_multitasking(df, case_col, activity_col, resource_col, finishtime_col):
    df = df.sort_values(by=finishtime_col)
    
    resource_timelines = defaultdict(list)
    
    for _, row in df.iterrows():
        resource_val = row[resource_col]  
        completion_time = row[finishtime_col]  
        resource_timelines[resource_val].append(completion_time)
    
    concurrent_counts = defaultdict(list)
    window_size = timedelta(minutes=60)
    
    for resource_val, timestamps in resource_timelines.items():
        if len(timestamps) <= 1:
            continue
            
        timestamps.sort()
        
        for i, time_point in enumerate(timestamps):
            window_start = time_point - window_size
            window_end = time_point
            
            activities_in_window = sum(1 for t in timestamps if window_start <= t <= window_end)
            concurrent_counts[resource_val].append(activities_in_window)
    
    concurrency1 = {}
    for resource_val, counts in concurrent_counts.items():
        if counts:
            concurrency1[resource_val] = sum(counts) / len(counts)
        else:
            concurrency1[resource_val] = 1
    
    return concurrency1

def estimate_start_times_multitasking(log_file, output_file):
    df = pd.read_csv(log_file)
    
    case_col = "Case ID"
    activity_col = "Activity" 
    resource_col = "Resource"
    finishtime_col = "Complete Timestamp"
    
    df[finishtime_col] = pd.to_datetime(df[finishtime_col])
    df = df.sort_values(by=finishtime_col)
    
    result_df = df.copy()
    startclmn = 'Start Timestamp'
    result_df[startclmn] = pd.NaT
    
    concurrency1 = analyze_multitasking(df, case_col, activity_col, resource_col, finishtime_col)
    
    caseSeq333 = defaultdict(list)
    for _, row in df.iterrows():
        case_id = row[case_col]
        activity_val = row[activity_col]  
        timestamp = row[finishtime_col]
        
        caseSeq333[case_id].append((activity_val, timestamp))
    
    activity_gaps = defaultdict(list)
    for case_id, activities in caseSeq333.items():
        activities.sort(key=lambda x: x[1])
        
        for i in range(len(activities) - 1):
            current_activity = activities[i][0]
            current_time = activities[i][1]
            next_time = activities[i+1][1]
            
            gap_minutes = (next_time - current_time).total_seconds() / 60
            if 1 <= gap_minutes <= 1440:
                activity_gaps[current_activity].append(gap_minutes)
    
    activity_durations = {}
    for activity_name, gaps in activity_gaps.items():
        if gaps:
            activity_durations[activity_name] = max(1, np.percentile(gaps, 25))
        else:
            activity_durations[activity_name] = 30
    
    if activity_durations:
        default_duration = np.mean(list(activity_durations.values()))
    else:
        default_duration = 30
    
    for activity_name in df[activity_col].unique():  
        if activity_name not in activity_durations:
            activity_durations[activity_name] = default_duration
    
    first_activities = {}
    for case_id, activities in caseSeq333.items():
        if activities:
            activities.sort(key=lambda x: x[1])
            first_activities[case_id] = activities[0][0]
    
    last_case_activity = {}
    last_resource_activity = {}
    
    for idx, row in df.iterrows():
        case_id = row[case_col]
        resource_val = row[resource_col]  
        activity_val = row[activity_col]  
        completion_time = row[finishtime_col]
        
        # this (assign seriousness) is specific for my thesis, if you wanna use this code for another log, change this to the most common first event within all cases.
        if activity_val == "Assign seriousness" and case_id in first_activities and first_activities[case_id] == activity_val:
            random_duration = random.uniform(1, 60)
            start_time = completion_time - timedelta(minutes=random_duration)
            
            # microseconds not needed
            start_time = start_time.replace(microsecond=0)
            
            result_df.at[idx, startclmn] = start_time
            
            last_case_activity[case_id] = completion_time
            last_resource_activity[resource_val] = completion_time
            continue
        
        multitaskFaktor = concurrency1.get(resource_val, 1)
        
        if multitaskFaktor > 10:
            multitaskFaktor = 10

        # 0.70 means %30 of estimated duration is assumed as waiting times. 
        # i chose this so for helpdesk. if you are using this code for another log, change it according to its characteristics
        adjustmentPercentage = max(0.1, 0.70 / multitaskFaktor)
        
        if case_id in last_case_activity:
            prev_completion = last_case_activity[case_id]
            raw_duration = (completion_time - prev_completion).total_seconds() / 60
        elif resource_val in last_resource_activity:
            prev_completion = last_resource_activity[resource_val]
            raw_duration = (completion_time - prev_completion).total_seconds() / 60
        else:
            raw_duration = activity_durations.get(activity_val, default_duration)
        
        adjusted_duration = raw_duration * adjustmentPercentage
        
        if adjusted_duration <= 0:
            adjusted_duration = 1
        elif adjusted_duration > 360:
            if activity_val in activity_durations and activity_durations[activity_val] < 360:
                adjusted_duration = activity_durations[activity_val]
            else:
                adjusted_duration = random.uniform(30, 360)
        
        start_time = completion_time - timedelta(minutes=adjusted_duration)
        
        # remove microseconds etcc
        start_time = start_time.replace(microsecond=0)
        
        last_case_activity[case_id] = completion_time
        last_resource_activity[resource_val] = completion_time
        
        result_df.at[idx, startclmn] = start_time
    
    result_df.to_csv(output_file, index=False)
    
    print(f"Processed log saved to {output_file}")
    return result_df

import os

# save to same file
script_dir = os.path.dirname(os.path.abspath(__file__))

input_file = "BPM_Resource_Allocation/preprocessing/helpdesk_Raw.csv"
output_filename = "finaleStartsEstimated.csv"
output_file = os.path.join(script_dir, output_filename)

result_df = estimate_start_times_multitasking(input_file, output_file)