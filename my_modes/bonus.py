from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class Bonus(Mode):
    """Display end of ball bonus"""

    def __init__(self, game, priority):
        super(Bonus, self).__init__(game, priority)
        font_big = self.game.fonts['jazz18']
        self.title_layer = TextLayer(128/2, 7, font_big, 'center').set_text('BONUS')
        self.title_layer.opaque = True
        self.text_layers = [self.create_text_layer(i) for i in range(0, 9)]
        self.tabular_layer = GroupedLayer(128, 32, self.text_layers)

    def mode_started(self):
        self.game.stop_all_sounds()
        self.game.sound.play_voice('drain')
        self.layer = self.title_layer
        self.delay(name='show_bonus', event_type=None, delay=1.5, handler=self.show_page1)

    def mode_stopped(self):
        self.cancel_delayed('show_bonus')

    def show_page1(self):
        self.game.sound.play('bonus')
        self.layer = self.tabular_layer

        player = self.game.current_player()
        modes_attempted = player.getState('num_modes_attempted', 0)
        modes_completed = player.getState('num_modes_completed', 0)
        crime_scenes = player.getState('crime_scenes_total_levels', 0)
        
        modes_attempted_bonus = modes_attempted * 4000
        modes_completed_bonus = modes_completed * 12000
        crime_scenes_bonus = crime_scenes * 2000
        self.base_bonus =  modes_attempted_bonus + modes_completed_bonus + crime_scenes_bonus

        self.set_line_text(0, modes_attempted, 'MODE', 'MODES', modes_attempted_bonus)
        self.set_line_text(1, modes_completed, 'COMPLETED', 'COMPLETED', modes_completed_bonus)
        self.set_line_text(2, crime_scenes, 'CRIME SCENE', 'CRIME SCENES', crime_scenes_bonus)

        self.delay(name='show_bonus', event_type=None, delay=3, handler=self.show_page2)

    def show_page2(self):
        self.game.sound.play('bonus')

        bonus_x = self.game.getPlayerState('bonus_x', 1)
        total = self.base_bonus * bonus_x
        self.game.score(total)

        self.set_line_text(0, -1, 'BASE', None, self.base_bonus)
        self.set_line_text(1, -1, 'BONUS X', None, bonus_x)
        self.set_line_text(2, -1, 'TOTAL', None, total)

        self.delay(name='show_bonus', event_type=None, delay=3, handler=self.exit_callback)

    def create_text_layer(self, index):
        font_small = self.game.fonts['07x5']
        x = [20, 24, 118][index % 3]
        y = 3 + 10 * int(index / 3)
        justify = ['right', 'left', 'right'][index % 3]
        return TextLayer(x, y, font_small, justify)

    def set_line_text(self, line_index, count, singular, plural, value):
        index = line_index * 3
        self.text_layers[index].set_text('' if count < 0 else str(count))
        self.text_layers[index + 1].set_text(singular if count < 2 else plural)
        self.text_layers[index + 2].set_text('00' if str(value) == 0 else str(value))

    def sw_flipperLwL_active(self, sw):
        self.flipper_active()

    def sw_flipperLwR_active(self, sw):
        self.flipper_active()

    def flipper_active(self):
        # skip to total
        self.cancel_delayed('show_bonus')
        self.show_page2()
