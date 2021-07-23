# Synch.Live video library

This branch contains development for the observer system equipped with
the Raspberry Pi Camera Module.
Moreover it provides extra tools for extracting hues from an image and
extracting and plotting trajectories from a video.
Both are located in `camera`.

`media` folder contains footage of players wearing the hats, snapshots, and
extracted trajectories.

### Observer code

All code located in the `camera` folder is supposed to run on the observer.
Setup instructions on `origin/dev-ansible` branch. Depends on `picamera`
package so it won't run on a regular dev environment.

Object detection is in `detection.py` and real-time tracking in `tracking.py`.
`server.py` runs a Flask web app for calibration and real time preview of
footage.


### Tools for testing the detection and tracking

Code in the `tracking` folder is designed to be run when there is access
to a GUI, on any Linux dev environment. The required Python packages are
in `camera/requirements.txt`.

To test out object detection by hue, saturation and luminosity on a given
image, run

    python3 hsv_range.py --filename image.png

This launches a GUI with trackbars for testing out how the detection
will work on a given image. The script will print the HSV min and max
values to terminal, which should be used as params in `detection.py`.


To extract trajectories from video using one of the OpenCV trackers
`CSRT`, `KCF`, `BOOSTING`, `MIL`, `TLD`, `MEDIANFLOW`, `MOSSE`, run

    python3 trajectories.py track --filename video.png --tracker CSRT --out data.np

The video will be displayed with bounding boxes and labels as the
objects are tracked.
`data.np` is saved in the `media/trajectories` folder.

This is useful to compare performance of real time tracker to more
accurate but less efficient trackers. Defaults to CSRT tracker. Dumps
the trajectories as Numpy 3D arrays that represent the frame, the
player, and the coordinates.
The object detection happens only on the first frame and is the same
function as the real-time system uses, from `detection.py`.


To plot trajectories, run

    python3 trajectories.py plot --filename data.np --out plot.png

The `plot.png` file will be dumped in the `media/plots` folder.
