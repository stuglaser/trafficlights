import sys
from contextlib import contextmanager
from termcolor import colored

fh = open('/proc/cpuinfo', 'r')
if len([x for x in fh.readlines() if x.find('BCM2708') != -1 or x.find('BCM2835') != -1 or x.find('BCM2709') != -1 or x.find('BCM2836') != -1]) > 0:
    import RPi.GPIO as GPIO


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
IS_FAKE = False

COLOR_BTN = 21
SOLID_SWT = 7 # blink when nothing is set
CYCLE_SWT = 22
DISCO_SWT = 19

lookup = {'RED1': RED1, 'YLW1': YLW1, 'GRN1': GRN1,
          'RED2': RED2, 'YLW2': YLW2, 'GRN2': GRN2}
rev_lookup = {v: k for k, v in lookup.iteritems()}


def setup_controls():
    if 'RPi.GPIO' not in sys.modules:
        raise Exception('Cannot use HW on non RPi')

    if not GPIO.getmode() or GPIO.getmode() != GPIO.BOARD:
        GPIO.setmode(GPIO.BOARD)

    GPIO.setup(COLOR_BTN, GPIO.IN)
    GPIO.setup(DISCO_SWT, GPIO.IN)
    GPIO.setup(CYCLE_SWT, GPIO.IN)
    GPIO.setup(SOLID_SWT, GPIO.IN)

def setup():
    if not IS_FAKE:
        GPIO.setmode(GPIO.BOARD)
        for led in ALL:
            GPIO.setup(led, GPIO.OUT)
            GPIO.output(led, OFF)


def cleanup():
    if 'RPi.GPIO' in sys.modules:
        GPIO.cleanup()


def input(button):
    return GPIO.input(button)

@contextmanager
def setup_manager(args):
    global IS_FAKE
    IS_FAKE=args.fake
    setup()
    if args.controls:
        setup_controls()

    try:
        yield
    finally:
        cleanup()


def only(*on):
    if not IS_FAKE:
        off = set(ALL) - set(on)
        for led in on:
            GPIO.output(led, ON)
        for led in off:
            GPIO.output(led, OFF)
    else:
        light_a = []
        light_b = []
        for led in on:
            light = rev_lookup[led]
            if light[-1] == "1":
                light_a.append(light[0:len(light) - 1])
            else:
                light_b.append(light[0:len(light) - 1])

        print " A   B "
        print "=== ==="
        if 'RED' in light_a and 'RED' in light_b:
            print "=%s= =%s=" % (colored('@', 'red'), colored('@', 'red'))
        elif 'RED' in light_a and 'RED' not in light_b:
            print "=%s= =@=" % (colored('@', 'red'))
        elif 'RED' not in light_a and 'RED' in light_b:
            print "=@= =%s=" % (colored('@', 'red'))
        elif 'RED' not in light_a and 'RED' not in light_b:
            print "=@= =@="
        if 'YLW' in light_a and 'YLW' in light_b:
            print "=%s= =%s=" % (colored('@', 'yellow'), colored('@', 'yellow'))
        elif 'YLW' in light_a and 'YLW' not in light_b:
            print "=%s= =@=" % (colored('@', 'yellow'))
        elif 'YLW' not in light_a and 'YLW' in light_b:
            print "=@= =%s=" % (colored('@', 'yellow'))
        elif 'YLW' not in light_a and 'YLW' not in light_b:
            print "=@= =@="
        if 'GRN' in light_a and 'GRN' in light_b:
            print "=%s= =%s=" % (colored('@', 'green'), colored('@', 'green'))
        elif 'GRN' in light_a and 'GRN' not in light_b:
            print "=%s= =@=" % (colored('@', 'green'))
        elif 'GRN' not in light_a and 'GRN' in light_b:
            print "=@= =%s=" % (colored('@', 'green'))
        elif 'GRN' not in light_a and 'GRN' not in light_b:
            print "=@= =@="
        print "=== ==="
