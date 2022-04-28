from procgame.game import Mode

class Bonus(Mode):
    """Display end of ball bonus"""

    def __init__(self, game, priority):
        super(Bonus, self).__init__(game, priority)

    def mode_started(self):
        self.game.stop_all_sounds()
        self.game.sound.play_voice('drain')
        self.game.base_play.display('Bonus')

        # compute everything before we start so we can easily skip to the end
        # do not show bonus items worth zero
        self.bonus_items = (self.create_item('num_chain_features', 'Chain Feature', 4000) +
            self.create_item('num_hurry_ups', 'Hurry Up', 12000) +
            self.create_item('num_blocks', 'Block', 2000))

        bonus = sum(item['points'] for item in self.bonus_items)
        bonus_x = self.game.getPlayerState('bonus_x', 1)
        if bonus > 0 and bonus_x > 1:
            self.bonus_items += [{'text': str(bonus_x) + 'X', 'points': None}]
            bonus *= bonus_x
        self.game.score(bonus)

        self.bonus_items += [{'text': 'Total', 'points': bonus}]
        self.delay(name='show_bonus', event_type=None, delay=1.5, handler=self.show_bonus, param=0)

    def create_item(self, state, title, value):
        num = self.game.getPlayerState(state, 0)
        return [] if num == 0 else [{'text': self.format_text(num, title), 'points': num * value}]

    def format_text(self, value, title):
        return str(value) + ' ' + title + ('s' if value > 1 else '')

    def show_bonus(self, index):
        if index == len(self.bonus_items):
            self.game.base_play.display('')
            self.exit_callback()
        else:
            self.game.sound.play('bonus')
            bonus_item = self.bonus_items[index]
            self.game.base_play.display(bonus_item['text'], bonus_item['points'])
            self.delay(name='show_bonus', event_type=None, delay=1.5, handler=self.show_bonus, param=index + 1)

    def sw_flipperLwL_active(self, sw):
        self.flipper_active()

    def sw_flipperLwR_active(self, sw):
        self.flipper_active()

    def flipper_active(self):
        # skip to total
        self.cancel_delayed('show_bonus')
        self.show_bonus(len(self.bonus_items) - 1)
