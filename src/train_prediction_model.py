import os
import sys
import pickle
import multiprocessing
import time
from simulator.simulator import Simulator, Reporter
from planner import Planner
from task_execution_time import ExecutionTimeModelHelpdesk
from task_execution_time import ExecutionTimeModelACR
from russel_policies import RandomPolicy
from simulator.problems import MinedProblem

"""
This file is responsible for training the prediction model that estimates processing times of individual resources. Use your mined simulation model here by saving it
to problem_file. Configure the simulation parameters and run this file to train the prediction model, which will result in a pickle file that contains the trained model.
"""

script_dir = os.path.dirname(os.path.abspath(__file__))
bpo_path = os.path.abspath(os.path.join(script_dir, "..", "bpo-project", "bpo"))
sys.path.append(bpo_path)

# path to the mined Helpdesk simulation model
problem_file = os.path.join(bpo_path, "HELPDESK_Problem_TESTIN2.pickle")
problem = MinedProblem.from_file(problem_file)

# adjust interarrival time (if needed)
# problem.interarrival_time._alpha *= 1.8

prediction_model = ExecutionTimeModelHelpdesk()
#prediction_model = ExecutionTimeModelACR()

warm_up_policy = RandomPolicy()
warm_up_time = 24 * 2 * 365  # warm-up time in hours
simulation_time = warm_up_time
activity_names = list(problem.resource_pools.keys())

my_planner = Planner(prediction_model,
                     warm_up_policy, warm_up_time,
                     warm_up_policy,
                     activity_names,
                     predict_multiple=True,
                     hour_timeout=120,
                     debug=True)

simulator = Simulator(problem, Reporter(), my_planner)
simulator_result = simulator.simulate(24*5*365)

parent_dir = os.path.dirname(script_dir)
model_output_path = os.path.join(parent_dir, "prediction_model_HELPDESK_TESTIN2.pkl")

with open(model_output_path, 'wb') as file:
    pickle.dump(prediction_model, file)

print("Simulation completed.")
print("Result:", simulator_result)
print("Trained model saved to:", model_output_path)
