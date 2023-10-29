import pygame


class Renderer:

    def __init__(self, scale) -> None:
        self.scale = scale
        self.cols = 64
        self.rows = 32
        self.screen = pygame.display.set_mode((self.cols * self.scale, self.rows * self.scale))

        # create a list called self.display with the appropriate range
        self.display = ([0] * self.cols * self.rows)

    def setPixel(self, x, y):

        # Deal with wrapping as per technical reference.
        x = x % self.cols
        y = y % self.rows

        print(x, y)

        # Calculate the index in the display array.
        index = x + (y * self.cols)

        # check if index is out of range
        if index > len(self.display):
            print("index out of range")

        # Set the pixel to 1 if it is already 1, then return 1.
        if self.display[index] == 1:
            self.display[index] = 0
            return 1
        else:
            self.display[index] = 1
            return 0


    def clear(self):
        self.screen.fill((0, 0, 0))
        self.display = [0] * self.cols * self.rows
        pygame.display.flip()

    def render(self):

        # Iterate through the display array.
        for i in range(self.cols * self.rows):

            # Calculate the x and y coordinates.
            x = (i % self.cols) * self.scale
            y = (i // self.cols) * self.scale

            # If the value at index i in the display array is 1, then draw a square.
            if self.display[i]:
                rect = pygame.draw.rect(self.screen, (255, 255, 255), (x, y, self.scale, self.scale))
                pygame.display.update(rect)


    def testRender(self):
        self.setPixel(0, 0)
        self.setPixel(5, 2)
