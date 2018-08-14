#!/usr/bin/env python
import argparse
import random
from chan import Chan, chanselect, Timeout, ChanClosed
from nanomsg import Socket, PAIR, PUB
from SimpleXMLRPCServer import SimpleXMLRPCServer
import time
import threading

import lights


MASTER_PORT = 55755
SERVER_PORT = 8085

DEFAULT_PERIOD = 12
DEFAULT_YELLOW = 2.5

CMD_PING = 'PING'
CMD_LIGHTS = 'LIGHTS'


class DiscoTimer(object):
    def __init__(self, base=500, jitter=1000):
        self.trip = False
        self._stop = threading.Event()
        self.chan = Chan()
        self._thread = threading.Thread(name='LightTimer', target=self.run)
        self._thread.daemon = True
        self._thread.start()
        self.base = base
        self.jitter = jitter
        random.seed()

    def run(self):
        while not self._stop.is_set():
            random_lights = []
            for l in lights.ALL:
                maybe = random.randint(0, 1)
                if maybe == 1:
                    random_lights.append(l)
            self.chan.put(random_lights)
            time.sleep((self.base + random.randint(0, self.jitter)) / 1000)

    def stop(self):
        self._stop.set()
        
class SolidTimer(object):
    def __init__(self, color, blink=False, period=0.5):
        self.blink = blink
        self.period = period
        self.color = color.split('-')[0]
        self.chan = Chan()
        self._stop = threading.Event()
        self._thread = threading.Thread(name='LightTimer', target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def run(self):
        STATE = []
        if self.color == 'red':
            STATE = [lights.RED1, lights.RED2]
        elif self.color == 'yellow':
            STATE = [lights.YLW1, lights.YLW2]
        elif self.color == 'green':
            STATE = [lights.GRN1, lights.GRN2]

        on = True
        while not self._stop.is_set():
            if on:
                if self.blink:
                    self.chan.put([STATE[0]])
                    on = False
                    time.sleep(self.period)
                else:
                    self.chan.put(STATE)
                    time.sleep(5)
            else:
                self.chan.put([STATE[1]])
                on = True
                time.sleep(self.period)


        self.chan.close()

    def stop(self):
        self._stop.set()
            
class LightTimer(object):
    def __init__(self, period=DEFAULT_PERIOD, yellow=DEFAULT_YELLOW):
        self.period = period
        self.yellow = yellow
        self.trip = False
        self._stop = threading.Event()
        self.chan = Chan()
        self._thread = threading.Thread(name='LightTimer', target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def run(self):
        STATES = [
            [lights.RED1, lights.GRN2],
            [lights.RED1, lights.YLW2],
            [lights.GRN1, lights.RED2],
            [lights.YLW1, lights.RED2],
        ]
        state_i = len(STATES) - 1
        t_last = 0
        while not self._stop.is_set():
            t_yellow = min(0.25 * self.period, DEFAULT_YELLOW)
            t_green = self.period - t_yellow
            dur = t_green if state_i % 2 == 0 else t_yellow

            now = time.time()
            if now > t_last + dur or self.trip:
                t_last = now
                state_i = (state_i + 1) % len(STATES)
                self.chan.put(STATES[state_i])
                self.trip = False
            time.sleep(0.1)
        self.chan.close()

    def stop(self):
        self._stop.set()


class Server(object):
    def __init__(self):
        self.chan = Chan()
        self._server = SimpleXMLRPCServer(
            ('0.0.0.0', SERVER_PORT),
            logRequests=False,
            allow_none=True)
        self._server.register_introspection_functions()
        self._server.register_instance(self)
        self._thread = threading.Thread(name='Server', target=self._server.serve_forever)
        self._thread.daemon = True
        self._thread.start()

    def status(self):
        st = {'server': 'ok'}
        try:
            resp_chan = Chan(1)
            self.chan.put(('status', resp_chan), timeout=0.5)
            resp = resp_chan.get(timeout=0.5)
            st.update(resp)
        except Timeout:
            st['loop'] = 'Error: Did not hear from main thread in time'
        return st

    def set_period(self, period):
        self.chan.put(('set_period', period), timeout=2.0)
        return True


    def trip(self):
        self.chan.put(('trip',), timeout=2.0)
        return True


def master_loop(mode):
    sock_slave = Socket(PAIR)
    sock_slave.bind('tcp://*:%s' % MASTER_PORT)
    sock_slave.recv_timeout = 250
    #sock_slave.send_buffer_size = 1000
    sock_slave.send_timeout = 200
    seq = 0

    timer = None
    if mode == 'cycle':
        timer = LightTimer()
    elif mode == 'red' or mode == 'green' or mode == 'yellow':
        timer = SolidTimer(mode)
    elif mode == 'red-blink' or mode == 'green-blink' or mode == 'yellow-blink':
        timer = SolidTimer(mode, True)
    elif mode == 'disco':
        timer = DiscoTimer()

    server = Server()

    while True:
        ch, value = chanselect([timer.chan, server.chan], [])
        #print 'AFTER chanselect', ch is timer.chan, time.time()
        if ch is timer.chan:
            lights.only(*value)
            #print "LIGHTS", value
            try:
                seq += 1
                sock_slave.send('%i %s %s' % (
                    seq,
                    CMD_LIGHTS,
                    ' '.join(lights.rev_lookup[led_pin] for led_pin in value)))
            except Exception as ex:
                #print ex
                pass
        elif ch is server.chan:
            if value[0] == 'status':
                slave = None
                try:
                    seq += 1
                    sock_slave.send('%i PING' % seq)
                    while True:
                        slave_msg = sock_slave.recv().split()
                        if int(slave_msg[0]) == seq:
                            slave = 'ok'
                            break
                        elif int(slave_msg[0]) > seq:
                            raise Exception('Skipped ping message')
                except Exception as ex:
                    slave = repr(ex)
                value[1].put({'loop': 'ok', 'slave': slave})
            elif value[0] == 'set_period':
                timer.period = value[1]
            elif value[0] == 'trip':
                timer.trip = True
            else:
                print "UNKNOWN COMMAND:", value
    time.sleep(2)


def slave_loop(master):
    sock_master = Socket(PAIR)
    sock_master.connect('tcp://%s:%s' % (master, MASTER_PORT))

    while True:
        msg = sock_master.recv()
        #print 'HEARD', msg
        bits = msg.split()
        msgid = bits[0]
        cmd = bits[1]

        if cmd == CMD_PING:
            sock_master.send('%s PONG' % msgid)
        elif cmd == CMD_LIGHTS:
            which_pins = [lights.lookup[lgt] for lgt in bits[2:]]
            lights.only(*which_pins)
        else:
            print 'Unhandleable message: %r' % msg


def main():
    parser = argparse.ArgumentParser(description='Traffic light control system')
    parser.add_argument('--master', '-m', help='Address of master')
    parser.add_argument('--fake', '-f', help='Fake Mode', default=False, action='store_true')
    parser.add_argument('--mode', help='Force a different mode', default='cycle')
    args = parser.parse_args()

    if args.mode != 'cycle' and args.mode != 'red' and args.mode != 'yellow' and args.mode != 'green' and args.mode != 'disco' and args.mode != 'red-blink' and args.mode != 'yellow-blink' and args.mode != 'green-blink':
        raise Exception('Bad mode')

    with lights.setup_manager(args.fake):
        if args.master is None:
            print 'I am the master'
            master_loop(args.mode)
        else:
            print 'Obeying:', args.master
            slave_loop(args.master)


if __name__ == '__main__':
    main()
