from procgame.dmd import GroupedLayer, ScriptedLayer, TextLayer
from procgame.game import AdvancedMode

class Timer(AdvancedMode):
    """timer for a timed mode"""

    def __init__(self, game, priority):
        super(Timer, self).__init__(game, priority)
        self.timer = 0

    def mode_stopped(self):
        self.stop_timer()

    def start_timer(self, time, delay_time=1):
        # Tell the mode how much time it gets, if it cares.
        self.timer_update(time)
        self.timer = time
        self.delay_time = delay_time
        self.delay(name='decrement timer', event_type=None, delay=self.delay_time, handler=self.decrement_timer)

    def stop_timer(self):
        self.timer = 0
        self.cancel_delayed('decrement timer')

    def reset_timer(self, time, delay_time=1):
        # assign a new deadline and align the handler on the delay boundary
        self.stop_timer()
        self.start_timer(time, delay_time)

    def add_time(self, time):
        self.timer += time

    def pause(self):
        self.cancel_delayed('decrement timer')

    def resume(self):
        if self.timer > 0:
            self.delay(name='decrement timer', event_type=None, delay=self.delay_time, handler=self.decrement_timer)

    def decrement_timer(self):
        if self.timer > 0:
            self.timer -= 1
            self.delay(name='decrement timer', event_type=None, delay=self.delay_time, handler=self.decrement_timer)
            self.timer_update(self.timer)
        else:
            self.expired()

    def expired(self):
        pass

    def timer_update(self, time):
        pass


class TimedMode(Timer):
    """Base class for timed modes, start with an intro showing instructions,
    then display the number of shots with a countdown timer"""

    def __init__(self, game, priority, mode_time, name, instructions, num_shots_required=0, animationLayer=None):
        super(TimedMode, self).__init__(game, priority)
        self.mode_time = mode_time
        self.name = name
        self.num_shots_required = num_shots_required

        font_large = self.game.fonts['large']
        font_small = self.game.fonts['tiny']
        font_num = self.game.fonts['large_num']

        intro_name_layer = TextLayer(128/2, 6, font_large, 'center').set_text(name)
        intro_instruct_layer = TextLayer(128/2, 25, font_small, 'center').set_text(instructions)
        intro_page_layer = GroupedLayer(128, 32, [intro_name_layer, intro_instruct_layer])
        script = [{'seconds':1, 'layer':intro_name_layer}, {'seconds':3, 'layer':intro_page_layer}]
        self.intro_layer = ScriptedLayer(width=128, height=32, script=script, hold=True, opaque=True)
        self.intro_duration = self.intro_layer.duration() - 1.0/30.0

        self.countdown_layer = TextLayer(127, 1, font_small, 'right')
        self.name_layer = TextLayer(1, 1, font_small, 'left').set_text(name)
        self.score_layer = TextLayer(128/2, 10, font_num, 'center')
        self.status_layer = TextLayer(128/2, 26, font_small, 'center')
        layers = [animationLayer] if animationLayer else []
        layers += [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer]
        self.mode_layer = GroupedLayer(128, 32, layers, opaque=True)

    def mode_started(self):
        self.intro_layer.reset()
        self.layer = self.intro_layer
        self.delay(name='intro_ended', event_type=None, delay=self.intro_duration, handler=self.intro_ended)
        self.num_shots = 0
        self.play_music()

    def mode_stopped(self):
        self.stop_timer()

    def intro_ended(self):
        self.layer = self.mode_layer
        if self.mode_time > 0:
            self.start_timer(self.mode_time)
        self.update_status()

    def play_music(self):
        self.game.sound.stop_music()
        self.game.sound.play_music('mode', loops=-1)

    def incr_num_shots(self):
        self.num_shots += 1
        self.update_status()

    def decr_num_shots(self):
        if self.num_shots > 0:
            self.num_shots -= 1
            self.update_status()

    def update_status(self):
        if self.num_shots > self.num_shots_required:
            # only Impersonator can get extra hits
            extra_shots = self.num_shots - self.num_shots_required
            status = 'Shots made: ' + str(extra_shots) + ' extra'
        else:
            status = 'Shots made: ' + str(self.num_shots) + '/' + str(self.num_shots_required)
        self.status_layer.set_text(status)

    def mode_tick(self):
        score = self.game.current_player().score
        text = self.game.format_points(score)
        self.score_layer.set_text(text)

    def timer_update(self, time):
        self.countdown_layer.set_text(str(time))

    def expired(self):
        success = self.num_shots >= self.num_shots_required
        self.exit_callback(success)
