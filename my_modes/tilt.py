# Originally copied from PyProcGameHD-SkeletonGame
# Copyright (c) 2014-2015 Michael Ocean and Josh Kugler

import time
from procgame.game import Mode, SwitchStop

class Tilted(Mode):
    """ Consumes all switch events to block scoring """

    def __init__(self, game):
        super(Tilted, self).__init__(game, priority=99999)
        always_seen_switches = self.game.switches.items_tagged('tilt_visible')
        always_seen_switches.append(self.game.switches.items_tagged('trough'))
        for sw in [x for x in self.game.switches if x.name not in self.game.trough.position_switchnames and x.name not in always_seen_switches]:
            self.add_switch_handler(name=sw.name, event_type='active', delay=None, handler=self.ignore_switch)

    def ignore_switch(self, sw):
        return SwitchStop

    def mode_stopped(self):
        self.game.game_tilted = False
        self.game.base_play.tilt.tilt_reset()

    # Eject any balls that get stuck before returning to the trough.
    def sw_popperL_active_for_500ms(self, sw):
        self.game.coils.popperL.pulse(40)

    def sw_popperR_active_for_500ms(self, sw):
        self.game.coils.popperR.pulse(40)

    def sw_shooterL_active_for_500ms(self, sw):
        self.game.coils.shooterL.pulse(40)

    def sw_shooterR_active_for_500ms(self, sw):
        self.game.coils.shooterR.pulse(40)


class TiltMonitorMode(Mode):
    """Monitor tilt warnings and slam tilt"""

    def __init__(self, game, priority, tilt_sw=None, slam_tilt_sw=None):
        super(TiltMonitorMode, self).__init__(game, priority)
        self.tilt_sw = tilt_sw
        self.slam_tilt_sw = slam_tilt_sw
        self.tilted_mode = Tilted(game)

        if tilt_sw:
            self.add_switch_handler(name=tilt_sw, event_type='active', delay=None, handler=self.tilt_handler)
        if slam_tilt_sw:
            self.add_switch_handler(name=slam_tilt_sw, event_type='active', delay=None, handler=self.slam_tilt_handler)

        self.num_tilt_warnings = 2 # BasePlay overwrites this with the value of a settings
        self.tilt_bob_settle_time = 2.0
        self.tilted = False

    def tilt_reset(self):
        self.times_warned = 0
        self.tilted = False
        self.previous_warning_time = None

    def mode_started(self):
        self.tilt_reset()

    def mode_stopped(self):
        self.game.remove_modes([self.tilted_mode])

    def tilt_handler(self, sw):
        now = time.time()
        if (self.previous_warning_time is not None) and ((now - self.previous_warning_time) < self.tilt_bob_settle_time):
            # tilt bob still swinging from previous warning
            return
        else:
            self.previous_warning_time = now

        if self.times_warned == self.num_tilt_warnings:
            if not self.tilted:
                self.call_tilt_callback(self.game.tilted)
        else:
            self.times_warned += 1
            self.game.tilt_warning(self.times_warned)

    def slam_tilt_handler(self, sw):
        self.call_tilt_callback(self.game.slam_tilted)
        return True

    def tilt_delay(self, fn, secs_since_bob_tilt=2.0):
        """ calls the specified `fn` if it has been at least `secs_since_bob_tilt`
            (make sure the tilt isn't still swaying)
        """

        if self.game.switches[self.tilt_sw].time_since_change() < secs_since_bob_tilt:
            self.delay(name='tilt_bob_settle', event_type=None, delay=secs_since_bob_tilt, handler=self.tilt_delay, param=fn)
        else:
            return fn()

    def call_tilt_callback(self, callback):
        # Disable flippers so the ball will drain.
        self.game.enable_flippers(enable=False)

        # Make sure ball won't be saved when it drains.
        self.game.ball_save.disable()

        # Ensure all lamps are off.
        for lamp in self.game.lamps:
            lamp.disable()

        # Kick balls out of places it could be stuck.
        # TODO: ball search!!
        self.tilted = True

        self.game.modes.add(self.tilted_mode)
        #play sound
        #play video
        callback()
