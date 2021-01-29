import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI

# initialise the LEDs
LED_COUNT = 20
SPI_PORT   = 0
SPI_DEVICE = 0
leds = Adafruit_WS2801.WS2801Pixels(PIXEL_COUNT,
  spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

# turn them all on with max brightness
for k in range(LED_COUNT):
  leds.set_pixel(k,
    Adafruit_WS2801.RGB_to_color(255, 255, 255))
leds.show()

