#!/usr/bin/env python3

import argparse
import sys
import time

import pigpio


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description = __doc__, formatter_class = argparse.RawDescriptionHelpFormatter)

    p.add_argument("gpio", type = int, help = "GPIO Pin")
    return (p.parse_args())


# Try running with these args
#
# "Hello" 123 --enable
if __name__ == '__main__':
    args = cmdline_args()

    #PIN = args.gpio

    # Start the signal generation
    GPIO = pigpio.pi()
    GPIO.set_mode(args.gpio, pigpio.INPUT)

    # Pull down the GPIO-Pin and cleanup with stop()
    print(GPIO.read(args.gpio))
    GPIO.stop()

    print()
