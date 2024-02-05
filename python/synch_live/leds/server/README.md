# Synch.Live hats server code

The code in this folder creates a Flask web application to control the LEDs
of the player's hat. It gives the user ability to control colour, blinking
frequency and effect duration & store the settings in the configuration file
for easier access. User can also try out various effects and animations from
`leds` folder.

## Contents

The `server` package contains 4 main components: `static` folder, `templates` folder, `server.py`
and `config.yaml` (an example of it is on GitHub, saved and changed on the hats through the web application).

### `server.py`

The main python file with the Flask application that handles all requests and responses.

### `static`

Folder with all the static assets such as CSS, JavaScript, and image files.

- `hat_standalone.css` : stylesheet for the hat control template.
- `output.css` : stylesheet for the layout template.
- `style.css` : general stylesheet.
- `hat_standalone_script.js` : JavaScript file for the tab content and default values.
- `favicon.ico` : the icon file for Synch.Live.

### `templates`

Folder with all the HTML templates used by Flask to render pages.

- `_taghelpers.html` : tag helpers template.
- `hat_standalone.html` : template for the hat control.
- `layout.html` : parent template for the layout containing navigation bar, which is extended by all other pages.
- `main.html` : template for the home page from which you can go to observer.

### `config.yaml`

It contains the configuration settings for the RGB colours, blink frequency and effect duration for the headset. The
example of this file is shown on GitHub but it is different on all the hats based on the passed configurations.

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

## Running the code for development

### Making changes on hat 4 and 5

1. Clone this repository to your local machine.
2. Make changes in `server.py` or any of the HTML/CSS files.
3. In development mode, you need to comment out the lines in `leds/server/server.py` that relate
   to `WS2801Headset`. You will also need to comment out all of the routese that contain `leds` (this is all of the
   routes after `"/main"`). This is because all of these imports and routes are related to LEDs, so they will not work
   locally on your machine.
5. Run the app as follows:

 ```
 cd /python
 python3 leds/server/server.py local
 
 or 
 
 python leds/server/server.py local
 ```

6. Go to `localhost:5000` or `http://127.0.0.1:5000/` in your web browser. If import errors appear, check again that
   you have commented out everything related to the `leds` in `server.py`.
7. Make sure the hats are turned on.
8. After introducing the changes, transfer the updated files from `leds` folder to the hats using WinSCP or Ansible.
9. Open your web browser and navigate to http://192.168.100.104:5000/ (for player 4) or http://192.168.100.105:5000/ (
   for player 5) to view the web application.

### Making changes to led functionality

1. Clone this repository to your local machine.
2. Make changes in `ws2801_headset.py` and `headset.py` to edit LED functionality. In order to add new functionality,
   it may be necessary to add new buttons in the `hat_standalone.html` file, and new app routes in eh `server.py` file,
   both located in the `server` folder.
3. Copy the code onto the hats. You can do this by following 'Step 4' from the 'Setup Notes' section above.
4. Open the hat webpage.
    1. If connected on the same network as the Synch.Live router, then go to the following web address:
       `192.168.100.1xx:5000`. Replace the 'xx' with the hat number. For example, to access 'hat 04', replace 'xx'
       with '04'
       so that the address is `192.168.100.104:5000`.
    2. Otherwise, if connecting via SSH, on a different connection from the hats:
        1. Make sure that the Synch.Live router is connected to the wider internet. This will need port forwarding setup
           from your home router to the Synch.Live router.
        2. Setup Putty to allow you to view the hat's page on your local browser:
            1. Open Putty.
            2. Set the 'Host Name' as `synchlive.ddns.net`.
            3. Set the 'Port number' to the port number set up on your home router to forward to the Synch.Live router.
            4. In the 'Auth' tab in the sidebar, upload your SSH private key in .ppk format. Make sure that the
               corresponding public key is saved to the observer's list of accepted SSH keys.
            5. In the 'Tunnels' tab, set the 'Source Port' to `5000` and the 'Destination' as `localhost:xxxx` where
               'xxxx' is any port number in the range 1000-9000. It is important that this isn't the same as anybody
               else who will be accessing the page remotely at the same time as you.
            6. In the 'Data' tab, set the "Auto-login username" to `pi`.
            7. In the 'Session' tab, press `Save`.
        3. Run the Putty session setup in the previous step. It may be necessary to enter the passphrase to your SSH
           key.
        4. Enter the following command into the command line: `ssh -L xxxx:localhost:5000 playerY -N` where 'xxxx' is
           the
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

Currently, only hat 4 and 5 have the files with recently developed Flask web application. If you want to extend it to
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

## How to Use Hat App

To use this Flask web application, follow these steps:

1. Make sure that the Synch.Live router is turned on.
2. Connect to the Synch.Live network using the password.
3. Make sure the hat is turned on.
4. Open your web browser and navigate to http://192.168.100.104:5000/ (for player 4) or http://192.168.100.105:5000/ (
   for player 5) to view the web application.
5. Use the panel to control the LEDs of the hat.

- **'Colour' tab**: allows you to try main and secondary colour, blinks per minute and duration time. There is an
  option of saving the configuration in a config.yaml file, which is later used to apply effects.
- **'Effects' tab**: configurations from config.yaml file are used to run effects such as pilot, exposure, breathe and
  two
  types of fade. If config.yaml doesn't exist (it was not saved), default colours are used.
- **'Animations' tab**: contains pre-defined effects such as rainbow, fire, police lights, paparazzi and disco lights.
- **Home page**: navigates to the observer app.
- **Hat 4**: navigates to hat 4 app.
- **Hat 5**: navigates to hat 5 app.

### Troubleshooting notes

- Flask issues
    - Most of them are related to the incorrect routes, so when changing functionality make sure that you are
      requesting the right one. The app is running in debug mode to make debugging easier.

- Server doesn't start on boot
    - When the routes in the `server.py` are incorrect, it can't render any templates.
    - If it is still not working, SSH into the hat and run the following command to check the logs for the server:
      ```journalctl -u hat.service```
