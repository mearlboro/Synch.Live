# Synch.Live database connection

An SQLite database is created to store trajectories and experiment parameters.
The database holds two tables `trajectories` and `experiment_parameters`.
The code for the database is located in `python/synch_live/camera/db/__init__.py`.

## Running an experiment and getting a database
1. Once you launch the Flask app from the `python` directory, `database.db` is created automatically (if it doesn't already exist) in the `python` directory. 
2. To observe the experiment, you can navigate to the `Experiment` tab. If you want to update the experiment settings, click the `Calibrate` button before starting the experiment. After you have finished calibrating, press the button `Play` to return to return to the experiment control page. 
3. Input `Experiment ID` and `Experiment location` that are specific to your experiment. Ticking the box `Test?` marks this as a test experiment. The database will automatically delete experiments marked as tests after 7 days. Press `Start!` to start observing the experiment. 
4. During a running experiment, the data is collected and stored in `database.db`. 
5. When you are finished observing, press the `Stop` button to finish the experiment. This finalises the database with the end time of your experiment. 

## Downloading a database
When you have stopped observing the experiment, the experiment parameters and trajectories associated with that experiment can be downloaded. Navigate to the `Data` tab and in the `Experiment ID` dropdown menu select an exepiment for which you want to download data. The dropdown menu contains all the experiment IDs currently stored in the database. When you press `Download!`, a database will be downloaded in `csv` format for the chosen experiment ID.

## `trajectories` TABLE
This table contains:
- `experiment_id` which is input by the user on the app, 
- `player_id` which starts from '1' and depends on the number of hats used in the experiment, 
- `frame_id` which starts from '0' every time a new experiment is run to indicate the video frame, 
- `position_x` which is computed as "x-w/2", 
- `position_y` which is computed as "y-h/2", 
- `unfiltered_psi` which is 'NULL' when `frame_id` is '0', and contains the unfiltered calculated psi parameter from `emergence.py`, 
- `filtered_psi` which is 'NULL' when `frame_id` is '0, and contains the filtered calculated psi parameter from `emergence.py`.

The database is written to from `python/synch_live/camera/video/__init__.py` by calling functions `write_in_trajectories_player_coordinates` and `write_in_trajectories_psis` stored in `python/synch_live/camera/db/__init__.py`.

## `experiment_parameters` TABLE
This table contains: 
- `experiment_id` which is input by the user on the app,
- `experiment_is_test` which is chosen by user by ticking `Test?` box before starting an experiment,
- `date` which is a current date at the experiment run time, 
- `location` which is by the user on the app, 
- `start_time` which is the current time at the experiment start time, 
- `end_time` which is the time when the `Stop` button is pressed, 
- `use_correction`, 
- `psi_buffer_size`, 
- `observation_window_size`, 
- `use_local`, 
- `sigmoid_a` which is filled when task is set to 'emergence', 
- `sigmoid_b` which is filled when task is set to 'emergence'.

`experiment_id`, `experiment_is_test`, `location`,`date` and `start_time` parameters of the table are filled in `python/synch_live/camera/server/tracking.py` when we `Start!` an experiment by calling the `write_in_experiment_parameters` function stored in `python/synch_live/camera/db/__init__.py`.

The other parameters of this table are filled in `python/synch_live/camera/video/__init__.py`
by calling `write_in_experiment_parameters_emergenceCalculator`, `write_in_experiment_parameters_sigmoids` and `write_in_experiment_parameters_end_time` functions stored in `python/synch_live/camera/db/__init__.py`.

## python/synch_live/camera/server/download.py
In order to download data stored in database, users are given a dynamic dropdown list of all experiment IDs stored in the database. The unique IDs are retrieved by calling `get_all_experiment_ids_query` stored in `python/synch_live/camera/db/__init__.py`. When a user chose a particular experiment id, `process_query` function (stored in `python/synch_live/camera/db/__init__.py`) retrieves data with that experiment ID from the database and converts it into `csv` file.