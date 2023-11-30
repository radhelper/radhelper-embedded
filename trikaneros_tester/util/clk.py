#!/usr/bin/env python3

import argparse
import sys
import time

import pigpio


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description = __doc__, formatter_class = argparse.RawDescriptionHelpFormatter)

    p.add_argument("gpio", type = int, help = "GPIO Pin")
    p.add_argument("freq", type = int, help = "Clock Frequency")

    return (p.parse_args())


# Try running with these args
#
# "Hello" 123 --enable
if __name__ == '__main__':
    args = cmdline_args()

    CLK_PIN = args.gpio

    # Start the signal generation
    GPIO = pigpio.pi()
    GPIO.hardware_clock(CLK_PIN, args.freq)

    try:
        # Keep the script running until Ctrl + C are pressed
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # Pull down the GPIO-Pin and cleanup with stop()
    GPIO.write(CLK_PIN, 0)
    GPIO.stop()

    print()
