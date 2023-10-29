import os

import pygame
from pygame import QUIT, KEYDOWN, KEYUP
from pygame.time import Clock
from controls import Controls
from renderer import Renderer
from audio import Audio
from cpu import CPU
from datetime import datetime as Date, time, datetime


class Chip8:

    def __init__(self) -> None:
        pygame.init()
        pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])
        pygame.display.set_caption("Chip8 Emulator")
        self.renderer = Renderer(10)
        self.clock = Clock()
        self.fps = 301
        self.controls = Controls()
        self.audio = Audio()
        self.CPU = CPU(self.renderer, self.controls, self.audio)
        self.CPU.load_spriate_into_memory()
        self.CPU.readRom("roms/blitz")
        self.last_time = 0

        # create loop to run the program

    def run(self):
        while True:
            self.step()

    def getCurrentTime(self):
        return self.clock.get_time()


    def step(self):
        now = self.clock.get_time()
        elapsed = now - self.last_time
        self.clock.tick(self.fps)


        self.CPU.cycle()
        self.last_time = now
        self.controls.handle_events()
        self.renderer.render()




    def emulate_cycle(self):
        pass




