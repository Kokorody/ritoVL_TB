#riot kontolllllllllllllllllllllllll
#wantap

import cv2
import time
import numpy
import ctypes
import win32api
import threading
import bettercam
from multiprocessing import Pipe, Process
from ctypes import windll
import os
import json

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def bypass(pipe):
    keybd_event = windll.user32.keybd_event
    while True:
        try:
            key = pipe.recv()
            if key == b'\x01':
                keybd_event(0x4F, 0, 0, 0)  # O key
                keybd_event(0x4F, 0, 2, 0)  # O key
        except EOFError:
            break

def send_key_multiprocessing(pipe):
    pipe.send(b'\x01')

class Triggerbot:
    def __init__(self, pipe, keybind, toggle_rate_key, fov, shooting_rates, hsv_range, fps):
        user32 = windll.user32
        self.WIDTH, self.HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        self.size = fov
        self.Fov = (
            int(self.WIDTH / 2 - self.size),
            int(self.HEIGHT / 2 - self.size),
            int(self.WIDTH / 2 + self.size),
            int(self.HEIGHT / 2 + self.size),
        )
        self.camera = bettercam.create(output_idx=0, region=self.Fov)
        self.frame = None
        self.keybind = keybind
        self.toggle_rate_key = toggle_rate_key
        self.pipe = pipe
        self.cmin, self.cmax = hsv_range
        self.shooting_rates = shooting_rates
        self.current_rate_index = 0
        self.frame_duration = 1 / fps  # Convert FPS to frame duration in seconds
        self.last_toggle_time = 0

    def Capture(self):
        while True:
            self.frame = self.camera.grab()
            time.sleep(self.frame_duration)  # Sleep for the duration of one frame

    def Color(self):
        if self.frame is not None:
            hsv = cv2.cvtColor(self.frame, cv2.COLOR_RGB2HSV)
            mask = cv2.inRange(hsv, self.cmin, self.cmax)
            return numpy.any(mask)

    def toggle_shooting_rate(self):
        current_time = time.time()
        # Add a small cooldown to prevent rapid toggling
        if current_time - self.last_toggle_time > 0.5:
            self.current_rate_index = (self.current_rate_index + 1) % len(self.shooting_rates)
            print(f"Shooting rate changed to: {self.shooting_rates[self.current_rate_index]} ms")
            self.last_toggle_time = current_time

    def Main(self):
        while True:
            # Check for rate toggle key
            if win32api.GetAsyncKeyState(self.toggle_rate_key) < 0:
                self.toggle_shooting_rate()

            # Check for shooting
            if win32api.GetAsyncKeyState(self.keybind) < 0 and self.Color():
                send_key_multiprocessing(self.pipe)
                time.sleep(self.shooting_rates[self.current_rate_index] / 1000)  # Convert ms to seconds
            time.sleep(0.001)

def save_config(config):
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

if __name__ == "__main__":
    parent_conn, child_conn = Pipe()
    p = Process(target=bypass, args=(child_conn,))
    p.start()

    # Check for config file
    config = {}
    if os.path.exists('config.json'):
        cls()
        
        print("Config file found. Do you want to load (1) or update (2) the config?")
        choice = int(input("Choice: "))
        cls()
        if choice == 1:
            config = load_config()
            print("Config loaded:")
            print(json.dumps(config, indent=4))
        else:
            config['fov'] = float(input("Enter FOV size: "))
            cls()

            config['keybind'] = int(input("Enter keybind (hex): "), 16)
            cls()

            # Updated shooting rates configuration
            default_rates = [100, 300, 450]
            print(f"Default shooting rates will be: {default_rates} ms")
            config['shooting_rates'] = default_rates
            cls()

            config['toggle_rate_key'] = int(input("Enter toggle rate key (hex): "), 16)
            cls()

            config['fps'] = float(input("Enter desired FPS: "))
            cls()

            hsv_choice = int(input("Use default HSV range (1) or custom (2)? "))
            cls()

            if hsv_choice == 1:
                config['hsv_range'] = [(30, 125, 150), (30, 255, 255)]  
            else:
                config['hsv_range'] = [
                    [int(input("Enter lower Hue: ")), int(input("Enter lower Saturation: ")), int(input("Enter lower Value: "))],
                    [int(input("Enter upper Hue: ")), int(input("Enter upper Saturation: ")), int(input("Enter upper Value: "))]
                ]
            cls()

            save_config(config)
            print("Config updated:")
            print(json.dumps(config, indent=4))
    else:
        config['fov'] = float(input("Enter FOV size: "))
        cls()
        
        config['keybind'] = int(input("Enter keybind (hex): "), 16)
        cls()

        # Updated shooting rates configuration
        default_rates = [100, 300, 450]
        print(f"Default shooting rates will be: {default_rates} ms")
        config['shooting_rates'] = default_rates
        cls()

        config['toggle_rate_key'] = int(input("Enter toggle rate key (hex): "), 16)
        cls()
        
        config['fps'] = float(input("Enter desired FPS: "))
        cls()
        
        hsv_choice = int(input("Use default HSV range (1) or custom (2)? "))
        cls()
        
        if hsv_choice == 1:
            config['hsv_range'] = [(30, 125, 150), (30, 255, 255)] 
        else:
            config['hsv_range'] = [
                [int(input("Enter lower Hue: ")), int(input("Enter lower Saturation: ")), int(input("Enter lower Value: "))],
                [int(input("Enter upper Hue: ")), int(input("Enter upper Saturation: ")), int(input("Enter upper Value: "))]
            ]
        cls()
        
        save_config(config)
        print("Config created:")
        print(json.dumps(config, indent=4))

    triggerbot = Triggerbot(
        parent_conn, 
        config['keybind'], 
        config['toggle_rate_key'], 
        config['fov'], 
        config['shooting_rates'], 
        config['hsv_range'], 
        config['fps']
    )
    threading.Thread(target=triggerbot.Capture).start()
    threading.Thread(target=triggerbot.Main).start()
    p.join()