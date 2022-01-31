from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode, SwitchStop
from procgame.service import ServiceModeSkeleton

class Deadworld(Mode):
    """Controls the Deadworld planet"""

    def __init__(self, game, priority):
        super(Deadworld, self).__init__(game, priority)
        self.num_balls_locked = 0
        self.num_balls_to_eject = 0
        self.setting_up_eject = False
        self.ball_eject_in_progress = False
        self.crane_delay_active = False

    def mode_stopped(self):
        self.stop_spinning()
        self.cancel_delayed(['globe_restart', 'crane_release_check', 'crane_restart', 'crane_delay']) # in case of tilt

    def start_spinning(self):
        self.game.coils.globeMotor.pulse(0)

    def stop_spinning(self):
        self.game.coils.globeMotor.disable()

    def get_num_balls_locked(self):
        return self.num_balls_locked - self.num_balls_to_eject

    def install_rule(self, auto_disable):
        # when auto_disable is True, the globe will stop spinning when it reaches its start position (globePosition2)
        # when auto_disable is False, the globe will keep spinning
        switch_num = self.game.switches.globePosition2.number
        self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, auto_disable)

    def enable_lock(self):
        # start and keep spinning
        self.install_rule(auto_disable=False)
        self.start_spinning()

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
        
        # this flag tells the crane and crane magnet to activate at the proper time
        self.ball_eject_in_progress = True

        # Make sure globe is turning
        self.start_spinning()
        if self.game.switches.globePosition2.is_inactive():
            # we must get the globe in the start position (globePosition2) first
            self.setting_up_eject = True
            self.install_rule(auto_disable=False)
        else:
            self.delay(name='crane_restart', event_type=None, delay=1.9, handler=self.start_crane)
            self.install_rule(auto_disable=True)

        # TODO: this method already started the globe spinning, do we expect to stop spinning within 1sec and require a restart?
        self.delay(name='globe_restart', event_type=None, delay=1, handler=self.start_spinning)

    def start_crane(self):
        # start the crane moving
        self.game.coils.crane.pulse(0)

    def sw_globePosition2_active(self, sw):
        if self.setting_up_eject:
            self.setting_up_eject = False
            self.delay(name='crane_restart', event_type=None, delay=0.9, handler=self.start_crane)
            self.install_rule(auto_disable=True)

    def sw_craneRelease_active(self, sw):
        # this switch detects a ball was indeed ejected
        # We can now update the ball counts with confidence
        # After a successful ball release, we ignore the switch for the next 2 seconds.
        if not self.crane_delay_active:
            self.crane_delay_active = True
            self.delay(name='crane_delay', event_type=None, delay=2, handler=self.end_crane_delay)
            self.num_balls_to_eject -= 1
            self.num_balls_locked -= 1
            # error check
            if self.num_balls_locked < 0:
                self.num_balls_locked = 0

    def end_crane_delay(self):
        # make the craneRelease switch sensitive again
        self.crane_delay_active = False

    def sw_magnetOverRing_open(self, sw):
        if self.ball_eject_in_progress:
            # this turns the crane magnet on for 2 seconds
            self.game.coils.craneMagnet.pulse(0)
            self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)

    def crane_release(self):
        # this is called 2sec after the magnet grabbed the ball
        # it is now time to drop the ball to release it
        
        self.delay(name='globe_restart', event_type=None, delay=1, handler=self.start_spinning)

        # drop the ball and stop the crane movement
        self.game.coils.craneMagnet.disable()
        self.game.coils.crane.disable()
        self.delay(name='crane_release_check', event_type=None, delay=1, handler=self.crane_release_check)

    def crane_release_check(self):
        # this is called 1sec after the crane dropped the ball to release it 
        if self.num_balls_to_eject > 0:
            # keep going until finished
            self.delay(name='crane_restart', event_type=None, delay=0.9, handler=self.start_crane)
        else:
            # TODO: crane_release already stopped the crane, do we expect we restarted the crane within 1 sec and now need to stop it again????
            self.game.coils.crane.disable()
            if self.num_balls_locked > 0:
                self.start_spinning()
            else:
                self.stop_spinning()

            self.ball_eject_in_progress = False


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
        self.stop_spinning()
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
