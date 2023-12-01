#!/usr/bin/env python3

import argparse
import sys
import time

import pigpio


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description = __doc__, formatter_class = argparse.RawDescriptionHelpFormatter)

    p.add_argument("gpio", type = int, help = "GPIO Pin")
    p.add_argument("state", type = int, help = "State (0 or 1")
    return (p.parse_args())


# Try running with these args
#
# "Hello" 123 --enable
if __name__ == '__main__':
    args = cmdline_args()

    #PIN = args.gpio

    # Start the signal generation
    GPIO = pigpio.pi()
    GPIO.set_mode(args.gpio, pigpio.OUTPUT)

    # try:
    # Keep the script running until Ctrl + C are pressed
    #    while True:
    #        GPIO.write(PIN, 1)
    #        time.sleep(1)
    #        GPIO.write(PIN, 0)
    #        time.sleep(1)
    #except KeyboardInterrupt:
    #    pass

    # Pull down the GPIO-Pin and cleanup with stop()
    GPIO.write(args.gpio, args.state)
    GPIO.stop()

    print()
