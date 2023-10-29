import pygame


class Controls:

    def __init__(self):
        self.KEYMAP = {
            pygame.K_1: 0x1,
            pygame.K_2: 0x2,
            pygame.K_3: 0x3,
            pygame.K_4: 0xC,
            pygame.K_q: 0x4,
            pygame.K_w: 0x5,
            pygame.K_e: 0x6,
            pygame.K_r: 0xD,
            pygame.K_a: 0x7,
            pygame.K_s: 0x8,
            pygame.K_d: 0x9,
            pygame.K_f: 0xE,
            pygame.K_z: 0xA,
            pygame.K_x: 0x0,
            pygame.K_c: 0xB,
            pygame.K_v: 0xF,
        }
        self.events = {}

        self.keysPressed = []

        self.onNextKeyPress = False

        self.add_event_listner(pygame.KEYDOWN, self.on_key_down)
        self.add_event_listner(pygame.KEYUP, self.on_key_up)
        self.add_event_listner(pygame.QUIT, pygame.quit)

    def handle_events(self):
        val = None
        for event in pygame.event.get():
            if event.type in self.events:
                val = self.events[event.type](event)  # Call the event callback.

        if val is not None:
            return val
        else:
            return None



    def add_event_listner(self, event_id, callback):
        self.events[event_id] = callback

    def remove_event_listner(self, event, callback):
        self.events[event] = None

    def on_key_down(self, event: pygame.KEYDOWN):
        key = self.KEYMAP[event.key]

        self.keysPressed = True


        if self.onNextKeyPress is True:
            self.onNextKeyPress = False
            return key

    def on_key_up(self, event: pygame.KEYUP):
        key = self.KEYMAP[event.key]
        self.keysPressed = False

    def is_key_pressed(self, key_code):
        return key_code in self.keysPressed

    def wait_for_key_press(self):
        print("waiting for key press")
        while True:
            event = pygame.event.wait(6000)

            # When an event occurs, try to map it from the pygame key to the Chip-8 key
            if event.type == pygame.KEYDOWN:
                key = self.KEYMAP.get(event.key)

                # If the pressed key is in the keymap, return the corresponding Chip-8 key
                if key is not None:
                    return key


