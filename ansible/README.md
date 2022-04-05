# Deploy Synch.Live fleet using Ansible

The code and files in this directory are used to configure hardware and deploy software to any number of Synch.Live player hats, assuming they have been setup with Raspberry Pi OS, an IP and hostname, network connection and SSH access.

A detailed explanation of what is being setup, as well as a quick introduction to concepts in Ansible, can be read [here](https://mis.pm/synch-live-part-4#player-deploy).

### Setup Instructions

First, [install Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installation-guide) on your machine. You will be usign this machine as a control node for the devices that need to be deployed.

Ansible can send commands in parallel for all players, so you should use as argument to `-f` the number of hats in your fleet. We assume 10 hats.

1. Boot up all players and make sure they have enough battery. Wait for a minute just to make sure all have booted.
2. Configure hardware, by running

        ansible-playbook config_hardware.yml -f 10

3. Install necessary software, by running

        ansible-playbook install_software.yml -f 10

4. Make sure that the clock synchronisation daemon is installed and well configured

        ansible-playbook sync_time.yml -f 10

5. Reboot all the players, by running

        ansible-playbook reboot.yml -f 10 --tags reboot

6. To copy off the latest Python files used to control the leds/run the experiment

        ansible-playbook synch_code.yml -f 10


To only run ansible for the `observer` (note the comma at the end)

        ansible-playbook install_software.yml -i observer,

To only run ansible only for the `players`

        ansible-playbook install_software.yml --limit players

# Commanding the fleet

## Testing / mocking

### Sync test
#### Start

We begin by synchronising clocks using the `sync_time` playbook

    ansible-playbook sync_time.yml -t experiment -f 10

This test consists of chaotic blinks for 250 seconds which slowly align
themselves until they sync. Then they keep on blinking periodically for
another 100 seconds. If the clocks are the same, the test is a success
when all hats blink in sync at the end.

You should edit the value for variable `MINUTE` below to schedule a time
to start the test. The script will be run with cron and will always start
the test at 10 seconds after the specified minute.

    ansible-playbook test_lights.yml -t schedule -f 10 --extra-vars MINUTE=30

#### Stop

To turn off all LEDs blinking and remove cronjob

    ansible-playbook test_lights.yml -t stop -f 10 --extra-vars MINUTE=30

Make sure you update the `MINUTE` variable to match the cronjob created
in the previous section.


### Cluster SSH

The tool `clusterssh` (package name `clusterssh` in Debian and Raspberry Pi OS)
is particularly useful for testing Synch.Live as it allows synchronous
simultaneous SSH connections to all players at once.

Install the tool, and preconfigure a cluster with the player's hosts

    apt install clusterssh
    mkdir ~/.clusterssh
    echo "players player1 player2 player3 player4 player5 player6 player7 player8 player9 player10" > ~/.clusterssh/clusters

Then simply run

    cssh pi@players

to connect to all players at once, and run commands directly.

## Experiment

To copy off the latest Python files used to control the leds/run the experiment

        ansible-playbook sync_code.yml -f 10


To synchronise the clocks for an experiment

        ansible-playbook sync_time.yml -f 10 --tags experiment


To start an experiment at a specific time, e.g. 30 minutes past the hour

        ansible-playbook experiment.yml --limit players -f 10 --tags start --extra-vars MINUTE=30


To stop an experiment running at a specific time, e.g. 30 minutes past the hour

        ansible-playbook experiment.yml --limit players -f 10 --tags stop --extra-vars MINUTE=30


To shutdown all players

        ansible-playbook reboot.yml -f 10 --tags shutdown


# Troubleshooting

## Ansible uses python2 instead of python3

This is configured in `ansible/hosts` and should be picked up by the playbooks.
If that doesn't happen, it may be that your local Ansible doesn't use python3.
To check:

    ansible --version | grep "python version"

You can also force the flag to run python3 when running the playbook e.g.

    ansible-playbook install_software.yml -e 'ansible_python_interpreter=/usr/bin/python3'

See also the Ansible [documentation](https://docs.ansible.com/ansible/latest/reference_appendices/python_3_support.html#using-python-3-on-the-managed-machines-with-commands-and-playbooks)


## Raspbian Buster get update issue (2021/12/20)

Given some changes in the source repos of Raspberry Pi OS this error may appear when
running Ansible to update packages

        Get:1 http://archive.raspberrypi.org/debian buster InRelease [32.6 kB]
        Get:2 http://raspbian.raspberrypi.org/raspbian buster InRelease [15.0 kB]
        Reading package lists... Done
        E: Repository 'http://archive.raspberrypi.org/debian buster InRelease' changed its 'Suite' value from 'testing' to 'oldstable'
        N: This must be accepted explicitly before updates for this repository can be applied. See apt-secure(8) manpage for details.
        E: Repository 'http://raspbian.raspberrypi.org/raspbian buster InRelease' changed its 'Suite' value from 'stable' to 'oldstable'
        N: This must be accepted explicitly before updates for this repository can be applied. See apt-secure(8) manpage for details.


To fix, SSH into the Pi and run

        sudo apt update --allow-releaseinfo-change

A way to include this in the config is currently not exposed in the API for the Ansible `apt` module.
