# Originally copied from PyProcGameHD-SkeletonGame
# Copyright (c) 2014-2015 Michael Ocean and Josh Kugler

import time
from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode, SwitchStop


class SlamTilted(Mode):
    """Display 'Slam Tilt' and wait a little while before resetting the game"""

    def __init__(self, game):
        super(SlamTilted, self).__init__(game, priority=99999)
        self.layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center').set_text('Slam Tilt')

    def mode_started(self):
        self.delay('reset_game', event_type=None, delay=5, handler=self.reset_game)

    def reset_game(self):
        self.game.reset()
        self.game.update_lamps()


class Tilted(Mode):
    """Display 'Tilt' and consume all switch events to block scoring"""

    def __init__(self, game):
        super(Tilted, self).__init__(game, priority=99999)
        text_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center').set_text('Tilt')
        self.layer = GroupedLayer(128, 32, [text_layer])
        always_seen_switches = self.game.switches.items_tagged('tilt_visible')
        always_seen_switches.extend(self.game.switches.items_tagged('trough'))
        for sw in [x for x in self.game.switches if x.name not in self.game.trough.position_switchnames and x not in always_seen_switches]:
            self.add_switch_handler(name=sw.name, event_type='active', delay=None, handler=self.ignore_switch)

    def mode_started(self):
        self.game.sound.play('tilt')

    def ignore_switch(self, sw):
        return SwitchStop

    def mode_stopped(self):
        self.game.base_play.tilt.tilt_reset()

    # Eject any balls that get stuck before returning to the trough.
    def sw_popperL_active(self, sw):
        return self.coil_switch_active(sw)

    def sw_popperR_active(self, sw):
        return self.coil_switch_active(sw)

    def sw_shooterL_active(self, sw):
        return self.coil_switch_active(sw)

    def sw_shooterR_active(self, sw):
        return self.coil_switch_active(sw)

    def coil_switch_active(self, sw):
        self.delay('pulse_coil', event_type=None, delay=0.3, handler=self.pulse_coil, param=sw)
        return SwitchStop

    def pulse_coil(self, sw):
        if sw.is_active():
            self.game.coils[sw.name].pulse(40)


class TiltMonitorMode(Mode):
    """Monitor tilt warnings and slam tilt"""

    def __init__(self, game, priority, tilt_sw=None, slam_tilt_sw=None):
        super(TiltMonitorMode, self).__init__(game, priority)
        self.tilt_sw = tilt_sw
        self.slam_tilt_sw = slam_tilt_sw

        if tilt_sw:
            self.add_switch_handler(name=tilt_sw, event_type='active', delay=None, handler=self.tilt_active)
        if slam_tilt_sw:
            self.add_switch_handler(name=slam_tilt_sw, event_type='active', delay=None, handler=self.slam_tilt_active)

        self.num_tilt_warnings = 2 # BasePlay overwrites this with the value of a settings
        self.tilt_bob_settle_time = 2.0
        self.tilted = False

    def tilt_reset(self):
        self.times_warned = 0
        self.tilted = False
        self.previous_warning_time = None

    def mode_started(self):
        self.tilt_reset()

    def tilt_active(self, sw):
        now = time.time()
        if (self.previous_warning_time is not None) and ((now - self.previous_warning_time) < self.tilt_bob_settle_time):
            # tilt bob still swinging from previous warning
            return
        else:
            self.previous_warning_time = now

        if self.times_warned == self.num_tilt_warnings:
            if not self.tilted:
                self.tilted = True
                self.game.tilted()
        else:
            self.times_warned += 1
            self.game.tilt_warning(self.times_warned)

    def slam_tilt_active(self, sw):
        self.game.slam_tilted()
        return True

    def tilt_delay(self, fn, secs_since_bob_tilt=2.0):
        """ calls the specified `fn` if it has been at least `secs_since_bob_tilt`
            (make sure the tilt isn't still swaying)
        """
        if self.game.switches[self.tilt_sw].time_since_change() < secs_since_bob_tilt:
            self.delay(name='tilt_bob_settle', event_type=None, delay=secs_since_bob_tilt, handler=self.tilt_delay, param=fn)
        else:
            return fn()
