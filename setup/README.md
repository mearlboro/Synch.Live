# Quickstart Synch.Live system

The code and files in this directory are used to quickstart an SD card running Raspberry Pi OS Lite for a Synch.Live player hat or observer. The steps are described in detail [here](https://mis.pm/synch-live-part-4#player-setup).

### Network

This setup expects a particular network configuration, on the subnet `192.168.100.0/24`. The router's IP address is assumed to be `192.168.100.1`. The IP addresses for the players are statically allocated, such that the machine with the hostname `player1` will be found at `192.168.100.101`.

The IP address for the observer is `192.168.100.100`.

Make sure that you modify lines 6 and 7 of the file `boot/wpa_supplicant.conf` with the network name (SSID) and password of your WiFi network.

### SSH keys

You should first generate a public-private key pair which will be used to communicate with all players via secure shell (SSH), by running the command below (with your preferred passphrase):

        ssh-keygen -t ed25519 -N "passphrase" -C "$(whoami)@synch.live" -f .ssh/synchlive

The public key will be included into the file `.ssh/authorised_keys` by the setup script.

### Instructions

Then, for each Raspberry Pi in the system (headset or observer) that needs to be deployed:

1. Install Raspberry Pi OS Lite onto the SD card. On Linux, plug the SD card in and find the device name by running `sudo fdisk -l`. Downloading the [iso](https://www.raspberrypi.com/software/operating-systems/) and use `dd` to write the OS to disk, e.g.

        pv 2021-01-11-raspios-buster-armhf-lite.img | sudo dd of=/dev/sdb

2. After the imaging is complete, make sure SD card is mounted. Two partitions are expected: `boot` and `rootfs`. You can check this by running `lsblk`, and you should see something like this:

    mmcblk0        8:16   1  59.5G  0 disk
    ├─mmcblk0p1    8:17   1   256M  0 part  /media/m/boot
    └─mmcblk0p2    8:18   1   1.5G  0 part  /media/m/rootfs


3. Run the setup script for the current player number

        ./setup_sd_card.sh 1

   or with the parameter set to 0 for the observer

        ./setup_sd_card.sh 0

### A note for Observer OS (06/2022)

We use a version of Rasbperry Pi OS Lite based on Debian Buster. Since April 2022, Raspberry Pi has released a new version based on Debian Bullseye. While the changs are irrelevant to the players, considerable changes have been made to [the camera API](https://www.raspberrypi.com/news/bullseye-camera-system/) which no longer supports the PiCamera library currently used by this project.

Until our codebase is updated to a more generic PiCamera approach, the sstem muste be deployed with  [a Buster-based version of RPi OS Lite](https://downloads.raspberrypi.org/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2022-04-07/2022-04-04-raspios-buster-armhf-lite.img.xz), which is now referred to as Raspberry Pi OS (Legacy) on the RPi website.
