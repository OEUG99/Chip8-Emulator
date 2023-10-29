import pygame


class Renderer:

    def __init__(self, scale) -> None:
        self.scale = scale
        self.cols = 64
        self.rows = 32
        self.screen = pygame.display.set_mode((self.cols * self.scale, self.rows * self.scale))

        # create a list called self.display with the appropriate range
        self.display = ([0] * self.cols * self.rows)

    def setPixel(self, x, y, wrap=False):

        if wrap is True:
            # wrap around the screen if the coordinates are greater than the screen size or less than 0
            x = x % self.cols
            if x < 0:
                x = self.cols + x

            y = y % self.rows
            if y < 0:
                y = self.rows + y


        # Calculate the index in the display array.
        index = x + (y * self.cols)

        # check if index is out of range
        if index > len(self.display):
            return 0

        # XOR value into the display
        self.display[index] ^= 1

        # return 1 if collision else 0
        return not self.display[index]


    def clear(self):
        self.display = [0] * self.cols * self.rows

    def render(self):

        self.screen.fill((0, 0, 0))

        # Iterate through the display array.
        for i in range(self.cols * self.rows):

            # Calculate the x and y coordinates.
            x = (i % self.cols) * self.scale
            y = (i // self.cols) * self.scale

            # If the value at index i in the display array is 1, then draw a square.
            if self.display[i]:
                rect = pygame.draw.rect(self.screen, (255, 255, 255), (x, y, self.scale, self.scale))

        pygame.display.flip()


    def testRender(self):
        self.setPixel(0, 0)
        self.setPixel(0, -31)
