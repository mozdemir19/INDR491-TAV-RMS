import pandas as pd
import numpy as np
from functools import reduce
import itertools

def newDF(tasks, resources, defaultValue=0):
    return pd.DataFrame(defaultValue, index=tasks.TaskId, columns=resources.ResourceId)

def read_prios(tasks, resources, priorityContent, scores):

    priorities = [newDF(tasks, resources, 0.0) for _ in range(priorityContent['PriorityId'].max())]

    for i in range(len(priorities)):
        df = priorities[i]
        df.loc[priorityContent[(priorityContent['PriorityId'] == i + 1) & (priorityContent['ObjectType'] == 'Task')]['ObjectId'].values,
            priorityContent[(priorityContent['PriorityId'] == i + 1) & (priorityContent['ObjectType'] == 'Resource')]['ObjectId'].values] = scores[i]
        
        priorities[i] = df

    return priorities


def priorityGroupVars(tasks, resources, priorityContent):
    priorityVars = []

    for i in range(1, priorityContent.PriorityId.max() + 1):
        df = newDF(tasks, resources, 0)
        df.loc[priorityContent.loc[(priorityContent['PriorityId'] == i) & (priorityContent['ObjectType'] == 'Task')]['ObjectId'].values,
               priorityContent.loc[(priorityContent['PriorityId'] == i) & (priorityContent['ObjectType'] == 'Resource')]['ObjectId'].values] = 1
        priorityVars.append(df)

    
    priorityVars.append(newDF(tasks, resources, 1))
    
    return priorityVars

def compute_compatibilities(tasks, resources):
    compatibilities = newDF(tasks, resources)

    for index, row in tasks.iterrows():
        aircraftAndTaskType = resources[(resources[row['AircraftTypeCode'] + 'P'] == 1) & (resources[row['TaskTypeName']] == 1)].ResourceId
        if not pd.isna(row['ArrivalCategory']):
            arrivalCat = resources[resources[row['ArrivalCategory']] == 1].ResourceId
        if not pd.isna(row['DepartureCategory']):
            departureCat = resources[resources[row['DepartureCategory']] == 1].ResourceId
        if not pd.isna(row['ArrivalServiceType']):
            arrivalServiceType = resources[resources[row['ArrivalServiceType']] == 1].ResourceId
        if not pd.isna(row['DepartureServiceType']):
            departureServiceType = resources[resources[row['DepartureServiceType']] == 1].ResourceId
        
        cols = aircraftAndTaskType[aircraftAndTaskType.isin(arrivalCat) & aircraftAndTaskType.isin(departureCat) & aircraftAndTaskType.isin(arrivalServiceType) & aircraftAndTaskType.isin(departureServiceType)]
        compatibilities.loc[row['TaskId'], cols] = 1 

    return compatibilities


def trunc_ts(series, tasks):
    time_series = pd.Series(True,
                        index= pd.date_range(start=tasks.StartDateTime.min()
                                             ,end=tasks.EndWithBuffer.max()
                                             ,freq=pd.offsets.Minute(1)))
    
    return time_series.truncate(series['StartDateTime'], series['EndWithBuffer'])

def heatmap(tasks):
    

    taskHeatmap = tasks.apply(trunc_ts, tasks=tasks, axis=1).T
    taskHeatmap[taskHeatmap == True] = 1
    taskHeatmap = taskHeatmap.fillna(0).astype(int)
    taskHeatmap.columns = tasks.TaskId.values
    taskHeatmap = taskHeatmap.drop_duplicates()

    return taskHeatmap

def utilities(data):
    tasks = pd.read_excel(data, sheet_name='Tasks')
    resources = pd.read_excel(data, sheet_name='Resources')
    scorePairs = pd.read_excel(data, sheet_name='ScorePairs')

    utilities = newDF(tasks, resources, 300.0)

    for index, row in scorePairs.iterrows():
        utilities.loc[row['TaskId'], row['ResourceId']] = row['ScoreValue']

    return utilities

def resource_utilization(resource, tasks, x):
    sum = []
    for index, row in tasks.iterrows():
        sum.append(x[row.TaskId, resource] * int(row['Duration-min']))
    
    return sum
