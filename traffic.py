#!/usr/bin/env python
import argparse
from chan import Chan, chanselect
from nanomsg import Socket, PAIR, PUB
import time
import threading

import lights


PORT = 55755

DEFAULT_PERIOD = 4
DEFAULT_YELLOW = 1


class LightTimer(object):
    def __init__(self, period=DEFAULT_PERIOD, yellow=DEFAULT_YELLOW):
        self.period = period
        self.yellow = yellow
        self._stop = threading.Event()
        self.chan = Chan()
        self._thread = threading.Thread(name='LightTimer', target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def run(self):
        t_green = self.period - self.yellow
        states = [
            (t_green, [lights.RED1, lights.GRN2]),
            (self.yellow, [lights.RED1, lights.YLW2]),
            (t_green, [lights.GRN1, lights.RED2]),
            (self.yellow, [lights.YLW1, lights.RED2]),
        ]
        state_i = len(states) - 1
        t_last = 0
        while not self._stop.is_set():
            now = time.time()
            if now > t_last + states[state_i][0]:
                t_last = now
                state_i = (state_i + 1) % len(states)
                self.chan.put(states[state_i][1])
            time.sleep(0.1)
        self.chan.close()

    def stop(self):
        self._stop.set()


def master_loop():
    sock_slave = Socket(PAIR)
    sock_slave.bind('tcp://*:%s' % PORT)

    timer = LightTimer()

    while True:
        ch, value = chanselect([timer.chan], [])
        if ch is timer.chan:
            lights.only(*value)
    time.sleep(2)


def slave_loop(master):
    sock_master = Socket(PAIR)
    sock_master.connect('tcp://%s:%s' % (master, PORT))


def main():
    parser = argparse.ArgumentParser(description='Traffic light control system')
    parser.add_argument('--master', '-m', help='Address of master')
    args = parser.parse_args()

    with lights.setup_manager():
        if args.master is None:
            print 'I am the master'
            master_loop()
        else:
            print 'Obeying:', args.master
            slave_loop(args.master)


if __name__ == '__main__':
    main()
