# Originally copied from pyprocgame
# Copyright (c) 2009-2011 Adam Preble and Gerry Stellenberg

from procgame.game import AdvancedMode, Mode, SwitchStop
from procgame.dmd import Frame, FrameLayer, FrameQueueLayer, GroupedLayer, MarkupFrameGenerator, ScriptedLayer, font_named
from procgame.highscore import CategoryLogic, EntrySequenceManager

class JDEntrySequenceManager(EntrySequenceManager):

    def __init__(self, game, priority, categories):
        super(JDEntrySequenceManager, self).__init__(game, priority)
        self.logic = CategoryLogic(game=game, categories=categories)

    def create_highscore_entry_mode(self, left_text, right_text, entered_handler):
        return JDInitialEntryMode(game=self.game, priority=self.priority+1, left_text=left_text, right_text=right_text, entered_handler=entered_handler)

    def evt_initial_entry(self, prompt):
        self.game.sound.play_voice('high score')
        self.banner_mode = Mode(game=self, priority=8)
        markup = MarkupFrameGenerator()
        text = '\n#GREAT JOB#\n[%s]' % (prompt.left.upper()) # we know that the left is the player name
        frame = markup.frame_for_markup(markup=text, y_offset=0)
        self.banner_mode.layer = ScriptedLayer(width=128, height=32, script=[{'seconds':3.0, 'layer':FrameLayer(frame=frame)}])
        self.banner_mode.layer.on_complete = self.banner_complete
        self.game.modes.add(self.banner_mode)
        return -1 # delay event until banner is complete

    def banner_complete(self):
        self.game.sound.play_music('ball_launch', loops=-1)
        self.game.modes.remove([self.banner_mode])
        self.force_event_next()


class JDInitialEntryMode(Mode):
    """Mode that prompts the player for their initials.

    *left_text* and *right_text* are strings or arrays to be displayed at the
    left and right corners of the display.  If they are arrays they will be
    rotated.

    :attr:`entered_handler` is called once the initials have been confirmed.

    This mode does not remove itself; this should be done in *entered_handler*."""

    entered_handler = None
    """Method taking two parameters: `mode` and `initials`."""

    char_back = '<'
    char_done = '='

    max_length = 12

    init_font = None
    font = None
    letters_font = None

    def __init__(self, game, priority, left_text, right_text, entered_handler):
        super(JDInitialEntryMode, self).__init__(game, priority)

        self.entered_handler = entered_handler

        self.init_font = font_named('Font09Bx7.dmd')
        self.font = font_named('Font07x5.dmd')
        self.letters_font = font_named('Font07x5.dmd')

        self.layer = GroupedLayer(128, 32)
        self.layer.opaque = True
        self.layer.layers = []

        if type(right_text) != list:
            right_text = [right_text]
        if type(left_text) != list:
            left_text = [left_text]

        # Truncate 'SuperGame High Score 1' because it is too long, it overlaps the left text
        # The long high score category name fits nicely in attract mode though
        right_text = [text[10:] if text.startswith('SuperGame ') else text for text in right_text]
        seconds_per_text = 1.5

        script = []
        for text in left_text:
            frame = Frame(width=128, height=8)
            self.font.draw(frame, text, 0, 0)
            script.append({'seconds':seconds_per_text, 'layer':FrameLayer(frame=frame)})
        topthird_left_layer = ScriptedLayer(width=128, height=8, script=script)
        topthird_left_layer.composite_op = 'blacksrc'
        self.layer.layers += [topthird_left_layer]

        script = []
        for text in right_text:
            frame = Frame(width=128, height=8)
            self.font.draw(frame, text, 128-(self.font.size(text)[0]), 0)
            script.append({'seconds':seconds_per_text, 'layer':FrameLayer(frame=frame)})
        topthird_right_layer = ScriptedLayer(width=128, height=8, script=script)
        topthird_right_layer.composite_op = 'blacksrc'
        self.layer.layers += [topthird_right_layer]

        self.inits_frame = Frame(width=128, height=10)
        inits_layer = FrameLayer(opaque=False, frame=self.inits_frame)
        inits_layer.set_target_position(0, 10)
        self.layer.layers += [inits_layer]

        self.lowerhalf_layer = FrameQueueLayer(opaque=False, hold=True)
        self.lowerhalf_layer.set_target_position(0, 23)
        self.layer.layers += [self.lowerhalf_layer]

        self.letters = []
        for idx in range(26):
            self.letters += [chr(ord('A')+idx)]
        self.letters += [' ', '.', self.char_back, self.char_done]
        self.char_done_index = self.letters.index(self.char_done)
        self.current_letter_index = 0
        self.initials = ''
        self.cursor_visible = True
        self.draw_initials()
        self.animate_to_index(0)

    def mode_started(self):
        self.delay(name='blink_cursor', event_type=None, delay=0.25, handler=self.blink_cursor)

    def mode_stopped(self):
        # we must explicitly cancel this delayed handler since the mode is removed within pyprocgame
        self.cancel_delayed('blink cursor')

    def animate_to_index(self, new_index, inc=0):
        letter_spread = 10
        letter_width = 5
        if inc < 0:
            rng = range(inc * letter_spread, 1)
        elif inc > 0:
            rng = range(inc * letter_spread)[::-1]
        else:
            rng = [0]
        for x in rng:
            frame = Frame(width=128, height=9)
            frame.fill_rect(61,0,8,9,(255,255,255,255))
            frame.fill_rect(62,1,6,7,(0,0,0,255))
            for offset in range(-7, 8):
                index = new_index - offset
                #print 'Index %d  len=%d' % (index, len(self.letters))
                if index < 0:
                    index = len(self.letters) + index
                elif index >= len(self.letters):
                    index = index - len(self.letters)
                self.letters_font.draw(frame, self.letters[index], 128/2 - offset * letter_spread - letter_width/2 + x, 1)
            # inverse the colors of the current index letter
            #for x2 in range(61, 69):
            #    for y2 in range(0, 8):
            #        frame.set_dot(x2, y2, 15 - frame.get_dot(x2, y2))
            self.lowerhalf_layer.frames += [frame]
        self.current_letter_index = new_index

        # Prune down the frames list so we don't get too far behind while animating
        x = 0
        while len(self.lowerhalf_layer.frames) > 15 and x < (len(self.lowerhalf_layer.frames)-1):
            del self.lowerhalf_layer.frames[x]
            x += 2

    def draw_initials(self):
        # Draw the middle panel, with the selected initials in order
        self.inits_frame.clear()
        init_spread = 8
        x_offset = -3 + self.inits_frame.width/2 - len(self.initials) * init_spread / 2
        if len(self.initials) == self.max_length:
            # recenter since we do not display the blinking cursor
            x_offset += init_spread / 2
        elif self.cursor_visible:
            self.inits_frame.fill_rect(len(self.initials) * init_spread + x_offset, 9, 8, 1, (255,255,255,255))
        for x in range(len(self.initials)):
            self.init_font.draw(self.inits_frame, self.initials[x], x * init_spread + x_offset, 0)

    def blink_cursor(self):
        self.cursor_visible = not self.cursor_visible
        self.draw_initials()
        self.delay(name='blink_cursor', event_type=None, delay=0.25, handler=self.blink_cursor)

    def letter_increment(self, inc):
        new_index = (self.current_letter_index + inc)
        if new_index < 0:
            new_index = len(self.letters) + new_index
        elif new_index >= len(self.letters):
            new_index = new_index - len(self.letters)
        self.animate_to_index(new_index, inc)

    def letter_accept(self):
        letter = self.letters[self.current_letter_index]
        if letter == self.char_back:
            if len(self.initials) > 0:
                self.initials = self.initials[:-1]
        elif letter == self.char_done:
            self.initials = self.initials[:-1] # Strip off the done character
            if self.entered_handler != None:
                self.entered_handler(self, self.initials)
            else:
                self.game.logger.warning('InitialEntryMode finished but no entered_handler to notify!')
            self.cancel_delayed('blink_cursor')
        elif len(self.initials) < self.max_length:
            self.initials += letter
            if len(self.initials) == self.max_length:
                self.animate_to_index(self.char_done_index)
        self.draw_initials()

    def sw_flipperLwL_active(self, sw):
        self.start_periodic_movement(-1)

    def sw_flipperLwL_inactive(self, sw):
        self.stop_periodic_movement()

    def sw_flipperLwR_active(self, sw):
        self.start_periodic_movement(1)

    def sw_flipperLwR_inactive(self, sw):
        self.stop_periodic_movement()

    def start_periodic_movement(self, delta):
        self.stop_periodic_movement()
        self.periodic_movement(delta)

    def stop_periodic_movement(self):
        self.cancel_delayed('periodic_movement')

    def periodic_movement(self, delta):
        self.letter_increment(delta)
        self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_movement, param=delta)

    def sw_startButton_active(self, sw):
        self.letter_accept()
        return SwitchStop
