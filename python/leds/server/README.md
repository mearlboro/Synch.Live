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

1. Comment out the lines in server.py which are related to the LEDs.
2. Make changes in HTML, CSS or `server.py`.
3. Push to GitHub and transfer the updated files to the hats using WinSCP.
4. [Add stuff about systemd to start server on boot for new hats]

## How to Use [rewrite this for development and user testing]

To use this Flask web application, follow these steps:

1. Clone this repository to your local machine.
2. Navigate to the server directory.
3. Make sure you have Python and Flask installed on your machine.
4. Make sure the hat is turned on.
5. Open your web browser and navigate to http://192.168.100.104:5000/ (for player 4) or http://192.168.100.105:5000/ (
   for player 5) to view the web application.
6. Use the web interface to control the LEDs of the player's hat.

### Troubleshooting notes

- Flask debugger issues
    - most Flask issues are related to the incorrect routes, so when changing functionality make sure that you are
      requesting the right one.

- Server doesn't start on boot
    - happens only when the flask app itself is incorrect, so it can't render any templates.
