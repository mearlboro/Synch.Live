# Synch.Live Hats `leds` Folder

This package contains the necessary code to control the LEDs on the hat. It also contains a folder for the code
related to the hat's personal Flask server, used to run a webpage that controls its leds. The most important files to
be aware of are the `ws2801_headset.py` and `headset.py` files; these are the two files that almost certainly need to
be edited in order to add more functionality with respect to the running of the LEDs.

## Contents

The `leds` package contains 3 main components: `server` folder, `.py files related to the use of the hat's leds` and
other `miscellaneous files`.

### `server`

A folder containing the code needed to run the Flask web server. This serves a webpage that allows for controlling
of the hat.

### `.py files for controlling of the hat's leds`

The most important files to edit when considering new led functionality are `headset.py` and `ws2801_headset.py`.

- `__init__.py` : empty file
- `headset.py` : parent methods for the methods in `ws2801_headset.py` that log the running of led code/effects /
  animations. Implementation for legacy methods.
- `mockloop.py` : legacy function that makes the lights blink with a period given by the period parameter.
- `startup.py` : runs the `crown_breathe` function in an infinite loop.
- `stop.py` : turns all lights on the hat off.
- `wait.py` : allows running of the `breathe`, `exposure`, `pilot`, or `rainbow` functions on the hat from the
- command line.
- `ws2801_headset.py` : functions with their implementation for various methods of running the hat leds.

### `Miscellaneous Files`

Other files:

- `experiment.py` : used to help run an experiment.
- `logger.py` : used for writing to the log file.
- `requirements.txt` : the libraries, modules and packages needed for this part of the project.

## Setup Notes

1. Install required packages from `requirements.txt`.
2. Make sure that the latest code is on the hats from `python` folder for `leds`. This was done using the WinSCP, but
   can be potentially done using existing Ansible scripts.

    ``` 
    Instruction for using WinSCP: open-source SSH File Transfer Protocol.
   
    1. Fill in the details on the starter page:
    
       Host name: player4
       Port number: 22
       User name: pi
       Password: the password for the pi

    2. Click on “Advanced”.
    3. Under the “Connection” tab, go to “Tunnel”.
    4. Enter the following details: 
       
       Host name: synchlive.ddns.net
       Port number: 1984
       User name: pi
       Private key file: find the directory with your SSH key
   
    5. Click “OK” at the bottom of the window.
    6. Click “Save”. Make sure the save password checkbox is ticked on the popup that appear.
       Then click “OK”.
    7. Now you can just click on the “player4” label on the left-hand pane, and click login to view, transfer
       and edit files on the hat
    ```

## Editing and testing/running the code for development

### Making changes to led functionality

1. Clone this repository to your local machine.
2. Make changes in `ws2801_headset.py` and `headset.py` to edit LED functionality. In order to add new functionality,
   it may be necessary to add new buttons in the `hat_standalone.html` file, and new app routes in eh `server.py` file,
   both located in the `server` folder.
3. Copy the code onto the hats. You can do this by following 'Step 4' from the 'Setup Notes' section above.
4. Run the relevant code, via the GUI, to check that the hat functionality is running as required.
5. Push the new/edited code to the Synch.Live Git repo. Copy the code to all the Hats.

Distributing the code to other hats can be found in the README for the hats server [here](python/leds/server/README.md).