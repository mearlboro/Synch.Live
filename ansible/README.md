# Deploy Synch.Live fleet using Ansible

The code and files in this directory are used to configure hardware and deploy software to any number of Synch.Live player hats, assuming they have been setup with Raspberry Pi OS, an IP and hostname, network connection and SSH access.

A detailed explanation of what is being setup, as well as a quick introduction to concepts in Ansible, can be read [here](https://mis.pm/synch-live-part-4#player-deploy).

### Instructions

First, [install Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installation-guide) on your machine. You will be usign this machine as a control node for the devices that need to be deployed.

Ansible can send commands in parallel for all players, so you should use as argument to `-f` the number of hats in your fleet. We assume 10 hats.

1. Boot up all players and make sure they have enough battery. Wait for a minute just to make sure all have booted.
2. Configure hardware, by running

        ansible-playbook config-hardware.yml -f 10

3. Install necessary software, by running

        ansible-playbook install-software.yml -f 10

4. Reboot all the players, by running

        ansible-playbook reboot.yml -f 10
