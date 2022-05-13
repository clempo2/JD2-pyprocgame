import time
from procgame.dmd import Frame, PanningLayer, TextLayer

class FixedSizeTextLayer(TextLayer):
    """A TextLayer where the text and blank blinking frames are opaque over the whole width x height"""

    def __init__(self, x, y, font, justify="left", opaque=False, width=128, height=32, fill_color=None):
        super(FixedSizeTextLayer, self).__init__(x, y, font, justify, opaque, width, height, fill_color)
        self.blank_frame = Frame(width, height)

    def set_text(self, text, seconds=None, blink_frames=None):
        """Displays the given message for the given number of seconds."""
        self.started_at = None
        self.seconds = seconds
        self.blink_frames = blink_frames
        self.blink_frames_counter = self.blink_frames
        if text == None:
            self.frame = None
        else:
            (w, h) = self.font.size(text)
            if self.justify == 'right':
                (x, y) = (self.width - w, 0)
                (self.target_x_offset, self.target_y_offset) = (-self.width, 0)
            elif self.justify == 'center':
                (x, y) = ((self.width - w)/2, 0)
                (self.target_x_offset, self.target_y_offset) = (-self.width/2, 0)
            else: # left justified
                (x, y) = (0,0)
                (self.target_x_offset, self.target_y_offset) = (0, 0)

            self.set_target_position(self.x, self.y)
            self.frame = Frame(width=self.width, height=self.height)
            if self.fill_color != None:
                self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color)
            self.font.draw(self.frame, text, x, y)

        return self

    def next_frame(self):
        if self.started_at == None:
            self.started_at = time.time()
        if (self.seconds != None) and ((self.started_at + self.seconds) < time.time()):
            self.frame = None
        elif self.blink_frames > 0:
            if self.blink_frames_counter == 0:
                self.blink_frames_counter = self.blink_frames
                if self.frame == self.blank_frame:
                    self.frame = self.frame_old
                else:
                    self.frame_old = self.frame
                    self.frame = self.blank_frame
            else:
                self.blink_frames_counter -= 1
        return self.frame


class FastPanningLayer(PanningLayer):
    """Pans faster than the regular PanningLayer"""
    def next_frame(self):
        self.tick += 2
        return super(FastPanningLayer, self).next_frame()
