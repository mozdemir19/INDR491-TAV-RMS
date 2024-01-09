import pandas as pd
import numpy as np
import utils
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

assignments = pd.read_csv('winter_assignments.csv',index_col=0)
tasks = pd.read_excel('RMS-MultiKPI-Input-KisDonemi-GercekVeri.xlsx', sheet_name='Tasks')
resources = pd.read_excel('RMS-MultiKPI-Input-YazDonemi-GercekVeri.xlsx', sheet_name='Resources')
tasks['StartDateTime'] = pd.to_datetime(tasks['StartDate'].astype(str) + ' ' + tasks['StartTime'].astype(str)) 
tasks['EndDateTime'] = pd.to_datetime(tasks['EndDate'].astype(str) + ' ' + tasks['EndTime'].astype(str))

tasks['EndWithBuffer'] = tasks['EndDateTime'] + pd.to_timedelta(tasks['BufferTime-min'], unit='minutes')
totalTime = int((tasks['EndDateTime'].max() - tasks['StartDateTime'].min()).total_seconds() / 60)
print('hi')




assignments['Duration'] = tasks['Duration-min']
print(assignments)
rutils = []

print(assignments.loc[assignments['ResourceId'] == 26])
for r in resources.ResourceId.values.astype(str):
    rutils.append(np.sum(assignments[assignments['ResourceId'] == r]['Duration']) / totalTime)

resources['Utilization'] = rutils



resources['NumCompat'] = pd.read_csv('compatsum.csv').iloc[:,1]

print(resources.loc[resources['Utilization'] == 0.0])

resources.sort_values(by='Utilization', ascending=True).to_csv('rutils.csv')