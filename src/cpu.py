import numpy as np
import random
from functools import partial

SHOULD_WRAP = False

class CPU:

    def __init__(self, renderer, controls, audio) -> None:
        self.renderer = renderer
        self.controls = controls
        self.audio = audio

        self.memory = [0] * 4096  # 4096 bytes of memory.
        self.v = np.array([0] * 16, np.uint8)  # 16 8-bit registers named V0, V1, ..., VF.
        self.index_register = np.array([0], np.uint16)  # 16-bit register called I (used for storing addresses).

        self.delay_timer = 0
        self.sound_timer = 0

        self.program_counter = 0x200  # Program counter starts at 0x200 (512).

        self.stack = []

        self.paused = False
        self.speed = 10

    def load_spriate_into_memory(self):
        sprites = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]

        for i, sprite in enumerate(sprites):
            self.memory[i] = sprite

    def __load_bytes_into_memory(self, bytes_):
        for i, byte in enumerate(bytes_):
            self.memory[0x200 + i] = byte

    def readRom(self, path):
        with open(path, 'rb') as f:
            bytes_ = f.read()
            self.__load_bytes_into_memory(bytes_)

    def cycle(self):
        for i in range(self.speed):
            if not self.paused:
                opcode = (self.memory[self.program_counter] << 8) | self.memory[self.program_counter + 1]
                print(hex(opcode))
                self.execute_instruction(opcode)

        if not self.paused:
            self.update_timers()

        self.play_sound()
        self.renderer.render()

    def execute_instruction(self, instruction):
        # Move the program counter to prep for the net instruction.
        # Each instruction is 2 bytes long, hence we incremenet by 2.
        self.program_counter += 2

        # 0x0F00 is a bitmask that specifically targets the second byte from the left in a two-byte value like an
        # opcode.
        # 0001 0010 0011 0100  (0x1234)
        # 0000 1111 0000 0000  (0x0F00)
        # -------------------
        # 0000 0010 0000 0000  (& operation result) (0x3000)
        #
        # This bitmask is used to extract the high byte from the instruction.
        # We can extract the low byte by using the 0x00F0 bitmask.
        #
        # A high byte is the leftmost byte in a two-byte value like an opcode.
        # a low byte is the rightmost byte in a two-byte value like an opcode.

        x = (instruction & 0x0F00) >> 8  # A 4-bit value, the lower 4 bits (nibble) of the high byte of the instruction

        y = (instruction & 0x00F0) >> 4  # A 4-bit value, the upper 4 bits (nibble) of the low byte of the instruction

        nnn = instruction & 0x0FFF  # A 12-bit value, the lowest 12 bits of the instruction

        kk = instruction & 0x00FF  # An 8-bit value, the lowest 8 bits of the instruction

        nibble_differentiator = instruction & 0x000F  # A 4-bit value, the lowest 4 bits of the instruction used for
        # differentiating between instructions of same type.

        # We will use another bitmask to grab the opcode from the instruction.
        # 1111 0000 0000 0000  (0xF000)
        opcode = instruction & 0xF000

        # Opcodes can be found here: http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#3.0
        # Super-chip opcodes here: http://johnearnest.github.io/Octo/docs/SuperChip.html
        if opcode == 0x0000:
            if instruction == 0x00E0:
                # Clear the display.
                self.renderer.clear()
            elif instruction == 0x00EE:
                # Return from a subroutine bt popping last element in stack and store it in program counter.
                self.program_counter = self.stack.pop()
        elif opcode == 0x1000:
            # jump to address nnn
            self.program_counter = nnn
        elif opcode == 0x2000:
            # Call subroutine at nnn.
            self.stack.append(self.program_counter)
            self.program_counter = nnn
        elif opcode == 0x3000:
            # Skip the next instruction if Vx == kk.
            if self.v[x] == kk:
                self.program_counter += 2
        elif opcode == 0x4000:
            # Skip the next instruction if Vx != kk.
            if self.v[x] != kk:
                self.program_counter += 2
        elif opcode == 0x5000:
            # Skip the next instruction if Vx == Vy.
            if self.v[x] == self.v[y]:
                self.program_counter += 2
        elif opcode == 0x6000:
            # Set Vx = kk.
            self.v[x] = kk
        elif opcode == 0x7000:
            # Set Vx = Vx + kk.
            self.v[x] += kk
        elif opcode == 0x8000:
            # for opcodes that start with 0x8, we need to check the last nibble to determine the instruction.

            if nibble_differentiator == 0x0000:
                # Set Vx = Vy.
                self.v[x] = self.v[y]
            elif nibble_differentiator == 0x0001:
                # Set Vx = Vx OR Vy.
                self.v[x] |= self.v[y]
            elif nibble_differentiator == 0x0002:
                # Set Vx = Vx AND Vy.
                self.v[x] = self.v[x] & self.v[y]
            elif nibble_differentiator == 0x0003:
                # Set Vx = Vx XOR Vy.
                self.v[x] ^= self.v[y]
            elif nibble_differentiator == 0x0004:
                # Set Vx = Vx + Vy, set VF = carry.
                #
                # The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,)
                # VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.
                temp = self.v[x] + self.v[y]

                # Check if the result is greater than 8 bits.
                # Toggle collision flag if it is.
                if temp > 255:
                    self.v[0xF] = 1
                else:
                    self.v[0xF] = 0

                # Only keep the lowest 8 bits of the result using a bitmask.
                self.v[x] = temp & 0x00FF
            elif nibble_differentiator == 0x0005:
                # Set Vx = Vx - Vy, set VF = NOT borrow.
                #
                # If Vx > Vy, then VF is set to 1, otherwise 0.
                # Then Vy is subtracted from Vx, and the results stored in Vx.
                if self.v[x] > self.v[y]:
                    self.v[0xF] = 1
                else:
                    self.v[0xF] = 0

                self.v[x] -= self.v[y]

            elif nibble_differentiator == 0x0006:
                # set Vx = Vx SHR 1.
                # If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.
                #
                # grab the least significant bit of Vx
                lsb = self.v[x] & 0x1

                # if lsb is 1, set VF to 1, otherwise 0
                if lsb == 1:
                    self.v[0xF] = 1
                else:
                    self.v[0xF] = 0

                # divide Vx by 2
                self.v[x] >>= 1
            elif nibble_differentiator == 0x0007:
                # Set Vx = Vy - Vx, set VF = NOT borrow.
                #
                # If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy,
                # and the results stored in Vx.

                if self.v[y] > self.v[x]:
                    self.v[0xF] = 1
                else:
                    self.v[0xF] = 0

                self.v[x] = self.v[y] - self.v[x]
            elif nibble_differentiator == 0x000E:
                # Set Vx = Vx SHL 1.
                #
                # If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0.
                # Then Vx is multiplied by 2.
                msb = self.v[x] & 0x80

                if msb == 1:
                    self.v[0xF] = 1
                else:
                    self.v[0xF] = 0

                # multiply Vx by 2
                self.v[x] <<= 1
        elif opcode == 0x9000:
            # Skip next instruction if Vx != Vy.
            #
            # The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2.
            if self.v[x] != self.v[y]:
                self.program_counter += 2
        elif opcode == 0xA000:
            # Set I = nnn.
            self.index_register = nnn
        elif opcode == 0xB000:
            # Jump to location nnn + V0.
            #
            # The program counter is set to nnn plus the value of V0.
            self.program_counter = nnn + self.v[0]
        elif opcode == 0xC000:
            # Set Vx = random byte AND kk.
            #
            # The interpreter generates a random number from 0 to 255, which is then ANDed with the value kk.
            # The results are stored in Vx.

            ran = random.randint(0, 255)
            self.v[x] = ran & kk
        elif opcode == 0xD000:
            # Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
            #
            # The interpreter reads n bytes from memory, starting at the address stored in I. These bytes are then
            # displayed as sprites on screen at coordinates (Vx, Vy). Sprites are XORed onto the existing screen. If
            # the sprite is positioned so part of it is outside the coordinates of the display, it wraps around to
            # the opposite side of the screen. See instruction 8xy3 for more information on XOR, and section 2.4,
            # Display, for more information on the Chip-8 screen and sprites.
            #
            #
            # In chip-8, a sprite is represented as a sequence of bytes.
            # where each bit in a byte represents a pixel.
            # Chip-8 sprites may be up to 15 bytes, for a possible sprite size of 8x15.
            width = 8
            height = nnn & 0xF
            assert height <= 15, "Sprite height is too large"

            # reset the collision flag
            self.v[0xF] = 0



            # unpack the sprite from memory aka unwrap it
            for row in range(height):

                sprite = self.memory[self.index_register + row]


                # displaying the sprite, we don't need to XOR since renderer.draw_pixel() does that for us.
                # We also don't have to worry about wrapping around the screen since the renderer does that for us too.

                for col in range(width):
                    # finding most significant bit of sprite
                    msb = sprite & 0x80

                    # if the pixel is on in the sprite:
                    if msb > 0:
                        # if the pixel is on in the screen, it will unset thus returning 1 so we know to toggle
                        # collision flag.

                        if SHOULD_WRAP:
                            if self.renderer.setPixel(self.v[x] + col, self.v[y] + row, True) == 1:
                                self.v[0xF] = 1
                        else:
                            if self.renderer.setPixel(self.v[x] + col, self.v[y] + row, False) == 1:
                                self.v[0xF] = 1



                    # shift the sprite left by 1
                    sprite <<= 1

                    # sleep for 5 seconds

                    # NOTE: there is an alternative way to do this, and that is to convert the sprite into a 2d array
                    # and then iterate through that array and draw the pixels. I chose to do it this way because it
                    # is more efficient.
        elif opcode == 0xE000:
            # opcodes that end in 0xE we to check the nibble to determine which instruction to execute.

            if nibble_differentiator == 0x000E:
                # Skip next instruction if key with the value of Vx is pressed.
                #
                # Checks the keyboard, and if the key corresponding to the value of Vx is currently in the down
                # position, PC is increased by 2.
                if self.controls.is_key_pressed(self.v[x]):
                    self.program_counter += 2
            elif nibble_differentiator == 0x0001:
                # Skip next instruction if key with the value of Vx is not pressed.
                #
                # Checks the keyboard, and if the key corresponding to the value of Vx is currently in the up
                # position, PC is increased by 2.
                if not self.controls.is_key_pressed(self.v[x]):
                    self.program_counter += 2
        elif opcode == 0xF000:
            # opcodes that end in 0xF we to check the nibble to determine which instruction to execute.

            if nibble_differentiator == 0x0007:
                # Set Vx = delay timer value.
                #
                # The value of DT is placed into Vx.
                self.v[x] = self.delay_timer
            elif nibble_differentiator == 0x000A:  # TODO test this instruction to make sure it works.
                # Wait for a key press, store the value of the key in Vx.
                #
                # All execution stops until a key is pressed, then the value of that key is stored in Vx.
                self.paused = True

                # defines the function for self.controls.onNextKeyPress to call inside of self.controls.on_key_down
                key = self.controls.wait_for_key_press()

                self.v[x] = key
                self.paused = False
                print(f"key pressed: {self.v[x]}")


            elif nibble_differentiator == 0x0008:
                # Set sound timer = Vx.
                #
                # ST is set equal to the value of Vx.
                self.sound_timer = self.v[x]
            elif nibble_differentiator == 0x000E:
                # Set I = I + Vx.
                #
                # The values of I and Vx are added, and the results are stored in I.
                self.index_register += self.v[x]
            elif nibble_differentiator == 0x0009:
                # Set I = location of sprite for digit Vx.
                #
                # The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx.
                self.index_register = self.v[x] * 5  # each sprite is 5 bytes long.
            elif nibble_differentiator == 0x0003:
                # Store BCD representation of Vx in memory locations I, I+1, and I+2.
                #
                # The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in
                # I, the tens digit at location I+1, and the ones digit at location I+2.
                self.memory[self.index_register] = self.v[x] // 100
                self.memory[self.index_register + 1] = (self.v[x] // 10) % 10
                self.memory[self.index_register + 2] = (self.v[x] % 100) % 10
            elif nibble_differentiator == 0x0005:
                # We need to check the last 2 nibbles to determine which instruction to execute for f-opcodes ending
                # in 5
                if (instruction & 0x00FF) == 0x0015:
                    # Set delay timer = Vx.
                    #
                    # DT is set equal to the value of Vx.
                    self.delay_timer = self.v[x]
                elif (instruction & 0x00FF) == 0x0055:
                    # Store registers V0 through Vx in memory starting at location I.
                    #
                    # The interpreter copies the values of registers V0 through Vx into memory, starting at the address
                    # in I.
                    for i in range(x):
                        self.memory[self.index_register + i] = self.v[i]
                elif (instruction & 0x00FF) == 0x0065:
                    # Read registers V0 through Vx from memory starting at location I.
                    #
                    # The interpreter reads values from memory starting at location I into registers V0 through Vx.
                    for i in range(x):
                        self.v[i] = self.memory[self.index_register + i]
        else:
            raise Exception(f'Unknown opcode: {instruction}')

        print("made it to the end of the instruction switch statement")

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1

        if self.sound_timer > 0:
            if self.sound_timer == 1:
                self.sound_timer -= 1

    def play_sound(self):
        # As long as sound timer is greater than zero a sound will be playing.
        if self.sound_timer > 0:
            self.audio.play(440, 0.1)
        else:
            self.audio.stop()
