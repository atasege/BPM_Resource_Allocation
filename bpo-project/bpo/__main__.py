import os
from problems import ImbalancedProblem, SequentialProblem, MMcProblem, MinedProblem
from simulator import Simulator, Reporter, EventLogReporterElement, TimeUnit
from planners import GreedyPlanner, HeuristicPlanner, ImbalancedPredictivePlanner
from predicters import ImbalancedPredicter
from visualizers import boxplot, line_with_ci, statistics
from distributions import DistributionType, UniformDistribution #POTaskDurationDistribution
from miners import mine_problem
import pandas
import numpy as np
import datetime

"""
This file is responsible for mining the simulation models. Configure and run the methods try_mine_helpdesk_problem() and try_mine_acr_problem(). 
See miners.py for the configuration parameters. Running the mentioned methods will result in the mined simulation model in the form of a .pickle file
"""

def try_mmc():
    planner = GreedyPlanner()
    reporter = Reporter(10000)
    results = Simulator.replicate(MMcProblem(), planner, reporter, 50000, 20)
    print(Reporter.aggregate(results))


# Simulating several planners and predicters for the imbalanced problem
def try_several_planners():
    print(Reporter.aggregate(Simulator.replicate(ImbalancedProblem(spread=1.0), GreedyPlanner(), Reporter(10000), 50000, 20)))
    print(Reporter.aggregate(Simulator.replicate(ImbalancedProblem(spread=1.0), HeuristicPlanner(), Reporter(10000), 50000, 20)))
    print(Reporter.aggregate(Simulator.replicate(ImbalancedProblem(spread=1.0), ImbalancedPredictivePlanner(ImbalancedPredicter), Reporter(10000), 50000, 20)))


# Comparing two spreads of the imbalanced problem in a box plot
def try_comparison():
    problem_instances = []
    spread10 = Simulator.replicate(ImbalancedProblem(spread=1.0), HeuristicPlanner(), Reporter(10000), 50000, 5)
    problem_instances = []
    spread05 = Simulator.replicate(ImbalancedProblem(spread=0.5), HeuristicPlanner(), Reporter(10000), 50000, 5)
    boxplot({'spread 0.5': spread05['task proc time'], 'spread 1.0': spread10['task proc time']})


# Comparing multiple spreads of the imbalanced problem in a line plot
def try_multiple_comparison():
    results = dict()
    for spread in np.arange(0.5, 1.01, 0.05):
        result = Reporter.aggregate(Simulator.replicate(ImbalancedProblem(spread=spread), HeuristicPlanner(), Reporter(10000), 50000, 5))
        results[spread] = result['task wait time']
    line_with_ci(results)


# Printing a trace for the sequential problem
def try_execution_traces():
    reporter = Reporter(warmup=0, reporter_elements=[EventLogReporterElement("../temp/my_log.csv", TimeUnit.MINUTES)])
    simulator = Simulator(SequentialProblem(), reporter, GreedyPlanner())
    simulator.simulate(1000)


# Mining a problem from an event log and saving it to file
def try_mine_problem():
    log = pandas.read_csv("./bpo/resources/BPI Challenge 2017 - clean.zip")
    problem = mine_problem(log,
                           datetime_format="%Y-%m-%d %H:%M:%S.%f",
                           earliest_start=datetime.datetime(2016, 1, 1),
                           latest_completion=datetime.datetime(2016, 12, 30),
                           datafields= {
                                'ApplicationType': DistributionType.CATEGORICAL,
                                'LoanGoal': DistributionType.CATEGORICAL,
                                'RequestedAmount': DistributionType.BETA
                            },
                            max_error_std=UniformDistribution(0.05, 0.2))
    problem.save("./temp/BPI Challenge 2017 - instance 3.pickle")

vars
def try_mine_po_problem():
    log = pandas.read_csv('./bpo/resources/PurchasingExample.csv')
    problem = mine_problem(log,
                           datetime_format="%Y/%m/%d %H:%M:%S.%f",
                           earliest_start=datetime.datetime(2011, 1, 1),
                           latest_completion=datetime.datetime(2011, 10, 14),
                           datafields= {},
                           min_resource_count=1,
                           #resource_field_name='Role',
                           resource_schedule_timeunit=datetime.timedelta(hours=1),
                           resource_schedule_repeat=int(24*7),
                           max_error_std=UniformDistribution(0.05, 0.2)
                           )
    problem.schedule = ([0]*6 + [1, 2, 13, 15, 16, 13, 12, 13, 9, 3, 2, 2] + [0]*6) * 5 + [0]*24*2
    #problem.processing_times = POTaskDurationDistribution()
    problem.save("./temp/po_problem.pickle")
    
def try_mine_helpdesk_problem():
    
 script_dir = os.path.dirname(os.path.abspath(__file__))
 file_path = os.path.join(script_dir, "HelpdeskStartsEstimated.csv")
 log = pandas.read_csv(file_path)
 problem = mine_problem(log,
                           #datetime_format="%Y/%m/%d %H:%M:%S.%f",
                           datetime_format="%Y-%m-%d %H:%M:%S",
                           earliest_start=datetime.datetime(2010, 1, 13),
                           latest_completion=datetime.datetime(2014, 1, 3),
                           datafields= {},
                                          min_resource_count=1,
                                          # for 15-minute intervals:
                                          resource_schedule_timeunit=datetime.timedelta(hours=1),
                                          resource_schedule_repeat=int(24*7), 
                                          max_error_std=UniformDistribution(0.05,0.2))
 # DUPLICATE has one resource
 if "DUPLICATE" not in problem.resource_pools or not problem.resource_pools["DUPLICATE"]:
        problem.resource_pools["DUPLICATE"] = ["Value 2"]

# INVALID has two resources
 if "INVALID" not in problem.resource_pools or not problem.resource_pools["INVALID"]:
    problem.resource_pools["INVALID"] = ["Value 1", "Value 2"]

# RESOLVED has two resources
 if "RESOLVED" not in problem.resource_pools or not problem.resource_pools["RESOLVED"]:
    problem.resource_pools["RESOLVED"] = ["Value 1", "Value 2"]

 #problem.save("HELPDESK_Problem_1hour.pickle")
 problem.save("HELPDESK_Problem_TESTIN2.pickle")
 print("Model mining complete. Saved to HELPDESK_Problem_TESTIN2.pickle")

def try_mine_acr_problem():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "acr_durations_zeros.csv")
    log = pandas.read_csv(file_path)
    problem = mine_problem(log,
                           datetime_format="%Y-%m-%d %H:%M:%S",
                           earliest_start=datetime.datetime(2016, 2, 1),
                           latest_completion=datetime.datetime(2016, 7, 1),
                           datafields= {},
                           min_resource_count=1,
                           resource_schedule_timeunit=datetime.timedelta(hours=1),
                           resource_schedule_repeat=int(24*7), 
                           max_error_std=UniformDistribution(0.05, 0.2))
    problem.save("ACR_problem_TESTIN.pickle")
    print("Model mining complete. Saved to ACR_problem_TESTIN.pickle")


# Load a mined problem from file, simulating it and saving the log
def try_simulate_mined_problem():
    problem = MinedProblem.from_file("./temp/BPI Challenge 2017 - clean Jan Jun - problem.pickle")
    reporter = Reporter(warmup=0, reporter_elements=[EventLogReporterElement("./temp/BPI Challenge 2017 - clean Jan Jun - simulated log.csv", TimeUnit.HOURS, data_fields=list(problem.data_types.keys()))])
    simulator = Simulator(problem, reporter, GreedyPlanner())
    simulator.simulate(365*24)

# Load a mined problem from file, simulating it and saving the log
def try_simulate_mined_po_problem():
    problem = MinedProblem.from_file("./temp/po_problem.pickle")
    reporter = Reporter(warmup=0,
                        reporter_elements=[EventLogReporterElement("./temp/po_problem - simulated log.csv",
                                                                   TimeUnit.HOURS,
                                                                   data_fields=list(problem.data_types.keys()))])
    simulator = Simulator(problem, reporter, GreedyPlanner())
    simulator.simulate((365*9.5/12)*24)

def try_visualize_task_processing_times():
    sl = pandas.read_csv("../bpo/resources/BPI Challenge 2017 - clean.zip")
    sl = sl.rename(columns={"Case ID": "case_id", "Activity": "task", "Resource": "resource", "Start Timestamp": "start_time", "Complete Timestamp": "completion_time"})
    s = statistics(sl)
    del s['Interarrrival times']
    boxplot(s)

    sl = pandas.read_csv("../temp/BPI Challenge 2017 - clean Jan Jun - simulated log.csv")
    s = statistics(sl)
    del s['Interarrrival times']
    boxplot(s)


if __name__ == "__main__":
    # try_mmc()
    # try_several_planners()
    # try_comparison()
    # try_multiple_comparison()
    # try_execution_traces()
    #try_mine_po_problem()
    #try_simulate_mined_po_problem()
    #try_mine_problem()
    try_mine_helpdesk_problem()
    #try_mine_acr_problem()
    #try_simulate_mined_problem()
    
