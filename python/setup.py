from setuptools import find_packages, setup
setup(
    name="camera",
    version="0.0.1",
    packages=find_packages(include=["camera", "camera.*"]),
)
