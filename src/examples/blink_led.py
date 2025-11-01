# MicroPython Example - Blink LED
from machine import Pin
from time import sleep

# Setup LED on GPIO2 (built-in LED on ESP32)
led = Pin(2, Pin.OUT)

def blink(times=10, delay=0.5):
    """Blink the LED a specified number of times."""
    for i in range(times):
        led.on()
        sleep(delay)
        led.off()
        sleep(delay)
    print(f"Blinked {times} times!")

# Main loop
if __name__ == "__main__":
    print("Starting blink sequence...")
    blink()
    print("Done!")
