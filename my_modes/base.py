from procgame.dmd import ScriptedLayer, TextLayer
from procgame.game import AdvancedMode

class Base(AdvancedMode):
    """Mode active throughout the whole cycle attract + game + initial entry"""

    def __init__(self, game, priority):
        super(Base, self).__init__(game, priority, AdvancedMode.System)

    def evt_volume_down(self, volume):
        self.set_status('VOLUME DOWN: ' + str(int(volume)), scroll=False)

    def evt_volume_up(self, volume):
        self.set_status('VOLUME UP: ' + str(int(volume)), scroll=False)

    def evt_tilt_warning(self, unused_times):
        self.game.sound.play('tilt warning')
        self.game.set_status('WARNING')

    def evt_tilt(self, slam_tilt):
        self.game.sound.fadeout_music()
        self.game.stop_all_sounds()
        # remove all scoring modes and shut up boring mode
        self.game.remove_modes([self.game.base_play])

        # slam tilt stays quiet
        if not slam_tilt:
            self.game.sound.play('tilt')

        tilt_msg = 'SLAM TILT' if slam_tilt else 'TILT'
        text_layer = TextLayer(128/2, 7, self.game.fonts['large'], 'center', opaque=True)
        self.game.tilted_mode.layer = text_layer.set_text(tilt_msg)

    def evt_balls_missing(self):
        self.game.set_status('BALL MISSING')
        self.game.deadworld.perform_ball_search()

    def evt_game_ending(self):
        self.game.attract_mode.update_score_layer()
        font_large = self.game.fonts['large']
        longwalk_layer = self.game.animations['longwalk']
        game_over_layer = TextLayer(128/2, 7, font_large, 'center', opaque=True).set_text('Game Over')

        script = [
            {'seconds':3.4, 'layer':longwalk_layer}, # stop this anim early, Game Over font does not fit rest of the game
            {'seconds':2.5, 'layer':game_over_layer},
        ]

        self.layer = ScriptedLayer(width=128, height=32, script=script, hold=True, opaque=True)
        return self.layer.duration()

    def evt_game_ended(self):
        self.layer = None