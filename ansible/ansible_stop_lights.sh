#! /bin/bash
cd ~/src/synch-live/ansible
ansible-playbook test_lights.yml -t stop -f 10
