# Quickstart Synch.Live player

You should first generate an SSH key for all players, by running the command below (with your preferred passphrase)

        ssh-keygen -t dsa -N "passphrase" -C "$(whoami)@synch.live" -f .ssh/synchlive

Then, for each player headset that needs to be deployed:

1. Install Raspberry Pi OS Lite onto the SD card
2. Make sure SD card is mounted. Two partitions are expected: `boot` and `rootfs`
3. Run the setup script for the current player number

        ./setup_sd_card.sh 1
