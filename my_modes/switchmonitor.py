from procgame.game import AdvancedMode, SwitchStop, SwitchContinue
from procgame.highscore import EntrySequenceManager

class JDSwitchMonitor(AdvancedMode):
    """A mode that monitors for specific switches and helps advance state as appropriate"""

    def __init__(self, game):
        super(JDSwitchMonitor, self).__init__(game, priority=32767)
        self.allow_restart = self.game.user_settings['Gameplay']['Allow restarts']

    # Enter service mode when the enter button is pushed.
    def sw_enter_active(self, sw):
        self.game.log('starting service mode')
        if not self.game.service_mode in self.game.modes:
            self.game.start_service_mode()
            return SwitchStop
        return SwitchContinue

    def sw_down_active(self, sw):
        if not self.game.service_mode in self.game.modes:
            self.game.volume_down()
            return SwitchStop
        return SwitchContinue

    def sw_up_active(self, sw):
        if not self.game.service_mode in self.game.modes:
            self.game.volume_up()
            return SwitchStop
        return SwitchContinue

    def sw_startButton_active_for_3s(self, sw):
        if self.game.ball > 1 and self.allow_restart:
            self.game.reset()
            return SwitchStop
        return SwitchContinue

    def sw_startButton_active_for_5s(self, sw):
        # you must press longer to restart on ball 1
        if self.allow_restart:
            self.game.reset()
            return SwitchStop
        return SwitchContinue

    def sw_startButton_active(self, sw):
        self.start_button_activated(False, 'Start button')

    def sw_superGame_active(self, sw):
        self.start_button_activated(True, 'Supergame button')

    def start_button_activated(self, supergame, button_name):
        for m in self.game.modes:
            if isinstance(m, EntrySequenceManager):
                return SwitchContinue

        if self.game.attract_mode in self.game.modes:
            if self.game.trough.is_full():
                # start_game() takes care of adding the first player and starting a ball
                self.game.start_game(supergame)
            else:
                self.game.attract_mode.ball_search()
        else:
            # game already started, add another player to current game
            # it does not have to be the same button that started the game
            if self.game.ball == 1:
                self.game.request_additional_player()
            else:
                self.game.logger.info('SwitchMonitor: ' + button_name + ' pressed, ignored at this stage')
        return SwitchStop
