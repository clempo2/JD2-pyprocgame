from procgame.dmd import ScriptedLayer, TextLayer
from procgame.game import AdvancedMode

class Base(AdvancedMode):
    """Mode active throughout the whole cycle attract + game + initial entry"""

    def __init__(self, game, priority):
        super(Base, self).__init__(game, priority, AdvancedMode.System)

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