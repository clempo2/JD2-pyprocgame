from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode, SwitchStop
from procgame.service import ServiceModeSkeleton

class Deadworld(Mode):
    """Controls the Deadworld planet"""

    def __init__(self, game, priority):
        super(Deadworld, self).__init__(game, priority)
        # a ball locked in this class means physically held by the planet,
        # this may or may not be a lock owned by the current player
        self.num_balls_locked = 0
        self.num_balls_to_eject = 0
        self.stowing_away = True
        self.preparing_eject = False
        self.ejecting = False
        self.eject_callback = None
        self.searching_balls = False
        self.crane_release_sensitive = True

    def mode_started(self):
        # when powering up the machine, position the crane in rest position (farthest from the ring)
        self.delay(name='start_crane', event_type=None, delay=0.2, handler=self.start_crane)

    def mode_stopped(self):
        # remove the switch rule
        self.install_spinning_rule(auto_disable=False)
        self.stop_spinning()
        self.game.coils.crane.disable()

    def start_spinning(self, auto_stop=False):
        self.install_spinning_rule(auto_stop)
        self.game.coils.globeMotor.pulse(0)

    def stop_spinning(self):
        self.game.coils.globeMotor.disable()

    def install_spinning_rule(self, auto_disable):
        # when auto_disable is True, the globe will stop spinning when it reaches its start position (globePosition2)
        # when auto_disable is False, the globe will keep spinning
        # globePosition2 is when any planet slot is aligned with the crane grab position.
        switch_num = self.game.switches.globePosition2.number
        self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, auto_disable)

    def sw_leftRampToLock_active(self, sw):
        # planet holds one more ball, it does not necessarily mean the player locked the ball
        self.num_balls_locked += 1
        self.game.trough.num_balls_locked += 1

    def perform_ball_search(self):
        # called in attract mode when the trough should be full but isn't
        if not self.searching_balls:
            self.searching_balls = True
            self.delay('stop_ball_search', event_type=None, delay=45, handler=self.stop_ball_search)
            self.init_eject()

    def stop_ball_search(self):
        self.searching_balls = False
        self.cancel_delayed('stop_ball_search')

    def eject_balls(self, num, eject_callback=None):
        self.num_balls_to_eject += num
        self.eject_callback = eject_callback

        # Tell the trough the balls aren't locked anymore so it can count properly.
        # Using max is a self-correcting error check, value must never be negative
        self.game.trough.num_balls_locked = max(0, self.game.trough.num_balls_locked - num)
        self.init_eject()

    def init_eject(self):
        if not self.ejecting:
            # this flag tells the crane and crane magnet to activate at the proper time
            self.ejecting = True
            if self.game.switches.globePosition2.is_active():
                self.start_eject()
            else:
                self.prepare_eject()

    def prepare_eject(self):
        # wait for the globe to be in its home position
        self.preparing_eject = True
        self.start_spinning()

    def sw_globePosition2_active(self, sw):
        if self.preparing_eject:
            self.start_eject()

    def start_eject(self):
        # the globe is in position 2, we can start the eject cycle
        # this code is slightly redundant on purpose to make it more resilient upon unforeseen error
        self.preparing_eject = False
        self.start_spinning(auto_stop=True)
        self.delay(name='start_crane', event_type=None, delay=0.8, handler=self.start_crane)

    def start_crane(self):
        # start the crane moving
        self.game.coils.crane.pulse(0)

    def sw_magnetOverRing_open(self, sw):
        if self.ejecting or self.stowing_away:
            # turn the crane magnet on for 2 seconds
            self.game.coils.craneMagnet.pulse(0)
            self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)

    def crane_release(self):
        # this is called 2 seconds after the crane grabbed the ball over the ring
        # stop the crane movement and drop the ball to release it
        self.game.coils.crane.disable()
        self.game.coils.craneMagnet.disable()
        self.delay(name='crane_done', event_type=None, delay=0.25, handler=self.crane_done)

    def sw_craneRelease_active(self, sw):
        # this switch detects a ball was indeed ejected
        # crane_release_sensitive is a debounce flag
        if self.crane_release_sensitive:
            # After a successful ball release, we ignore the crane release switch for the next 2 seconds.
            self.crane_release_sensitive = False
            self.delay(name='crane_sensitive', event_type=None, delay=2, handler=self.crane_sensitive)

            # We can now update the ball counts with confidence
            # Using max is a self-correcting error check, value must never be negative
            #   especially during ball search
            self.num_balls_to_eject = max(0, self.num_balls_to_eject - 1)
            self.num_balls_locked = max(0, self.num_balls_locked - 1)

    def crane_sensitive(self):
        # make the crane release switch sensitive again
        self.crane_release_sensitive = True

    def crane_done(self):
        # this is called 1/4 second after the crane dropped the ball to release it
        # determine what the crane and globe should do next
        if self.searching_balls:
            if self.game.trough.is_full():
                self.searching_balls = False
                self.ejecting = False
                self.cancel_delayed('stop_ball_search')
                self.stop_spinning()
            else:
                # keep searching
                self.start_eject()
        elif self.num_balls_to_eject > 0:
            # keep ejecting until finished
            self.start_eject()
        else:
            self.ejecting = False
            self.stowing_away = False
            if self.eject_callback:
                self.eject_callback()
            else:
                self.stop_spinning()

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
        self.game.remove_modes([self])
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
