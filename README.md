## Testing the Synch.Live players

The current branch contains the basic code and minimum Ansible config to
run various stress tests or sync tests on the players.

### Lights test

This test uses a snippet of code from tutorials-raspberrypi.com and
cycles through different colours and behaviours. The script is run
immediately as an ansible command, so it's likely it won't be run in
perfect sync. The choreography is done running after around a minute.

    ansible-playbook test_lights.yml -t  -f 10

### Sync test
#### Start

This test consists of chaotic blinks for 250 seconds which slowly align
themselves until they sync. Then they keep on blinking periodically for
another 100 seconds. If the clocks are the same, the test is a success
when all hats blink in sync at the end.

You should edit the variable `MINUTE` in `Run mock loop example` to
schedule a time to start the test. The script will be run with cron.

    ansible-playbook test_lights.yml -t schedule -f 10

#### Stop

To turn off all LEDs blinking and remove cronjob

    ansible-playbook test_lights.yml -t stop -f 10

Make sure you update the `MINUTE` variable to match the cronjob created
in the previous section.

