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

The code in the `camera` folder is to be run by the **observer** system, and
deployed via Ansible.

* `camerahelper.py` - helper code used for fetching frames from the sensor and
streaming
- `detection.py` - use HSV filters on an OpenCV image to detect the lights of
the players on each frame
- `emergence_calculator.py` - calculate emergence values
- `hsv_range.py` - tools for extracting colour ranges from an image
- `logger.py` - logging setup to be used when the system runs live
- `server.py` - runs a Flask app to stream the camera footage and a web control
panel for running experiments
- `tracking.py` - impplements a real-time tracker to be used when the system
runs live
- `trajectories.py` - extracts and plots trajectories from a video recorded in
the experiment, but using non-real time OpenCV trackers

The `media` folder contains footage of players from the first pilot and other
related multimedia
* example video files are in `media/video` and snapshots from them in `media/img`
* example trajectory files extracted from those videos are in the `media/trajectories`
folder and use the `.np` extension
* plots of these trajectories in `media/plots`

## Running the code for development

To run parts of the code locally you must install the pkgs in `camera/requirements.txt`

We recommend packaging with `pipenv` and the code should be run inside a `pipenv`
shell in the `camera/` folder

    $ cd python/camera
    $ pipenv shell requirements.txt


### Extracting and plotting trajectories

To extract trajectorie from video using non-real time tracking use

    $ python trajectories.py track --filename $video_file --out $traj_file

The extracted trajectories will be saved as a numpy dump.


To plot the extracted trajectories use

    $ python trajectories.py plot --filename $traj_file --out $image_file


### Image processing tools

To inspect colours of an image, and produce HSV values of colour ranges

    $ python hsv_range.py --filename $image_file

An OpenCV GUI with sliders for hue, saturation and value for the lower and
higher ends of the colour range to be selected from the image.
Move sliders to replace excluded colour with black until the desired range is
found.

### Calculating emergence

The code in `emergence_calculator.py` is contributed by [Dr. Pedro Mediano](https://github.com/pmediano)
using the [Java Information Dynamics Toolkit (JIDT)](https://github.com/jlizier/jidt/)
by [Dr. Joe Lizier](https://github.com/jlizier).

To test the emergence calculator on the trajectories, run

    $ python emergence_calculator.py --filename $traj_file


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
