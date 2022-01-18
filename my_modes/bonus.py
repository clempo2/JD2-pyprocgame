import locale
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
        chain_features = player.getState('chain_features', 0)
        hurry_ups = player.getState('num_hurry_ups', 0)
        blocks = player.getState('num_blocks', 0)
        
        chain_features_bonus = chain_features * 4000
        hurry_ups_bonus = hurry_ups * 12000
        blocks_bonus = blocks * 2000
        self.base_bonus =  chain_features_bonus + hurry_ups_bonus + blocks_bonus

        self.set_line_text(0, chain_features, 'FEATURE', 'FEATURES', chain_features_bonus)
        self.set_line_text(1, hurry_ups, 'HURRY UP', 'HURRY UPS', hurry_ups_bonus)
        self.set_line_text(2, blocks, 'BLOCK', 'BLOCKS', blocks_bonus)

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
        self.text_layers[index + 2].set_text('00' if str(value) == 0 else locale.format('%d', value, True))

    def sw_flipperLwL_active(self, sw):
        self.flipper_active()

    def sw_flipperLwR_active(self, sw):
        self.flipper_active()

    def flipper_active(self):
        # skip to total
        self.cancel_delayed('show_bonus')
        self.show_page2()
