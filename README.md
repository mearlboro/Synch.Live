# Synch.Live video library

This branch contains development for the **observer** system equipped with the
RPi Camera Module, as well as example media files and code that can be used
offline for testing and analysis.


## Contents

The code in the `camera` folder is to be run by the **observer** system, and
deployed via Ansible (for config, see branch `dev-ansible`):

* `camerahelper.py` - helper code used for fetching frames from the sensor and
streaming
- `detection.py` - use HSV filters on an OpenCV image to detect the lights of
the players on each frame
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

    pipenv shell requirements.txt


### Extracting and plotting trajectories

To extract trajectorie from video using non-real time tracking use

    python trajectories.py track --filename $video_file --out $traj_file

The extracted trajectories will be saved as a numpy dump.


To plot the extracted trajectories use

    python trajectories.py plot --filename $traj_file --out $image_file


### Image processing tools

To inspect colours of an image, and produce HSV values of colour ranges

    python hsv_range.py --filename $image_file

An OpenCV GUI with sliders for hue, saturation and value for the lower and
higher ends of the colour range to be selected from the image.
Move sliders to replace excluded colour with black until the desired range is
found.
