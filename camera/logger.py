from datetime import date
import logging
import os
import socket

# create directory for logs if it doesn't exit
if not os.path.exists('logs'):
    os.mkdir('logs')

# initialise logging to a file named by the current hostname
hostname = socket.gethostname()
# all experiments in a day are appended to the same log
today = date.today().strftime('%Y%m%d')

log_path = f"logs/{hostname}_{today}.log"
logging.basicConfig(filename = log_path, filemode = 'a', level = logging.INFO,
        format = '%(asctime)s.%(msecs)03d %(message)s', datefmt = '%H:%M:%S')
