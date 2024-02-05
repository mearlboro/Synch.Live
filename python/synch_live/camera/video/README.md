# Synch.Live camera video stream code

This package exists to provide the server with a video stream showing tracking information.

## `__init__.py`

In the `__init__.py` file are two classes, `Camera`, which wraps a video stream, and `VideoProcessor`,
which provides the video stream with tracking information and an interface to control it.
Importantly, both classes need to be instantiated on the main thread in order to be able to use `/dev/video*` devices.
In order to allow for this, remain agnostic about how the app is served,
and allow the server to start up independently of the video processor,
these classes are instead instantiated in a child process as described below.

## `pool.py`

This defines a single class `VideoProcessHandle`, which stores a single process pool (i.e. on the class) behind a lock,
shared by all instances.
It has two methods: `exec` blocks until the lock is acquired, and then schedules a job and blocks waiting for the result,
communicating with the child process over IPC; `reset_video_process` acquires the lock, shuts down the process pool,
and creates a new one.
On `SIGINT` the lock is acquired and the pool gets shut down—the lock not being released until exit to prevent
new jobs from being scheduled.

## `proxy.py`

This defines two classes, `VideoProcessorServer` and `VideoProcessorClient`, effectively a skeleton and stub respectively.
`VideoProcessorServer` stores a single `VideoProcessor` and provides static versions of its methods relevant to the Flask server.
The static methods all invoke the corresponding instance method on the stored `VideoProcessor`,
avoiding the difficulty of needing to pass a picklable instance in order to invoke methods
(`VideoProcessor` contains a lock, which is not picklable).
`VideoProcessorClient` also implements the methods of `VideoProcessor` relevant to the Flask server,
but calls `exec` on new `VideoProcessHandle`s using the static methods defined on `VideoProcessorServer`.
The server should interact with `VideoProcessorClient` to control the video feed.
