# Quickstart Synch.Live player

1. Install Raspberry Pi OS Lite onto the SD card
2. Make sure SD card is mounted. Two partitions are expected: `boot` and `rootfs`
3. Generate an SSH key pair with your preferred passphrase

        ssh-keygen -t dsa -N "passphrase" -C "$(whoami)@synch.live" -f .ssh/synchlive

4. Run the setup script for the current player number

        ./setup_sd_card.sh 1
