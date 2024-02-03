"""
Originally taken from https://github.com/Sakartu/TM74HC595/blob/master/TM74HC595.py

"""
import array

import uasyncio
from machine import Pin

# fmt: off
CHARS = {
    "0": 0xC0, "1": 0xF9, "2": 0xA4, "3": 0xB0, "4": 0x99,
    "5": 0x92, "6": 0x82, "7": 0xF8, "8": 0x80, "9": 0x90,
    "A": 0x88, "B": 0x80, "b": 0x83, "c": 0xA7, "C": 0xC6,
    "d": 0xA1, "D": 0xC0, "E": 0x86, "F": 0x8E, "G": 0xC2,
    "H": 0x89, "i": 0xFB, "I": 0xF9, "j": 0xF3, "J": 0xF1,
    "L": 0xC3, "n": 0xAB, "o": 0xA3, "O": 0xC0, "P": 0x8C,
    "q": 0x98, "r": 0xCE, "R": 0x88, "S": 0x92, "t": 0x87,
    "u": 0xE3, "U": 0xC1, "v": 0xE3, "V": 0xC1, "Y": 0x91,
    "‾": 0xFE, "-": 0xBF, "_": 0xF7, " ": 0xFF, "z": 0x9C,  # "degree" sign
}
# fmt: on


class Display:
    def __init__(self, sclk: int, rclk: int, dio: int, n_segments: int):
        self.sclk = Pin(sclk, Pin.OUT)
        self.rclk = Pin(rclk, Pin.OUT)
        self.dio = Pin(dio, Pin.OUT)
        self.n_segments = n_segments

    def _send_byte(self, byte: int) -> None:
        for bit in map(int, "{0:08b}".format(byte)):
            self.dio.value(bit)
            # Cycle the clock as required for the TM74HC595 controller chip
            self.sclk.value(0)
            self.sclk.value(1)

    def _set_port(self, h: int, port: int) -> None:
        port = 1 << (self.n_segments - 1 - port)
        self._send_byte(h)
        self._send_byte(port)
        self.rclk.value(0)
        self.rclk.value(1)

    async def show(self, text: str, n_redraw: int = 100, clear: bool = True, start_at: int = 0):
        """
        Show a sequence of characters on the 8-segment show.

        Parameters
        ----------
        text
            The sequence of str-type characters to show.
        n_redraw: int >= 1
            The number of times this method should n_redraw the text
        clear
            Whether this method should clear the show after all redraws are
            done
        start_at
            Where to start displaying text

        Notes
        -----
        Because the TM74HC595 controller can only control a single
        display at a time, it sets each display very quickly, one after the
        other, so that the human eye does not see it flickering. The number of
        redraws it should do can be specified by the user, thus definig how
        long the sequence should be displayed. The user can also choose to clear
        the display after the redraws or not and where to start displaying the
        given text.
        Be advised: not all characters are available for 8-segment displays!
        See TM74HC595.CHARS.keys() for a list of valid characters.
        The dot character can be used in the sequence as well.

        Examples
        --------
        >>> from TM74HC595 import Display
        >>> d = Display(21, 22, 23, 8)
        >>> d.show('-1.234567', 1000)

        """
        to_display = array.array("B")
        for _ in range(start_at):
            to_display.append(CHARS[" "])

        for i, c in enumerate(text):
            if c == ".":
                if i:
                    to_display[-1] &= 0b01111111  # Activate the '.'
            else:
                to_display.append(CHARS[c])

        if len(to_display) > self.n_segments:
            raise ValueError(
                "Not enough diplay segments"
                f"{self.n_segments} to display text of length {len(to_display)}"
            )
        for _ in range(n_redraw):
            for i, b in enumerate(to_display):
                self._set_port(b, i)
                await uasyncio.sleep_ms(0)

        if clear:
            self.clear()

    def clear(self):
        """Clear display."""
        for i in range(self.n_segments):
            self._set_port(0xFF, i)

    def test(self):
        """
        A method to test whether everything is working correctly
        """
        import time

        for i in range(self.n_segments):  # test each port
            self._set_port(CHARS["8"], 1 << i)
            time.sleep(0.5)

        # all displays at once, low-level
        self._set_port(CHARS["8"], 2**self.n_segments - 1)
        time.sleep(1)
        self.clear()
        time.sleep(0.2)

        # all displays at once, high-level
        self.show("8" * self.n_segments, 500)  # all 8's

        # left half, right half
        half = self.n_segments // 2
        self.show("8" * half, 500, start_at=0)  # left half
        self.show("8" * half, 500, start_at=half)  # right half

        # counter, speed test
        if self.n_segments == 4:
            for i in range(-999, 1000):
                self.show("{:-4d}".format(i), 1, False)
        else:
            for i in range(-999, 1000):
                self.show("{:-4d}{:-4d}".format(i, i), 1, False)

        self.clear()
        self.show("dOnE", 500)
        self.clear()
