import time
import datetime


while True:
  with open("battery.log", "a") as log:
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp:
      t = int(temp.read())
      t = t/1000
      now = datetime.datetime.now()
      print(now.strftime('%Y-%m-%d %H:%M:%S'), t, file=log)

  time.sleep(10)
