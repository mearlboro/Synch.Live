#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "usage: ./setup_sd_card.sh [player_number]" & exit
fi
case $1 in
    '' | *[!0-9]*) echo "setup_sd_card.sh: arg not a number" & exit
esac

if [ ! -d /media/$(whoami)/boot ] || [ ! -d /media/$(whoami)/rootfs ]; then
	echo "setup_sd_card.sh: make sure the Raspberry Pi drives are mounted" & exit
fi


number=$1
ipaddr="192.168.100.$((100+$number))"
hostname="player$1"

echo "setup_sd_card.sh: setting up $hostname with IP address $ipaddr"

echo "$hostname" > etc/hostname
sed -i "/static ip_address/s/192.168.100.[0-9][0-9][0-9]/$ipaddr/" etc/dhcpcd.conf

sudo cp etc/* /media/$(whoami)/rootfs/etc/


if [ ! -f .ssh/synchlive.pub ]; then
	echo "setup_sd_card.sh: need to generate an SSH key first, see README"
fi

echo "setup_sd_card.sh: copying wireless network settings and SSH keys"

sudo cp boot/* /media/$(whoami)/boot/

cat .ssh/synchlive.pub > .ssh/authorized_keys
mkdir /media/$(whoami)/rootfs/home/pi/.ssh
cp .ssh/authorized_keys /media/$(whoami)/rootfs/home/pi/.ssh/authorized_keys

umount /media/$(whoami)/boot
umount /media/$(whoami)/rootfs

echo "setup_sd_card.sh: done"
