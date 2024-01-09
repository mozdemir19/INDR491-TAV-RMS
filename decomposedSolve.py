import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pulp as pl
import plotly.express as px
import plotly.graph_objects as go
import utils as util

season = 'winter'

winter = 'RMS-MultiKPI-Input-KisDonemi-GercekVeri.xlsx'
summer = 'RMS-MultiKPI-Input-YazDonemi-GercekVeri.xlsx'

data = pd.ExcelFile(eval(season))
tasks = pd.read_excel(data, sheet_name='Tasks')
resources = pd.read_excel(data, sheet_name='Resources')
priorityContent = pd.read_excel(data, sheet_name='PriorityContents')

tasks['StartDateTime'] = pd.to_datetime(tasks['StartDate'].astype(str) + ' ' + tasks['StartTime'].astype(str)) 
tasks['EndDateTime'] = pd.to_datetime(tasks['EndDate'].astype(str) + ' ' + tasks['EndTime'].astype(str))

tasks['EndWithBuffer'] = tasks['EndDateTime'] + pd.to_timedelta(tasks['BufferTime-min'], unit='minutes')

compatibilities = util.compute_compatibilities(tasks, resources)
taskHeatmap = util.heatmap(tasks)

U = util.utilities(data)

taskList = tasks.TaskId
resourceList = resources.ResourceId

priorityVars = util.priorityGroupVars(tasks, resources, priorityContent)

print(priorityVars[-1])
solvedVars = set()

for priority in priorityVars:

    problem = pl.LpProblem(f'Adnan_Menderes_Decomposed_{season}', pl.LpMaximize)
    x = {}

    for t in taskList:
        for r in resourceList:
            x[t, r] = pl.LpVariable('x_%s,%s' % (t, r), lowBound=0, upBound=compatibilities.loc[t, r], cat=pl.LpBinary)


    for var in x:
        if var in solvedVars:
            x[var].setInitialValue(1, check=False)
            x[var].fixValue()
            continue
        if not bool(priority.loc[var]):
            x[var].setInitialValue(0, check=False)
            x[var].fixValue()


        

    
    ###OBJECTIVE FUNCTION
    problem += pl.lpSum([U.loc[var] * x[var] for var in x])

    #CONSTRAINTS

    #i) assign one task to one resource
    for t in taskList:
        problem += pl.lpSum([x[t, r] for r in resourceList]) <= 1


    #ii) assign one resource to one task at a time
    for idx, row in taskHeatmap.iterrows():
        tasks_in_time_step = set(dict(row[row==1]).keys())
        for r in resourceList:
            cons = [x[t, r] for t in tasks_in_time_step]
            if len(cons) > 1:
                constraint_for_time_bucket = pl.lpSum(cons) <= 1
                problem += constraint_for_time_bucket

    
    ### RESOURCE UTILIZATION
    # iii) find resource with max and min utilization
    totalTime = int((tasks['EndDateTime'].max() - tasks['StartDateTime'].min()).total_seconds() / 60)
    for r in resourceList:
        rUtil = (pl.lpSum(util.resource_utilization(r, tasks, x)))
        problem += 100 * rUtil <= 90 * totalTime
        problem += 100 * rUtil >= 10 * totalTime


    #problem.solve()
    solver = pl.getSolver('GUROBI_CMD', gapRel=0.01, timeLimit=180)
    solver.solve(problem)

    
    for var in x:            
        if x[var].varValue == 1:
            solvedVars.add(var)

    


assignments = pd.DataFrame(columns=['TaskId', 'ResourceId'])
for var in x:
    if x[var].varValue == 1:
        assignments.loc[len(assignments)] = [var[0], var[1]]
assignments.to_csv(f'decomposed_{season}_assignments.csv')
print(assignments)
gantt_df = pd.DataFrame({'ResourceId': assignments.ResourceId.astype(str), 'TaskId': assignments.TaskId,
                                'StartDateTime': tasks.loc[assignments.TaskId - 1].StartDateTime,
                                'EndDateTime': tasks.loc[assignments.TaskId - 1].EndDateTime})

fig = px.timeline(gantt_df, x_start='StartDateTime', x_end='EndDateTime', y='ResourceId', color='TaskId', color_continuous_scale='rainbow')
fig.write_html(f'decomposed_{season}_gantt.html')
fig.show()