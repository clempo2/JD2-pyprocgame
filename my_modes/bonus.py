from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class Bonus(Mode):
    """Display end of ball bonus"""

    def __init__(self, game, priority):
        super(Bonus, self).__init__(game, priority)
        font_big = self.game.fonts['jazz18']
        font_small = self.game.fonts['tiny7']
        self.title_layer = TextLayer(128/2, 7, font_big, 'center')
        self.name_layer = TextLayer(128/2, 7, font_small, 'center')
        self.value_layer = TextLayer(128/2, 20, font_small, 'center')
        self.layer = GroupedLayer(128, 32, [self.title_layer, self.name_layer, self.value_layer])

    def mode_started(self):
        self.game.sound.play('drain')

        self.delay_time = 1
        self.title_layer.set_text('BONUS', self.delay_time)
        self.name_layer.set_text('')
        self.value_layer.set_text('')

        player = self.game.current_player()
        num_modes_attempted = player.getState('num_modes_attempted', 0)
        attempted = ['Modes Attempted: ' + str(num_modes_attempted), num_modes_attempted * 4000]

        num_modes_completed = player.getState('num_modes_completed', 0)
        completed = ['Modes Completed: ' + str(num_modes_completed), num_modes_completed * 12000]

        crimescenes_total_levels = player.getState('crimescenes_total_levels', 0)
        crimescenes = ['Crimescene Levels: ' + str(crimescenes_total_levels), crimescenes_total_levels * 2000]

        base = attempted[1] + completed[1] + crimescenes[1]
        total_base = ['Total Base:', base]

        bonus_x = player.getState('bonus_x', 1)
        multiplier = ['Multiplier:', bonus_x]

        total = base * bonus_x
        total_bonus = ['Total Bonus:', total]
        self.game.score(total)

        self.item_index = 0
        self.bonus_items = [attempted, completed, crimescenes, total_base, multiplier, total_bonus]
        self.delay(name='show_bonus', event_type=None, delay=self.delay_time, handler=self.show_bonus_items)

    def mode_stopped(self):
        self.cancel_delayed('show_bonus')

    def show_bonus_items(self):
        if self.item_index == len(self.bonus_items):
            self.exit_callback()
            return

        self.game.sound.play('bonus')

        text, value = self.bonus_items[self.item_index]
        self.name_layer.set_text(text)
        self.value_layer.set_text(str(value))

        self.item_index += 1
        self.delay(name='show_bonus', event_type=None, delay=self.delay_time, handler=self.show_bonus_items)

    def sw_flipperLwL_active(self, sw):
        # speed up
        self.delay_time = 0.2

    def sw_flipperLwR_active(self, sw):
        # skip to total
        self.item_index = len(self.bonus_items) - 1
