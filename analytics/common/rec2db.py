#!/usr/bin/python3

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from configuration import env
import requests
import os
import datetime

office=list(map(float,env["OFFICE"].split(",")))
sthost=env["STHOST"]

class Handler(FileSystemEventHandler):
    def __init__(self, sensor):
        super(Handler,self).__init__()
        self._sensor = sensor
        self._last_file = None
        self._requests=requests.Session()

    def on_created(self, event):
        print("on_created: "+event.src_path, flush=True)
        if event.is_directory: return
        if event.src_path.endswith(".png"): return
        if self._last_file:
            if self._last_file==event.src_path: return
            try:
                self._process_file(self._last_file)
            except Exception as e:
                print("Exception: "+str(e), flush=True)
        self._last_file = event.src_path

    def _process_file(self, filename):

        video_base = 1008235783042570420
        # Real base 1638326863379333614
        # Filename example: '/tmp/rec/5ocgc30BswPB8WWEg2ml/2021/11/30/1638314060090100076_239493104.mp4'
        file_offset=int(os.path.splitext(os.path.basename(filename))[0].split('_')[-1])
        custom_time = str(int((file_offset + video_base)/1000000))
        print("filename is {}, time is {}".format(filename, custom_time))
        with open(filename,"rb") as fd:
            r=self._requests.post(sthost,data={
                "time": custom_time,
                "orig_time":str(int(int(os.path.basename(filename).split('_')[-2])/1000000)),
                "office":str(office[0])+","+str(office[1]),
                "sensor":self._sensor,
            },files={
                "file": fd,
            },verify=False)
        os.remove(filename)

class Rec2DB(object):
    def __init__(self, sensor):
        super(Rec2DB,self).__init__()
        self._sensor=sensor
        self._observer=Observer()

    def start(self):
        folder="/tmp/rec/"+self._sensor
        os.makedirs(folder, exist_ok=True)

        handler=Handler(self._sensor)
        self._observer.schedule(handler, folder, recursive=True)
        self._observer.start()

    def stop(self):
        self._observer.stop()
        self._observer.join()
