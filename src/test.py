import pickle
from simulator.simulator import Simulator, EventLogReporter
from simulator.problems import *
from planner import Planner
from policy import *
from ilp_policy import UnrelatedParallelMachinesSchedulingPolicy
from ilp_policy_non_assign import UnrelatedParallelMachinesSchedulingNonAssignPolicy
from ilp_policy_non_assign_2 import UnrelatedParallelMachinesSchedulingNonAssignPolicy2
from ilp_policy_2_batch import UnrelatedParallelMachinesSchedulingBatchPolicy2
from least_loaded_qualified_person_policy import LeastLoadedQualifiedPersonPolicy
from russel_policies import *
from park_policy import *
from task_execution_time import ExecutionTimeModel
from hungarian_policy import HungarianMultiObjectivePolicy

import numpy as np
import multiprocessing
import time
from datetime import datetime
import csv
import sys

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

"""
This file is responsible for the actual simulations that should use your mined simulation and prediction models. 
Configure the file names of your mined simulation model and prediction model. You can then execute run.sh with your desired simulation properties
to collect your simulation statistics. These statistics will be stored in the csv that is specified in this file (in lines 155-170)
"""

def run_simulator(problem, days, objective, delta, result_queue, selection_strategy=None):
    real_start_time = time.time()
    start_time = time.process_time()
    prediction_model = ExecutionTimeModel()

    if problem == 'BPIC':
        with open('prediction_model_bpic.pkl', 'rb') as file:
            prediction_model = pickle.load(file)
    elif problem == 'PO':
        with open('prediction_model_po.pkl', 'rb') as file:
            prediction_model = pickle.load(file)
    elif problem == 'Helpdesk':
        #with open('prediction_model_HELPDESK_1hour.pkl', 'rb') as file:
        with open('prediction_model_HELPDESK_TESTIN2.pkl', 'rb') as file:
            prediction_model = pickle.load(file)
    elif problem == 'ACR':
        with open('prediction_model_ACR_TESTIN.pkl', 'rb') as file:
            prediction_model = pickle.load(file)
    

    warm_up_policy = RandomPolicy()
    warm_up_time =  0
    simulation_time = 24*days
    if objective == "Hungarian":
        policy = HungarianMultiObjectivePolicy(1, 0, 0, delta)
    elif objective == "MILP":
        policy = UnrelatedParallelMachinesSchedulingNonAssignPolicy2(1, 0, 0, delta, selection_strategy)
    elif objective == "KBatch":
        # use delta for batch size k
        policy = UnrelatedParallelMachinesSchedulingBatchPolicy2(1, 0, 0, 0, selection_strategy, delta)
    elif objective == "Park":
        policy = None
    elif objective == "RoundRobin":
        policy = RoundRobinPolicy()
    elif objective == "LLQP":
        policy = LeastLoadedQualifiedPersonPolicy()
    elif objective == "ShortestQueue":
        policy = ShortestQueuePolicy()
    elif objective == "Random":
        policy = RandomPolicy()


        #to get  directory 
    script_dir = os.path.dirname(os.path.abspath(__file__))
        #going to the bpo-project/bpo directory
    bpo_path = os.path.abspath(os.path.join(script_dir, "..", "bpo-project", "bpo"))

    if problem == 'BPIC':
        instance_file = 'src/simulator/data/BPI Challenge 2017 - instance.pickle'
    elif problem == 'PO':
        instance_file = 'src/simulator/data/po_problem.pickle'
    elif problem == 'Helpdesk':
        instance_file = os.path.join(bpo_path, 'HELPDESK_Problem_TESTIN2.pickle')  # updated path to use bpo_path
    elif problem == 'ACR':
        instance_file = os.path.join(bpo_path, 'ACR_problem_TESTIN.pickle')

    

    sys.path.append('src/simulator')
    problem = MinedProblem.from_file(instance_file)

    activity_names = list(problem.resource_pools.keys())
    my_planner = Planner(prediction_model, warm_up_policy, warm_up_time, policy,
                        activity_names,
                        predict_multiple=True,
                        hour_timeout=3600,
                        debug=True)

    reporter = EventLogReporter('./test.csv', [])
    simulator = Simulator(problem, reporter, my_planner)

    if problem == 'PO':
        # reset arrival time for PO problem:
        #   BPICs test data set arrival times were fitted with
        #   a different method.
        simulator.problem.interarrival_time._alpha /= 10

    if objective == "Park":
        policy = ParkPolicy(simulator.problem.next_task_distribution, my_planner.predictor, my_planner.task_type_occurrences)
        my_planner.policy = policy

    simulator_result = simulator.simulate(simulation_time)
    times = (datetime.fromtimestamp(real_start_time).strftime("%Y-%m-%d %H:%M:%S"),
             datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S"),
             str(time.time() - real_start_time),
             str(time.process_time()-start_time)
            )
    if simulator_result[1] == "Stopped":
        res = [objective, *times, str(delta), "Stopped", "", *map(str, my_planner.get_current_loss()),
                          str(my_planner.num_assignments), str(my_planner.policy.num_allocated), str(my_planner.policy.num_postponed)]
    else:
        res = [objective, *times, str(delta), *map(str, simulator_result), *map(str, my_planner.get_current_loss()),
                          str(my_planner.num_assignments), str(my_planner.policy.num_allocated), str(my_planner.policy.num_postponed)]
    if objective == "MILP":
        res += [str(policy.optimal), str(policy.feasible), str(policy.no_solution), selection_strategy]
    else:
        res += ['', '', '', '']
    result_queue.put(res)

def get_alive_proceses(all_procesess):
    result = []
    for p in all_procesess:
        if p.is_alive():
            result.append(p)
    return result

processes = []
result_queue = multiprocessing.Queue()
alive_processes = []

MAX_PROCESSES = int(sys.argv[6])
problem = sys.argv[8]
for i in np.arange(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])):
    alive_processes = get_alive_proceses(processes)
    while len(alive_processes) >= MAX_PROCESSES:
        time.sleep(0.5)
        alive_processes = get_alive_proceses(processes)

    selection_strategy = sys.argv[7]
    p = multiprocessing.Process(target=run_simulator, args=(problem, int(sys.argv[5]), sys.argv[4], i, result_queue, selection_strategy))
    p.start()
    print(i, 'Started')
    processes.append(p)

    while not result_queue.empty():
        res = result_queue.get()
        print(res)
        with open('resultsTemporary.csv', 'a') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(res)

for p in processes:
    p.join()
while not result_queue.empty():
    res = result_queue.get()
    print(res)
    with open('resultsTemporary.csv', 'a') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(res)
