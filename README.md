
## It is highly recommended to use Fedora Linux for this project
### Log Information:

- CSV required with columns: Case ID, Activity, Resource, Start Timestamp, Complete Timestamp
- See the `preprocessing` file if start timestamps are missing
- See the `preprocessing` file if start and end events need to be merged
- The Helpdesk and ACR logs are ready to use in BPM_Resource_Allocation/bpo-project/bpo/

### Step 0: Setup

- Install pipenv and dependencies:
```
  chmod +x setup.sh
  ./setup.sh
```
- If you encounter any problems, make sure to execute the commands in setup.sh individually.
- If you use a different OS than Fedora, you will need to execute equivalent commands in setup.sh
- An alternative setup is available, however it only works for current session (less preferred)
- Make sure pipenv uses the existing Pipfile.lock to create the virtual environment
- You should use the same virtual environment during the following steps

### Step 1: Discover simulation model
- This step is done in `__main__.py` (located in BPM_Resource_Allocation/bpo-project/bpo/)
- Edit `__main__.py` to configure log path and mining parameters (each log has its own method)
- Run `__main__.py` to mine simulation model from event logs 
- This will result in a .pickle file, which is the mined simulation model

### Step 2: Train task processing time prediction model
- Adjust training parameters in `train_prediction_model.py` (located in BPM_Resource_Allocation/src/)
- Configure `train_prediction_model.py` to use your mined simulation model
- Then run:
```
  pipenv run python train_prediction_model.py
```
- This will result in a .pickle file, which is the trained prediction model

### Step 3: Conduct process simulation
- Configure `test.py` to use your mined simulation model and prediction model in (BPM_Resource_Allocation/src/)
- Change simulation properties in `run.sh`
- Run:
```
  chmod +x run.sh
  pipenv run sh run.sh
```
- This will result in a .csv that includes simulation statistics


### If you want to use a log other than ACR or Helpdesk, you should:
- Create a separate model mining method in `__main__.py` and use it in step 1
- Create a separate prediction model in `task_execution_time.py` and use it in step 2
- Adjust `test.py` to include your mined models
### Important Notes
- Dont forget to specify necessary input and output file names at each step
- Avoid using Virtual Machines for this project !



