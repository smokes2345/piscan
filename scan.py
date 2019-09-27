#!/usr/bin/env python3
from gpiozero import OutputDevice
from time import sleep
from picamera import PiCamera
import atexit
from flask import Flask, send_file, render_template, redirect, url_for, flash
import os
from os.path import sep
from multiprocessing import Process
from zipfile import ZipFile
from tempfile import mkstemp
from glob import iglob

Seq = list([None] * 4)
Seq[0] = [0,1,0,0]
Seq[1] = [0,1,0,1]
Seq[2] = [0,0,0,1]
Seq[3] = [1,0,0,1]
#Seq[4] = [1,0,0,0]
#Seq[5] = [1,0,1,0]
#Seq[6] = [0,0,1,0]
#Seq[7] = [0,1,1,0]

Seq[0] = [0,0,0,1]
Seq[1] = [0,0,1,1]
Seq[2] = [0,0,1,0]
Seq[3] = [0,1,1,0]
#Seq[4] = [0,1,0,0]
#Seq[5] = [1,1,0,0]
#Seq[6] = [1,0,0,0]
#Seq[7] = [1,0,0,1]

Seq[0] = [0,0,0,1]
Seq[1] = [0,0,1,0]
Seq[2] = [0,1,0,0]
Seq[3] = [1,0,0,0]

app_name = "Scanner"
server = Flask(app_name)
server.secret_key = b'I\xfe\xc63\xa3\xbc\x10)\xe3;\x913\xe3\x87\x88)1\x81\x16\xcdtC\xe6\xed'

pins = [25,8,7,1]

def _scan_proc():
    camera = PiCamera()
    camera.start_preview()
    #motor = Stepper([25,8,7,1])
    def _snap(step):
        snap(camera, step, dir=sep.join([app_name, 'static']))
    motor.start(callback=_snap, callback_freq=4)
    camera.stop_preview()
scan_proc = Process(target=_scan_proc)

def _get_stills():
    return iglob(sep.join([app_name, 'static', '*.jpg']))

@server.route("/")
def index():
    links = server.url_map.iter_rules()
    return render_template('index.html.j2', links=links)

@server.route("/scan/start")
def start_scan():
    for still in _get_stills():
        os.unlink(still)
    scan_proc.start()
    flash("Scan started")
    return redirect(url_for('index'))

@server.route("/scan/stop")
def stop_scan():
    motor.stop()
    scan_proc.join()
    flash("Scan stopped")
    return redirect(url_for('index'))

@server.route("/bundle")
def bundle():
    picfile = mkstemp()
    print(picfile)
    piczip = ZipFile(picfile[1], 'w')
    file_list = _get_stills()
    for pic in file_list:
        print("Adding {} to archive".format(pic))
        piczip.write(pic)
    return send_file(piczip.filename, attachment_filename='scan_stills.zip', as_attachment=True)

@server.route("/shutdown")
def shutdown():
    os.system("sudo shutdown now")
    return "Shutdown in progress, please wait a minute before pulling power"

class Stepper(object):

    def __init__(self, pins: list):
        self.pins = pins
        self._pins = [OutputDevice(p) for p in pins]
        self._next_step = 0
        self.running = False
        self.steps = 0

    def step(self, reverse=False, callback=None, callback_freq=4):
        print("Executing step {}".format(self._next_step))
        for i,p in enumerate(Seq[self._next_step]):
            if p:
                self._pins[i].on()
            else:
                self._pins[i].off()
        #if callable(callback) and (self._next_step % callback_freq) == 0:
        #    callback(self.steps)
        self._next_step = self._next_step + 1
        if reverse:
            self._next_step = self._next_step - 1
            if self._next_step < 0:
                self._next_step = len(Seq) - 1
        if self._next_step >= len(Seq): 
            self._next_step = 0
        sleep(0.001)
        self.steps = self.steps + 1
        #[ p.off() for p in self._pins ]

    def stop(self):
        self.running = False
        for p in self._pins:
            p.off()

    def start(self, steps=30, reverse=False, callback=None, callback_freq=1, callback_count=16):
        self.running = True
        while self.running:
            #self.step(reverse, callback=callback, callback_freq=callback_freq)
            if callable(callback) and (self._next_step % callback_freq) == 0:
                callback(self.steps)
            self.step(reverse)

motor = Stepper(pins)

def snap(camera, *args, **kwargs):
    print("Capturing...")
    if 'dir' in kwargs:
        if not os.path.exists(kwargs['dir']):
            os.mkdir(kwargs['dir'])
        capture_file = sep.join([kwargs['dir'], str(args[0]) + '.jpg'])
    else:
        capture_file = str(args[0]) + '.jpg'
    camera.capture(capture_file)
    print("Captured to {}".format(str(args[0])))

if __name__ == "__main__":
#    motor = Stepper([25,8,7,1])
#    motor.start(callback=snap, callback_freq=4)
    server.run(host='0.0.0.0')
                

