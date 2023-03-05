import sqlite3
import click
import datetime
import csv
from io import StringIO
from flask import current_app, g

today = datetime.date.today().strftime('%Y-%m-%d')
datapath = '/instance/database.db'

'''
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
'''

today = datetime.date.today().strftime('%Y-%m-%d')
datapath = './database.db'

# creating table 'trajectories' in database.db
def create_table_trajectories():
    cursor = sqlite3.connect(datapath)
    #cursor.execute('DROP TABLE IF EXISTS trajectories')
    cursor.execute('''CREATE TABLE IF NOT EXISTS trajectories
                (experiment_id text, 
                player_id integer, 
                frame_id integer, 
                position_x real, 
                position_y real, 
                unfiltered_psi real, 
                filtered_psi real)''')
    cursor.close()

# writing 'experiment_id', 'player_id', 'frame_id' and coordinates 'position_x' and 'position_y' in table 'trajectories'
# 'position_x' is calculated by x-w/2
# 'position_y' is calculated by y-h/2
def write_in_trajectories_player_coordinates(experiment_id, frame_id, boxes):
    cursor = sqlite3.connect(datapath)
    for i, box in enumerate(boxes):
        cursor.execute('''INSERT INTO trajectories 
        (experiment_id, 
        player_id, 
        frame_id, 
        position_x, 
        position_y) values (?, ?, ?, ?, ?)''', 
        (experiment_id, (i + 1), frame_id, box[0]-(box[2]/2), box[1]-(box[3]/2)))
    cursor.commit()
    cursor.close()

# writing 'unfiltered_psi' and 'filtered_psi' for specified 'experiment_id' and 'frame_id' in table 'trajectories'
def write_in_trajectories_psis(psi_u, psi_f, experiment_id, frame_id):
    cursor = sqlite3.connect(datapath)
    cursor.execute('''UPDATE trajectories SET 
        unfiltered_psi = ?, filtered_psi = ? 
        WHERE experiment_id = ? and frame_id = ?''', 
        (psi_u, psi_f, experiment_id, frame_id))
    cursor.commit()
    cursor.close()


# creating table 'experiment_parameters' in database.db
def create_table_experiment_parameters():
    cursor = sqlite3.connect(datapath)
    #cursor.execute('DROP TABLE IF EXISTS experiment_parameters')
    cursor.execute('''CREATE TABLE IF NOT EXISTS experiment_parameters
                (experiment_id text, 
                date date, 
                location text, 
                start_time time, 
                end_time time, 
                use_correction integer, 
                psi_buffer_size integer, 
                observation_window_size integer, 
                use_local integer, 
                sigmoid_a real, 
                sigmoid_b real)''')
    cursor.close()

# writing 'experiment_id','location', 'date' and 'start_time' in table 'experiment_parameters'
def write_in_experiment_parameters(experiment_id, experiment_location):
    cursor = sqlite3.connect(datapath)
    cursor.execute('''INSERT INTO experiment_parameters 
        (experiment_id, 
        location,
        date, 
        start_time) values (?, ?, ?, ?)''', 
        (experiment_id, experiment_location, today, datetime.datetime.now().strftime('%H:%M:%S')))
    cursor.commit()
    cursor.close()

# writing 'sigmoid_a' and 'sigmoid_b' for specified 'experiment_id' and 'date' in table 'experiment_parameters'
def write_in_experiment_parameters_sigmoids(sigmoid_a, sigmoid_b, experiment_id):
    cursor = sqlite3.connect(datapath)
    cursor.execute('''UPDATE experiment_parameters SET 
        sigmoid_a = ?, 
        sigmoid_b = ? WHERE experiment_id = ? and date = ?''', 
        (sigmoid_a, sigmoid_b, experiment_id, today))
    cursor.commit()
    cursor.close()

# writing 'use_correction', 'psi_buffer_size', 'observation_window_size' and 'use_local' 
# for specified 'experiment_id' and 'date' in table 'experiment_parameters'
def write_in_experiment_parameters_emergenceCalculator(use_correction, psi_buffer_size, 
                                                       observation_window_size, use_local, experiment_id):
    cursor = sqlite3.connect(datapath)
    cursor.execute('''UPDATE experiment_parameters SET 
        use_correction = ?, 
        psi_buffer_size = ?, 
        observation_window_size = ?, 
        use_local = ? WHERE experiment_id = ? and date = ?''', 
        (use_correction, psi_buffer_size, observation_window_size, use_local, experiment_id, today))
    cursor.commit()
    cursor.close()

# writing 'end_time' for specified 'experiment_id' and 'date' in table 'experiment_parameters'
def write_in_experiment_parameters_end_time(experiment_id):
    cursor = sqlite3.connect(datapath)
    cursor.execute('''UPDATE experiment_parameters SET end_time = ? 
        WHERE experiment_id = ? and date = ?''', 
        (datetime.datetime.now().strftime('%H:%M:%S'), experiment_id, today))
    cursor.commit()
    cursor.close()


# creating a query that joins tables 'trajectories' and 'experiment_parameters'
# the result is placed into 'csv' file
def process_query(experiment_id):
    connection = sqlite3.connect(datapath)
    cursor = connection.cursor()

    results = StringIO()
    cw = csv.writer(results)
  
    cursor.execute('''SELECT *
        FROM trajectories t
        JOIN experiment_parameters ep
        USING (experiment_id)
        WHERE t.experiment_id = ? 
        ORDER BY t.frame_id, t.player_id''', [experiment_id])

    rows = cursor.fetchall()
    cw.writerow([i[0] for i in cursor.description])
    cw.writerows(rows)

    cursor.close()

    return results

# creating a query that deletes all the rows in tables 'trajectories' and 'experiment_parameters' where 'date' column 
# has dates that are older than a week from today (current date).
def clean_query():
    connection = sqlite3.connect(datapath)
    cursor = connection.cursor()

    # after this number of days we delete data from the database
    days_ago = 7

    # calculate the date 7 days ago from the current date
    date_cutoff = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).date()

    # deleting from the table 'trajectories'
    cursor.execute('''DELETE 
        FROM trajectories
        WHERE experiment_id IN (SELECT experiment_id FROM experiment_parameters WHERE date(date) <= date(?))''', [date_cutoff])
    connection.commit()

    # deleting from the table 'experiment_parameters'
    cursor.execute('''DELETE
        FROM experiment_parameters 
        WHERE date(date) <= date(?)''', [date_cutoff])

    connection.commit()
    connection.close()

# creating a query to get all distinct 'experiment_id' in 'experiment_parameters' table in database.db  
def get_all_experiment_ids_query():
    connection = sqlite3.connect(datapath)
    cursor = connection.cursor()

    cursor.execute('SELECT DISTINCT experiment_id FROM experiment_parameters ORDER BY experiment_id')
    experiment_ids = [row[0] for row in cursor.fetchall()]

    connection.close()

    return experiment_ids

# creating tables 'trajectories' and 'experiment_parameters' in database.db    
create_table_trajectories()
create_table_experiment_parameters()

# cleaning old data in tables 'trajectories' and 'experiment_parameters' in database.db 
clean_query()
