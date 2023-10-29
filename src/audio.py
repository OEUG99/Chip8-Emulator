import numpy as np
import pygame


class Audio:

    def __init__(self):
        pygame.mixer.init()

    def play(self, frequency, duration):
        # Generate the samples for the tone
        sample_rate = 44100

        samples = (np.sin(2 * np.pi * np.arange(sample_rate * duration) * frequency / sample_rate)).astype(
            np.float32).tobytes()

        # Create a new Sound object with these samples
        sound = pygame.mixer.Sound(buffer=samples)

        # Play it!
        sound.play()

    def stop(self):
        pygame.mixer.stop()
