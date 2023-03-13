# Synch.Live camera code

The code in this package performs object detection and object tracking to
produce trajectories, and computes information-theoretical causal emergence of
these trajectories using the positions of each player and the centre of mass of
the group as described in:

Rosas FE*, Mediano PAM*, Jensen HJ, Seth AK, Barrett AB, Carhart-Harris RL, et al.
(2020) [_Reconciling emergences: An information-theoretic approach to identify
causal emergence in multivariate data_](https://doi.org/10.1371/journal.pcbi.1008289).
PLoS Comput Biol 16(12):e1008289.

## Contents

The `camera` package contains several sub packages, which are described below:
- `core` - core tools for performing image detection
- `server` - Flask app for the Observer UI
- `video` - a package for handling the video feed in a separate process to the server
- `db` - a package that connects to an SQLite database and includes functions for writing experiment parameters and trajectories to the database
- `tools` - a package that can be used to test the `core` functionality in a development environment

It also contains a folder `config` to store YAML config files.

### `core`
A package including all the core tools for performing image detection, tracking, and emergence computation on a video file of flocking.

- `detection.py` - use HSV filters on an OpenCV image to detect the lights of
the players on each frame
- `emergence.py` - calculate emergence values given trajectories of players
- `logger.py` - logging setup to be used when the system runs live
- `tracking.py` - impplements a real-time tracker to be used when the system
runs live
- `motion_models.py` - implements Kalman filter motion models for predicting
the next position of each tracked object

The code in `emergence.py` is contributed by [Dr. Pedro Mediano](https://github.com/pmediano).


### `server`

Contains the web app code structured using Flask blueprints. The app structure uses the following files:
* `__init__.py` - initialises the Flask app and registers the individual page blueprints
* `players_listener.py` - page to detect hat players connected to the local network and display links for them
* `setup.py` and `setup_items.py` - web pages for running Ansible scripts from the web app. `setup.py` runs all Ansible scripts (note that this takes a long time to run). `setup_itmes.py` allows the user to select a specific script to run from a menu; at present this does not contain all possible scripts but could be extended to do so
* `tracking.py` - page for setting experiment parameters (including calibration .yaml forms) and starting / stopping the experiment
* `experiment.py` - page for viewing the experiment and switching between manual and emergence mode
* `download.py` - page for downloading data from the database

Visual styling code is contained in the following sub-folders:

* `templates/` - contains HTML templates used by the Flask server to render the web UI

* `static/` - contains CSS, .js and other static elements for rendering the web UI

* `styles/` - contains Tailwind style code

### `tools`
A package that can be used to run the tools in `core` for development and testing
on an environment that is not the Observer.

- `hsv_range.py` - tools for extracting colour ranges from an image
- `trajectories.py` - extracts and plots trajectories from a video recorded in
the experiment, but using non-real time OpenCV trackers
- `colour.py` - tools to convert from OpenCV HSV to HTML hex and back
- `config.py` - tools used to manipulate config files

### `video`

A package that contains helper code to stream and fetch frames from the sensor or from a video file in a thread-safe way. See the README in the folder for additional detail.

### Config
The config folder contains YAML files with detection, tracking, camera and
experimental settings. A default config is in `camera/config/default.yml` which
is loaded by the server unless the `CONFIG_PATH` environmental variable is set.

A new config should be added for each new experimental configuration: for example
if a new space is being used, it is likely that settings need to change according
to the dimensions and illumination of the space.

## Setup Notes

### Running the code

The following commands install all Synch.Live packaging. We recommend using pip install within a virtual environment that runs on Python 3.7. This specific version is required for the current Observer Pi OpenCV set-up, so if you use a more recent version locally then you may find that your code does not run on the Observer.

    $ cd python
    $ pip install -e.

Run the following also; note that `npm` must be installed on the machine. Npm installation is global (i.e. not contained within the virtual enviornment).

    $ cd python/synch_live/camera/server
    $ npm install

The Flask app can be run (in debug mode) using the following commands:

    $ cd python
    $ flask --app synch_live.camera.server run --debug

If you are running the code on the Observer, then the Flask app will start on boot automatically. If you want to restart the app, run the following from anywhere in the system:

    $ sudo systemctl restart flask

### infordynamics.jar
`emergence.py` uses the [Java Information Dynamics Toolkit (JIDT)](https://github.com/jlizier/jidt/)
by [Dr. Joe Lizier](https://github.com/jlizier). A copy is included in the current repository.

The version used is a slightly modified `v1.5-dist` rebuilt with `ant` and is included in the `camera/` folder as `infodynamics.jar`. The JIDT code is called using JPype.
The following steps were taken to produce our version of JIDT:

    $ sudo apt install ant
    $ git clone git@github.com:jlizier/jidt.git

Then the file `java/source/infodynamics/measures/continuous/MutualInfoMultiVariateCommon.java`
is edited to keep the vectors of observation sets in the `finaliseAddObservations()` function by commenting out the following lines:

    vectorOfSourceObservations = null;
    vectorOfDestinationObservations = null;

Finally an `infodynamics.jar` package is built by calling

    $ ant jar


### Extracting and plotting trajectories

The code that was previously used to extract trajectories is in `trajectories.py`, however this is no longer working due to deprecation of some OpenCV features. You can download trajectories from the SQLite database instead (stored on the Observer) via the web app.

### Image processing tools

> **Note**: Not recently tested - note that this may not work smoothly with the database .csv as it was written for a numpy dump, so may require some adjustments

To inspect colours of an image, and produce HSV values of colour ranges

    $ cd python/camera/tools
    $ python hsv_range.py --filename $image_file

An OpenCV GUI with sliders for hue, saturation and value for the lower and
higher ends of the colour range to be selected from the image.
Move sliders to replace excluded colour with black until the desired range is
found.


### Calculating emergence

> **Note**: Not recently tested - note that this may not work smoothly with the database .csv as it was written for a numpy dump, so may require some adjustments

To test the emergence calculator on the trajectories, run

    $ cd python/camera/core
    $ python emergence.py --filename $traj_file


### Mocking the streaming server

Then to run a local server mocking the PiCamera by feeding in video footage from `media`, use a testing config set through an environmental variable and place the video in the `/python/instance` folder.

## Running the Observer

To run the server on the Observer of the Synch.Live system, the config file can be set in the same way using the env varibale `CONFIG_PATH`

#### Generic Camera

> **Note**: this has only been tested on Linux

You can run the observer if you have a camera connected to your computer, this can be:
+ integrated laptop camera
+ external USB webcam
+ camera/stream connected via a Capture Card

> Generic Camera's cannot be calibrated from the internal webpage, unlike the RaspberryPi Camera.

##### Linux

> **Note**: Not recently tested; code likely needs updating to run with updated system

Your user must be a part of the `video` group, or you must have permission to access the video device in `/dev/videoN`

check which camera device you may want to use `mpv`

    $ mpv /dev/video0

in this case my webcam is at index 0.

If you do not see your video stream, then check the available video devices with `ls /dev | grep video` and try other indices.

Using the index of your camera that you found earlir, update the CONFIG_PATH and re-start the Flask app.

    $ cd python
    $ CONFIG_PATH=./camera/config/generic-camera.yml
    $ flask --app synch_live.camera.server run


# Troubleshooting

RaspberryPi OS Lite does not include Java, GTK, or other libraries that are used by the system. A few errors may occur:

    ImportError: libgtk-3.so.0: cannot open shared object file: No such file or directory

Fix by installing `libgtk-3.0` (see also [[1]](https://stackoverflow.com/questions/71512811/error-when-loading-imutils-libgtk-3-so-0-cannot-open-shared-object-file-no-su))

    ImportError: libImath-2_2.so.12: cannot open shared object file: No such file or directory

Fix by installing `libilmbase-dev`, `libopenexr-dev`, `libgstreamer1.0-dev` (see also [[2]](https://github.com/EdjeElectronics/TensorFlow-Object-Detection-on-the-Raspberry-Pi/issues/18))

    RuntimeError: module compiled against API version 0xe but this version of numpy is 0xd

Make sure you install a version of `numpy` (>1.20) compatible with the one of OpenCV. `apt` often normally installs an older version. Best to use a Python environment due to possible issues with `pip` See also [[3]](https://github.com/pypa/pip/issues/9542).

    jpype._jvmfinder.JVMNotFoundException: No JVM shared library file (libjvm.so) found. Try setting up       the JAVA_HOME environment variable properly.

Make sure you install Java, i.e. `defaul-jdk`. Java 11 is best.

All these packages have now been included in the Ansible setup script `install_software.yml`, so if the setup was done correctly, these packages are installed, and still any of the above errors show up when running observer code, please submit an issue.


