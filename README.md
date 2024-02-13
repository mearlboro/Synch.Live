# Synch.Live
An art experience and collective behaviour experiment conceptualised by [Hillary Leone](https://cabengo.com) and based on an information-theoretic criterion of emergent behaviour developed by Rosas, Mediano et al.


## About this repository

This is the original repository for the initial Synch.Live 1.0 prototype.
It has been forked to the official [organisation](https://github.com/synch-live/Synch.Live1.0) where it has been improved upon by other authors, including students from Imperial College.

> [!IMPORTANT]
> **For the most up to date version of the repository please refer to the [official organisation repository](https://github.com/mearlboro/Synch.Live/tree/feat/MSc-project).**


The updates in the fork are also included in the current repository on branch [feat/MSc-project](https://github.com/mearlboro/Synch.Live/tree/feat/MSc-project) after merging PR#13 and #14. The current main branch contains the same codebase as the **June 2022** experiments.
For more details of the development process please see the [mis.pm website](https://mis.pm/synch-live).

> [!IMPORTANT]
> Code in this repository should be used only if using the prototype of Synch.Live.


## Instructions

The project uses lots of dependencies that are related to Raspberry Pi, OpenCV etc and are configured for relevant hardware.
For local development it is best to run in Nix using the provided `shell.nix`:

```sh
cd python
nix-shell shell.nix
```

Alternatively the `camera` package can be installed using `pip`, make sure you always work in a virtual environment:

```sh
cd python
python -m venv venv
source venv/bin/activate
pip install -e.
```

## Acknowledgements

This repository contains the development efforts until 2022, with contributions by Madalina Sas (@mearlboro), Dr. Pedro Mediano (@pmediano) and Christopher Lockwood (@lockwoodchris).

Hardware deisgn by Andrei Sas (@andrei-sas-dop) and Madalina Sas.
Development of the project was also supported by Dr. Daniel Bor and Dr. Fernando Rosas.

