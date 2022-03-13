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

The `camera` package contains three sub packages, `core`, `server` and `tools`.

### `core`
A package including all the core tools for performing image detection, tracking,
and emergence computation on a video file of flocking.

- `detection.py` - use HSV filters on an OpenCV image to detect the lights of
the players on each frame
- `emergence.py` - calculate emergence values given trajectories of players
- `logger.py` - logging setup to be used when the system runs live
- `tracking.py` - impplements a real-time tracker to be used when the system
runs live

The code in `emergence.py` is contributed by [Dr. Pedro Mediano](https://github.com/pmediano).

### `server`

- `server.py` - runs a Flask app to stream the camera footage and a web control
panel for running experiments
- `local.py` - runs a Flask app to stream some video footage and a web control
panel for running experiments
* `video.py` - helper code used for fetching frames from the sensor or from a video
file and streaming

### `tools`
A package that can be used to run the tools in `core` for development and testing
on an environment that is not the Observer.

- `hsv_range.py` - tools for extracting colour ranges from an image
- `trajectories.py` - extracts and plots trajectories from a video recorded in
the experiment, but using non-real time OpenCV trackers


## Setup Notes

### Packaging

    $ cd python
    $ pip install -e .

### infordynamics.jar
`emergence.py` uses the [Java Information Dynamics Toolkit (JIDT)](https://github.com/jlizier/jidt/)
by [Dr. Joe Lizier](https://github.com/jlizier). A copy is included in the current repository.

The version used is a slightly modified `v1.5-dist` rebuilt with `ant` and is included in
the `camera/` folder as `infodynamics.jar`. The JIDT code is called using JPype.
The following steps were taken to produce our version of JIDT:

    $ sudo apt install ant
    $ git clone git@github.com:jlizier/jidt.git

Then the file `java/source/infodynamics/measures/continuous/MutualInfoMultiVariateCommon.java`
is edited to keep the vectors of observation sets in the `finaliseAddObservations()` function
by commenting out the following lines:

    vectorOfSourceObservations = null;
    vectorOfDestinationObservations = null;

Finally an `infodynamics.jar` package is built by calling

    $ ant jar


## Running the code for development

To run parts of the code locally you must install the pkgs in `python/camera/requirements.txt`

We recommend packaging with `pipenv` and the code should be run inside a `pipenv`
shell in the `camera/` folder. The `pipenv` only requires installing the requirements
once unless more packages are added.

    $ cd python/camera
    $ pipenv install -r requirements.txt
    $ pipenv shell

### Extracting and plotting trajectories

To extract trajectorie from video using non-real time tracking use

    $ cd python/camera/tools
    $ python trajectories.py track --filename $video_file --out $traj_file

The extracted trajectories will be saved as a numpy dump.

To plot the extracted trajectories use

    $ cd python/camera/tools
    $ python trajectories.py plot --filename $traj_file --out $image_file


### Image processing tools

To inspect colours of an image, and produce HSV values of colour ranges

    $ cd python/camera/tools
    $ python hsv_range.py --filename $image_file

An OpenCV GUI with sliders for hue, saturation and value for the lower and
higher ends of the colour range to be selected from the image.
Move sliders to replace excluded colour with black until the desired range is
found.


### Calculating emergence

To test the emergence calculator on the trajectories, run

    $ cd python/camera/core
    $ python emergence.py --filename $traj_file


### Mocking the streaming server

Then to run a local server mocking the PiCamera by feeding in video footage from `media`

    $ cd python
    $ python camera/server/server.py local

To use different video streams you can use an environmental variable

    $ cd python
    $ VIDEO_PATH='../media/video/2.avi' python camera/server/server.py local

or 

    $ cd python
    $ export VIDEO_PATH='../media/video/1.avi'
    $ python camera/server/server.py local

### Running the Observer

> **Note**: this can only be run on a RaspberryPi with a PiCamera attached.

    $ cd python
    $ python3 camera/server/server.py observer



