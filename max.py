#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import logging
import subprocess
import atexit
import signal
import sys

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(14, GPIO.OUT)
pwm = GPIO.PWM(14, 100)

# Logging configuration
# Set up logging to syslog
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("\nPress Ctrl+C to quit \n")

# Function to clean up GPIO and turn off the fan
def cleanup(signum=None, frame=None):
    try:
        pwm.ChangeDutyCycle(0)  # Set fan speed to 0
        time.sleep(1.0)  # Wait for the fan to stop
        pwm.stop()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, GPIO.LOW)
        GPIO.cleanup()
        logging.info("Program terminated -- Cleaning up GPIO")
        logger.info("Fan turned off. Exiting program.")
    except Exception as e:
        logger.info(f"An error occurred during cleanup: {str(e)}")
    sys.exit(0)

# Register the cleanup function to be called on exit, SIGINT, and SIGTERM
atexit.register(cleanup)
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

try:
    # Run the fan at maximum speed (100%)
    logger.info("FAN IS RUNNING AT 100% speed")
    pwm.start(100)

    while True:
        # Get CPU temperature
        temp = subprocess.getoutput("vcgencmd measure_temp|sed 's/[^0-9.]//g'")

        # Log temperature
        log_message = f"Temperature: {float(temp)}°C"
        logger.info(log_message)
        sys.stdout.write(log_message + '\n')
        sys.stdout.flush()

        time.sleep(1.0)

except KeyboardInterrupt:
    cleanup()  # Clean up GPIO on keyboard interrupt

    # Log and logger.info exit message
    logging.info("Ctrl + C pressed -- Ending program")
    logger.info("Ctrl + C pressed -- Ending program")
except Exception as e:
    logger.info(f"An error occurred: {str(e)}")
    cleanup()  # Clean up GPIO on error
