from procgame.game import AdvancedMode
from tilt import TiltMonitorMode

class DrainMode(AdvancedMode):
    """Monitor drains to determine when the ball has ended.
       This mode waits for balls to drain when the player has tilted,
       therefore it must not affect the score or lamps.
    """

    def __init__(self, game, priority):
        super(DrainMode, self).__init__(game, priority, AdvancedMode.Ball)
        self.tilt_monitor = TiltMonitorMode(game, 1000, 'tilt', 'slamTilt')

    def mode_started(self):
        #TODO self.game.trough.drain_callback = self.drain_callback
        self.game.ball_search.enable()
        self.game.add_modes([self.tilt_monitor])

    def mode_stopped(self):
        #TODO self.game.trough.drain_callback = self.game.no_op_callback
        self.game.disable_ball_search()
        self.game.remove_modes([self.tilt_monitor])
        self.game.enable_flippers(False)

    def update_lamps(self):
        self.game.disable_all_lights()
        self.game.enable_gi(True)

    def TODO_drain_callback(self):
        if not self.tilt_monitor.tilted:
            if self.game.send_event('event_ball_drained'):
                # drain was intentional, ignore it
                return

        if self.game.num_balls_requested() == 0:
            if self.tilt_monitor.tilted:
                # wait for the tilt bob to stabilize, then finish the ball
                self.tilt_monitor.tilt_delay(self.finish_ball)
            else:
                self.finish_ball()

    def finish_ball(self):
        self.game.sound.fadeout_music()
        self.game.disable_ball_search()
        self.game.coils.globeMotor.disable()
        self.game.remove_modes([self.tilt_monitor])
        self.game.enable_flippers(False)

        if self.game.send_event('event_ball_ended'):
            # bonus mode will take care of it for us
            return
        
        # only way to reach here is if the player tilted
        self.game.end_ball()
