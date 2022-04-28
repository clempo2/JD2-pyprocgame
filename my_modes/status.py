from procgame.game import Mode

class StatusReport(Mode):
    """Display status report"""

    def mode_started(self):
        self.game.base_play.display('Status')

        player = self.game.current_player()
        num_blocks = player.getState('num_blocks', 0)

        self.status_items = [
            {'text': 'Extra Balls', 'value': player.extra_balls},
            {'text': 'Extra Balls Lit', 'value': player.getState('extra_balls_lit', 0)},
            {'text': 'Chain Features', 'value': player.getState('num_chain_features', 0)},
            {'text': 'Hurry Ups', 'value': player.getState('num_hurry_ups', 0)},
            {'text': 'Blocks', 'value': num_blocks}]

        if num_blocks >= self.game.blocks_required:
            self.status_items += [{'text': 'Current Block', 'value': 1 + player.getState('current_block', 0)}]

        self.status_items += [
            {'text': 'Blocks Remaining', 'value': self.game.blocks_required - player.getState('current_block', 0)},
            {'text': 'Inner Loop Combos', 'value': player.getState('best_inner_loops', 0)},
            {'text': 'Outer Loop Combos', 'value': player.getState('best_outer_loops', 0)}]

        self.num_items = len(self.status_items)
        self.index = 0
        self.delay(name='show_status', event_type=None, delay=1.5, handler=self.show_status)

    def mode_stopped(self):
        self.game.base_play.display('')

    def show_status(self):
        status_item = self.status_items[self.index]
        self.game.base_play.display(status_item['text'], status_item['value'])
        self.delay(name='show_status', event_type=None, delay=1.5, handler=self.progress, param=1)

    def progress(self, step):
        self.cancel_delayed('show_status')
        self.index = (self.index + step + self.num_items) % self.num_items
        self.show_status()

    def sw_flipperLwL_active(self, sw):
        if self.game.switches.flipperLwR.is_active():
            self.progress(-1)

    def sw_flipperLwR_active(self, sw):
        if self.game.switches.flipperLwL.is_active():
            self.progress(1)

    def sw_flipperLwL_inactive(self, sw):
        if self.game.switches.flipperLwR.is_inactive():
            self.exit()

    def sw_flipperLwR_inactive(self, sw):
        if self.game.switches.flipperLwL.is_inactive():
            self.exit()

    def exit(self):
        self.game.remove_modes([self])
        # this mode owns no lamps so no need to update lamps
