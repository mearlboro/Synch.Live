## Testing the Synch.Live players

The current branch contains the basic code and minimum Ansible config to
run various stress tests or sync tests on the players.

### Lights test

This test uses a snippet of code from tutorials-raspberrypi.com and
cycles through different colours and behaviours. The script is run
immediately as an ansible command, so it's likely it won't be run in
perfect sync. The choreography is done running after around a minute.

    ansible-playbook test_lights.yml -t -t now -f 10

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
