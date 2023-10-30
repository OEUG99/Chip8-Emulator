import os

import pygame
from pygame import QUIT, KEYDOWN, KEYUP
from pygame.time import Clock
from controls import Controls
from renderer import Renderer
from audio import Audio
from cpu import CPU
from config import FPS
from datetime import datetime as Date, time, datetime


class Chip8:

    def __init__(self) -> None:
        pygame.init()
        pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])
        pygame.display.set_caption("Chip8 Emulator")
        self.renderer = Renderer(10)
        self.clock = Clock()
        self.audio = Audio()
        self.controls = Controls()
        self.CPU = CPU(self.renderer, self.controls, self.audio)

        self.CPU.load_sprites_into_memory()
        self.CPU.readRom("roms/audio_test")

    def run(self):
        while True:
            self.step()

    def getCurrentTime(self):
        return self.clock.get_time()

    def step(self):
        self.controls.handle_events()
        self.renderer.render()
        self.CPU.cycle()
        self.clock.tick(FPS)
