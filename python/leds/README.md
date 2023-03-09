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
4. Open the hat webpage. 
   1. If connected on the same network as the Synch.Live router, then go to the following web address:
   `192.168.100.1xx:5000`. Replace the 'xx' with the hat number. For example, to access 'hat 04', replace 'xx' with '04'
   so that the address is `192.168.100.104:5000`. 
   2. Otherwise, if connecting via SSH, on a different connection from the hats:
      1. Make sure that the Synch.Live router is connected to the wider internet. This will need port forwarding setup 
      from your home router to the Synch.Live router.
      2. Setup Putty to allow you to view the hat's page on your local browser:
         1. Open Putty.
         2.  Set the 'Host Name' as `synchlive.ddns.net`.
         3. Set the 'Port number' to the port number set up on your home router to forward to the Synch.Live router.
         4.  In the 'Auth' tab in the sidebar, upload your SSH private key in .ppk format. Make sure that the
      corresponding public key is saved to the observer's list of accepted SSH keys.
         5.   In the 'Tunnels' tab, set the 'Source Port' to `5000` and the 'Destination' as `localhost:xxxx` where 
              'xxxx' is any port number in the range 1000-9000. It is important that this isn't the same as anybody 
              else who will be accessing the page remotely at the same time as you. 
         6.  In the 'Data' tab, set the "Auto-login username" to `pi`.
         7. In the 'Session' tab, press `Save`.
      3. Run the Putty session setup in the previous step. It may be necessary to enter the passphrase to your SSH key.
      4. Enter the following command into the command line: `ssh -L xxxx:localhost:5000 playerY -N` where 'xxxx' is the 
         port number set in the 'Tunnels' tab in Step 2, and 'Y' is the hat number you want to connect to. 
      5. Go to `localhost:5000` in your browser. You should be able to see the hat's webpage.
         ```
         If the webpage does not show, it might be fixed by rebooting the Flask server on the hat. To do this, 
         run the following code on the Hat's command line, within the `server` folder inside the `leds` folder:
         `sudo systemctl restart hat`. Then, refresh the browser page.
         ```
5. Run the relevant code, via the GUI, to check that the hat functionality is running as required. 
6. Push the new/edited code to the Synch.Live Git repo. Copy the code to all the Hats.


### Distributing the code to other hats

Currently, only hat 4 and 5 have the files with the updated code int the leds folder. If you want to extend it to
other hats, you need to do the following:

1. Install `requirements.txt` on the hat
2. Transfer recent files on the hat using WinSCP or Ansible
3. Setup of the SYSTEMD so that server starts on boot:
    1. Create a unit file
        - Open a sample unit file using the command as shown below:
        ```
        sudo nano /lib/systemd/system/hat.service
       ```
        - Add in the following text :
        ```
       [Unit]
       Description=Hat Service
       
       [Service]
       User=pi
       WorkingDirectory=~
       Type=simple
       ExecStart=python3 -m leds.server.server
       
       [Install]
       WantedBy=multi-user.target
       ```
        - You should save and exit the nano editor.
        - The permission needs to be set to 644 for the unit file:
       ```
       sudo chmod 644 /lib/systemd/system/hat.service
       ```
    2. Configure systemd:
        - After the unit file has been defined:
        ```
       sudo systemctl daemon-reload
       sudo systemctl enable hat.service
       ```
        - Reboot the Pi:
       ```
       sudo reboot
       ```