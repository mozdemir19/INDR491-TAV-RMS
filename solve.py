import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pulp as pl
import plotly.express as px
import plotly.graph_objects as go
import utils as util
import os, time

maxUtil, minUtil = 0.9, 0.2
seasons = ['winter', 'summer']
#season = 'winter'
priorityScoresList = pd.read_excel('AHP.xlsx', sheet_name='Sheet2').values.tolist()
winter = 'RMS-MultiKPI-Input-KisDonemi-GercekVeri.xlsx'
summer = 'RMS-MultiKPI-Input-YazDonemi-GercekVeri.xlsx'

result = pd.DataFrame(columns=['season', 'priorityScores', 'assgnmentCounts', 'utilMean', 'utilVar', 'utilMin', 'utilMax', 'zone1', 'zone2', 'zone3', 'Objective Function'])

for season in seasons:
    data = pd.ExcelFile(eval(season))
    tasks = pd.read_excel(data, sheet_name='Tasks')

    resources = pd.read_excel(data, sheet_name='Resources')
    priorityContent = pd.read_excel(data, sheet_name='PriorityContents')

    tasks['StartDateTime'] = pd.to_datetime(tasks['StartDate'].astype(str) + ' ' + tasks['StartTime'].astype(str)) 
    tasks['EndDateTime'] = pd.to_datetime(tasks['EndDate'].astype(str) + ' ' + tasks['EndTime'].astype(str))

    tasks['EndWithBuffer'] = tasks['EndDateTime'] + pd.to_timedelta(tasks['BufferTime-min'], unit='minutes')

    compatibilities = util.compute_compatibilities(tasks, resources)
    taskHeatmap = util.heatmap(tasks)

    np.sum(taskHeatmap, axis=1).to_csv('heatmapsum.csv')

    U = util.utilities(data)

    taskList = tasks.TaskId
    resourceList = resources.ResourceId

    
    for priorityScores in priorityScoresList:
        

        priorities = util.read_prios(tasks, resources, priorityContent, priorityScores)

        
        problem = pl.LpProblem(f'AdnanMenders_{season}Data', pl.LpMaximize)
        x = {}


        ###DECISION VARIABLES
        for t in taskList:
            for r in resourceList:
                x[t, r] = pl.LpVariable('x_%s,%s' % (t, r), lowBound=0, upBound=compatibilities.loc[t, r], cat=pl.LpBinary)

        ###OBJECTIVE FUNCTION
        problem += pl.lpSum([(U.loc[var] + np.sum([priorities[i].loc[var] for i in range(len(priorities))])) * x[var] for var in x])

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
        """for r in resourceList:
            rUtil = (pl.lpSum(util.resource_utilization(r, tasks, x)))
            problem += 100 * rUtil <= 90 * totalTime
            problem += 100 * rUtil >= 10 * totalTime"""


        solver = pl.getSolver('GUROBI_CMD', gapRel=0.01, timeLimit=300)
        solver.solve(problem)


        assignments = pd.DataFrame(columns=['TaskId', 'ResourceId'])
        assignmentCounts = np.zeros((5, ))

        for var in x:
            #print(x[var].varValue)
            
            if x[var].varValue == 1:
                assignmentCounts[0] += x[var].varValue
                
                truthArray = np.array([priorities[i].loc[var] > 0 for i in range(len(priorities))])
                assignmentCounts[1:] += truthArray * x[var].varValue
                
                #new_row = pd.DataFrame({'TaskId': var[0], 'ResourceId':var[1]})
                assignments.loc[len(assignments)] = [var[0], var[1]]


        assignments.to_csv(f'withoutUtil/{season}_{priorityScores}_assignments.csv')
        assignments['Duration'] = tasks['Duration-min']

        rutils = []
        zone1 = []
        zone2 = []
        zone3 = []
        for r in resources.ResourceId:
            utilization = np.sum(assignments[assignments['ResourceId'] == r]['Duration']) / totalTime
            rutils.append(utilization)
            if resources.loc[resources.ResourceId == r].Zone.values[0] == 'Apron 1':
                zone1.append(utilization)
            elif resources.loc[resources.ResourceId == r].Zone.values[0] == 'Apron 2':
                zone2.append(utilization)
            elif resources.loc[resources.ResourceId == r].Zone.values[0] == 'Apron 3':
                zone3.append(utilization)
        result.loc[len(result)] = [season, priorityScores, assignmentCounts, np.mean(rutils), np.var(rutils), np.min(rutils), np.max(rutils),
                                   np.mean(zone1), np.mean(zone2), np.mean(zone3), pl.value(problem.objective)]


        ##print gantt chart
        gantt_df = pd.DataFrame({'ResourceId': assignments.ResourceId.astype(str), 'TaskId': assignments.TaskId,
                                'StartDateTime': tasks.loc[assignments.TaskId - 1].StartDateTime,
                                'EndDateTime': tasks.loc[assignments.TaskId - 1].EndDateTime})

        fig = px.timeline(gantt_df, x_start='StartDateTime', x_end='EndDateTime', y='ResourceId', color='TaskId', color_continuous_scale='rainbow')
        fig.write_html(f'withoutUtil/{season}_{priorityScores}_gantt.html')
        #fig.show()

result.to_excel('withoutUtil/experiment_results.xlsx', index=False)