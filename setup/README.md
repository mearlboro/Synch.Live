# Quickstart Synch.Live player

The code and files in this directory are used to quickstart an SD card running Raspberry Pi OS Lite for a Synch.Live player hat. The steps are described in detail [here](https://mis.pm/synch-live-part-4#player-setup).

### Network

This setup expects a particular network configuration, on the subnet `192.168.100.0/24`. The router's IP address is assumed to be `192.168.100.1`. The IP addresses for the players are statically allocated, such that the machine with the hostname `player1` will be found at `192.168.100.101`. 

Make sure that you modify lines 6 and 7 of the file `boot/wpa_supplicant.conf` with the network name (SSID) and password of your WiFi network.

### SSH keys

You should first generate an SSH key which will be used to communicate with all players, by running the command below (with your preferred passphrase):

        ssh-keygen -t ed25519 -N "passphrase" -C "$(whoami)@synch.live" -f .ssh/synchlive

### Instructions

Then, for each Raspberry Pi in the system (headset or observer) that needs to be deployed:

1. Install Raspberry Pi OS Lite onto the SD card
2. Make sure SD card is mounted. Two partitions are expected: `boot` and `rootfs`
3. Run the setup script for the current player number

        ./setup_sd_card.sh 1

   or with the parameter set to 0 for the observer

        ./setup_sd_card.sh 0
