from procgame.dmd import ScriptedLayer, TextLayer
from procgame.game import AdvancedMode

class Base(AdvancedMode):
    """Mode active throughout the whole cycle attract + game + initial entry"""

    def __init__(self, game, priority):
        super(Base, self).__init__(game, priority, AdvancedMode.System)

    def mode_started(self):
        self.layer = None
        self.game_over = False

    def evt_volume_down(self, volume):
        self.set_status('VOLUME DOWN: ' + str(int(volume)), scroll=False)

    def evt_volume_up(self, volume):
        self.set_status('VOLUME UP: ' + str(int(volume)), scroll=False)

    def evt_tilt_warning(self, unused_times):
        self.game.sound.play('tilt warning')
        self.game.set_status('WARNING')

    def evt_tilt(self, slam_tilt):
        self.game.sound.fadeout_music()
        self.game.sound.stop_all()

        # remove all scoring modes and shut up boring mode
        self.game.modes.remove(self.game.base_play)

        # eject balls in VUKs and shooter lanes while the balls are draining
        self.game.modes.add(self.game.eject_mode)

        self.game.setPlayerState('hold_bonus_x', False)

        # slam tilt stays quiet
        if not slam_tilt:
            self.game.sound.play('tilt')

        tilt_msg = 'SLAM TILT' if slam_tilt else 'TILT'
        text_layer = TextLayer(128/2, 7, self.game.fonts['large'], 'center', opaque=True)
        self.game.tilted_mode.layer = text_layer.set_text(tilt_msg)

    def evt_tilt_ball_ending(self):
        self.game.modes.remove(self.game.eject_mode)

    def evt_balls_missing(self):
        self.game.set_status('BALL MISSING')
        self.game.deadworld.perform_ball_search()

    def evt_game_ending(self):
        # show the final score before the game over display
        self.game_over = True
        self.layer = self.game.generate_score_layer()
        self.game.attract_mode.score_layer = self.layer
        return 2

    def evt_game_ended(self):
        # show the game over display
        score_layer = self.layer
        font_large = self.game.fonts['large']
        longwalk_layer = self.game.animations['longwalk']
        game_over_layer = TextLayer(128/2, 7, font_large, 'center', opaque=True).set_text('Game Over')

        script = [
            {'seconds':3.4, 'layer':longwalk_layer}, # stop this anim early, Game Over font does not fit rest of the game
            {'seconds':2.5, 'layer':game_over_layer},
            {'seconds':2, 'layer':score_layer}
        ]

        self.layer = ScriptedLayer(width=128, height=32, script=script, hold=True, opaque=True)
        return self.layer.duration()

    def sw_startButton_active(self, sw):
        self.start_button_active()

    def sw_superGame_active(self, sw):
        self.start_button_active()

    def start_button_active(self):
        if self.game_over:
            # skip game over display and initial entry (if applicable)
            # go straight to attract mode
            self.game.safe_reset()
