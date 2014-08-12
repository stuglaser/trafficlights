from contextlib import contextmanager
from RPi import GPIO
import time


T_CYCLE = 5
T_YELLOW = 0.2 * T_CYCLE

ON = False
OFF = True

RED1 = 8
YLW1 = 10
GRN1 = 12
RED2 = 11
YLW2 = 13
GRN2 = 15
ALL = [RED1, YLW1, GRN1, RED2, YLW2, GRN2]

lookup = {'RED1': RED1, 'YLW1': YLW1, 'GRN1': GRN1,
          'RED2': RED2, 'YLW2': YLW2, 'GRN2': GRN2}
rev_lookup = {v: k for k, v in lookup.iteritems()}


def setup():
    GPIO.setmode(GPIO.BOARD)
    for led in ALL:
        GPIO.setup(led, GPIO.OUT)
        GPIO.output(led, OFF)


def cleanup():
    GPIO.cleanup()


@contextmanager
def setup_manager():
    setup()
    try:
        yield
    finally:
        cleanup()


def only(*on):
    off = set(ALL) - set(on)
    for led in on:
        GPIO.output(led, ON)
    for led in off:
        GPIO.output(led, OFF)
