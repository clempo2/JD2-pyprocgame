from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode, SwitchStop
from procgame.service import ServiceModeSkeleton

class Deadworld(Mode):
    """Controls the Deadworld planet"""

    def __init__(self, game, priority, deadworld_mod_installed):
        super(Deadworld, self).__init__(game, priority)
        self.deadworld_mod_installed = deadworld_mod_installed
        self.fast_eject = self.game.user_settings['Machine']['Deadworld fast eject']
        self.lock_enabled = False
        self.num_balls_locked = 0
        self.num_balls_to_eject = 0
        self.ball_eject_in_progress = False
        self.crane_delay_active = False
        self.setting_up_eject = False

    def mode_stopped(self):
        self.stop()

    def stop(self):
        self.game.coils.globeMotor.disable()

    def enable_lock(self):
        self.lock_enabled = True
        self.game.coils.globeMotor.pulse(0)
        # Make sure globe disable rule is off.
        switch_num = self.game.switches['globePosition2'].number
        self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, False)

    def disable_lock(self):
        self.lock_enabled = False

    def crane_activate(self):
        if self.ball_eject_in_progress:
            self.game.coils.crane.pulse(0)

    def globe_start(self):
        self.game.coils.globeMotor.pulse(0)

    def crane_start(self):
        self.game.coils.crane.pulse(0)

    def crane_release(self):
        if self.fast_eject:
            self.delay(name='globe_restart_delay', event_type=None, delay=1, handler=self.globe_start)

        self.game.coils.craneMagnet.disable()
        self.game.coils.crane.disable()
        self.delay(name='crane_release_check', event_type=None, delay=1, handler=self.crane_release_check)

    def crane_release_check(self):
        if self.num_balls_to_eject > 0:
            if self.fast_eject:
                # Fast mode just keeps going until finished
                self.delay(name='crane_restart_delay', event_type=None, delay=0.9, handler=self.crane_start)
            else:
                # restart when not in fast mode
                self.perform_ball_eject()
        else:
            self.game.coils.crane.disable()
            if self.num_balls_locked > 0:
                self.game.coils.globeMotor.pulse(0)
            else:
                self.game.coils.globeMotor.disable()

            self.ball_eject_in_progress = False

    def end_crane_delay(self):
        self.crane_delay_active = False

    def get_num_balls_locked(self):
        return self.num_balls_locked - self.num_balls_to_eject

    def sw_globePosition2_active(self, sw):
        if self.fast_eject:
            if self.setting_up_eject:
                self.setting_up_eject = False
                self.delay(name='crane_restart_delay', event_type=None, delay=0.9, handler=self.crane_start)
                switch_num = self.game.switches['globePosition2'].number
                self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)
        else:
            self.crane_activate()

    def sw_leftRampToLock_active(self, sw):
        self.num_balls_locked += 1
        self.game.trough.num_balls_locked += 1

    def perform_ball_search(self):
        self.perform_ball_eject()

    def eject_balls(self, num):
        self.num_balls_to_eject += num

        # Tell the trough the balls aren't locked anymore so it can count properly.
        self.game.trough.num_balls_locked -= num
        # Error check.
        if self.game.trough.num_balls_locked < 0:
            self.game.trough.num_balls_locked = 0

        self.perform_ball_eject()

    def perform_ball_eject(self):
        if self.ball_eject_in_progress:
            return
        
        self.ball_eject_in_progress = True

        # Make sure globe is turning
        self.game.coils.globeMotor.pulse(0)

        if self.fast_eject:
            # If globe not in position to start (globePosition2), it needs to get there first.
            if self.game.switches['globePosition2'].is_inactive():
                self.setting_up_eject = True
                switch_num = self.game.switches['globePosition2'].number
                self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, False)
            else:
                self.delay(name='crane_restart_delay', event_type=None, delay=1.9, handler=self.crane_start)
                switch_num = self.game.switches['globePosition2'].number
                self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)

            self.delay(name='globe_restart_delay', event_type=None, delay=1, handler=self.globe_start)
        else:
            switch_num = self.game.switches['globePosition2'].number
            self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)

    def sw_craneRelease_active(self, sw):
        if not self.crane_delay_active:
            self.crane_delay_active = True
            self.delay(name='crane_delay', event_type=None, delay=2, handler=self.end_crane_delay)
            self.num_balls_to_eject -= 1
            self.num_balls_locked -= 1
            # error check
            if self.num_balls_locked < 0:
                self.num_balls_locked = 0

    def sw_magnetOverRing_open(self, sw):
        if self.ball_eject_in_progress:
            self.game.coils.craneMagnet.pulse(0)
            self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)


class DeadworldTest(ServiceModeSkeleton):
    """Test the Deadworld planet in service mode"""

    def __init__(self, game, priority, font):
        super(DeadworldTest, self).__init__(game, priority, font)
        self.name = 'DeadWorld Test'
        
        self.title_layer = TextLayer(1, 1, font, 'left')
        self.title_layer.set_text(self.name)

        self.globe_layer = TextLayer(1, 9, font, 'left')
        self.arm_layer = TextLayer(1, 17, font, 'left')
        self.magnet_layer = TextLayer(1, 25, font, 'left')
        self.layer = GroupedLayer(128, 32, [self.title_layer, self.globe_layer, self.arm_layer, self.magnet_layer])

    def reset(self, lamp_style):
        self.globe_state = False
        self.crane_state = False
        self.magnet_state = False
        self.game.coils.globeMotor.disable()
        self.game.coils.crane.disable()
        self.game.coils.craneMagnet.disable()
        self.game.drive_lamp('startButton', lamp_style)
        self.game.drive_lamp('superGame', lamp_style)
        self.game.drive_lamp('buyIn', lamp_style)

    def mode_started(self):
        super(DeadworldTest, self).mode_started()
        self.reset('slow')
        self.set_texts()

    def mode_stopped(self):
        self.reset('off')

    def drive_coil(self, coil_name, enabled):
        if enabled:
            self.game.coils[coil_name].pulse(0)
        else:
            self.game.coils[coil_name].disable()
        
    def sw_exit_active(self, sw):
        self.game.modes.remove(self)
        self.game.update_lamps()
        return SwitchStop

    def sw_startButton_active(self, sw):
        self.globe_state = not self.globe_state
        self.drive_coil('globeMotor', self.globe_state)
        self.set_texts()
        return SwitchStop

    def sw_superGame_active(self, sw):
        self.crane_state = not self.crane_state
        self.drive_coil('crane', self.crane_state)
        self.set_texts()
        return SwitchStop

    def sw_buyIn_active(self, sw):
        self.magnet_state = True
        self.drive_coil('craneMagnet', self.magnet_state)
        self.set_texts()
        return SwitchStop

    def sw_buyIn_inactive(self, sw):
        self.magnet_state = False
        self.drive_coil('craneMagnet', self.magnet_state)
        self.set_texts()
        return SwitchStop

    def sw_enter_active(self, sw):
        return SwitchStop

    def sw_up_active(self, sw):
        return SwitchStop

    def sw_down_active(self, sw):
        return SwitchStop

    def sw_magnetOverRing_active(self, sw):
        self.arm_layer.set_text('SUPERGAME BTN: Crane:  Ring')

    def sw_magnetOverRing_inactive(self, sw):
        self.set_texts()

    def sw_globePosition1_active(self, sw):
        self.globe_layer.set_text('START BTN:      Globe:  P1')

    def sw_globePosition1_inactive(self, sw):
        self.set_texts()

    def sw_globePosition2_active(self, sw):
        self.globe_layer.set_text('START BTN:      Globe:  P2')

    def sw_globePosition2_inactive(self, sw):
        self.set_texts()

    def set_texts(self):
        state = 'On' if self.crane_state else 'Off'
        self.arm_layer.set_text('SUPERGAME BTN: Crane:   ' + state)
        
        state = 'On' if self.globe_state else 'Off'
        self.globe_layer.set_text('START BTN:      Globe:  ' + state)

        state = 'On' if self.magnet_state else 'Off'
        self.magnet_layer.set_text('BUY-IN BTN:     Magnet: ' + state)
