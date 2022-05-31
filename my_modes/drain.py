from procgame.game import Mode
from tilt import TiltMonitorMode

class DrainMode(Mode):
    """Monitor drains to determine when the ball has ended.
       This mode waits for balls to drain when the player has tilted,
       therefore it must not affect the score or lamps.
    """

    def __init__(self, game, priority):
        super(DrainMode, self).__init__(game, priority)
        num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
        self.tilt = TiltMonitorMode(self.game, 1000, 'tilt', 'slamTilt', num_tilt_warnings)

    def mode_started(self):
        self.game.trough.drain_callback = self.drain_callback
        self.game.ball_search.enable()
        self.game.add_modes([self.tilt])

    def mode_stopped(self):
        self.game.trough.drain_callback = self.game.no_op_callback
        self.game.disable_ball_search()
        self.game.remove_modes([self.tilt])
        self.game.enable_flippers(False)

    def update_lamps(self):
        self.game.disable_all_lights()
        self.game.enable_gi(True)

    def drain_callback(self):
        if not self.tilt.tilted:
            if self.game.send_event('evt_ball_drained'):
                # drain was intentional, ignore it
                return

        if self.game.num_balls_requested() == 0:
            if self.tilt.tilted:
                # wait for the tilt bob to stabilize, then finish the ball
                self.tilt.tilt_delay(self.finish_ball)
            else:
                self.finish_ball()

    def finish_ball(self):
        self.game.sound.fadeout_music()
        self.game.disable_ball_search()
        self.game.coils.globeMotor.disable()
        self.game.remove_modes([self.tilt])
        self.game.enable_flippers(False)

        if self.game.send_event('evt_ball_ended'):
            # bonus mode will take care of it for us
            return
        
        # only way to reach here is if the player tilted
        self.game.end_ball()
