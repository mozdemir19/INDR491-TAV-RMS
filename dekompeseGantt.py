import pandas as pd
import numpy as np
import plotly.express as px

assignments = pd.read_csv('decomposed_winter_assignments2.csv', index_col=0)
data = pd.ExcelFile('RMS-MultiKPI-Input-KisDonemi-GercekVeri.xlsx')
tasks = pd.read_excel(data, sheet_name='Tasks')
resources = pd.read_excel(data, sheet_name='Resources')

tasks['StartDateTime'] = pd.to_datetime(tasks['StartDate'].astype(str) + ' ' + tasks['StartTime'].astype(str)) 
tasks['EndDateTime'] = pd.to_datetime(tasks['EndDate'].astype(str) + ' ' + tasks['EndTime'].astype(str))

tasks['EndWithBuffer'] = tasks['EndDateTime'] + pd.to_timedelta(tasks['BufferTime-min'], unit='minutes')

gantt_df = pd.DataFrame({'ResourceId': assignments.ResourceId.astype(str), 'TaskId': assignments.TaskId,
                         'StartDateTime': tasks.loc[assignments.TaskId - 1].StartDateTime,
                         'EndDateTime': tasks.loc[assignments.TaskId - 1].EndDateTime})

fig = px.timeline(gantt_df, x_start='StartDateTime', x_end='EndDateTime', y='ResourceId', color='TaskId', color_continuous_scale='rainbow')
fig.show()


