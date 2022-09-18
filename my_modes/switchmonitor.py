from procgame.game import SwitchStop, SwitchContinue
from procgame.modes.switchmonitor import SwitchMonitor

class JDSwitchMonitor(SwitchMonitor):
    """A mode that monitors for specific switches and helps advance state as appropriate
	   For JD we also need to monitor the supergame button.
       A setting determines whether to allow resets by pressing start/supergame button for a long time.
    """

    def __init__(self, game):
        super(JDSwitchMonitor, self).__init__(game)

    def sw_startButton_active(self, sw):
        self.superGame_button_pressed = False
        super(JDSwitchMonitor, self).sw_startButton_active(sw)

    def sw_startButton_active_for_2s(self, sw):
        return self.check_reset(2)

    def sw_startButton_active_for_5s(self, sw):
        # you must press longer to restart on ball 1
        return self.check_reset(1)

    def sw_superGame_active(self, sw):
        self.superGame_button_pressed = True
        super(JDSwitchMonitor, self).sw_startButton_active(sw)

    def sw_superGame_active_for_2s(self, sw):
        return self.check_reset(2)

    def sw_superGame_active_for_5s(self, sw):
        # you must press longer to restart on ball 1
        return self.check_reset(1)

    def check_reset(self, min_ball):
        allow_restart = self.game.user_settings['Machine']['Allow restarts']
        if self.game.ball >= min_ball and allow_restart:
            self.game.reset_pending = True
            return SwitchStop
        return SwitchContinue
