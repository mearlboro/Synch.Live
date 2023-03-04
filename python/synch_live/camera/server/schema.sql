CREATE TABLE IF NOT EXISTS trajectories
                (experiment_id text, 
                player_id integer, 
                frame_id integer, 
                position_x real, 
                position_y real, 
                unfiltered_psi real, 
                filtered_psi real);

CREATE TABLE IF NOT EXISTS experiment_parameters
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
                sigmoid_b real);