from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class StatusReport(Mode):
    """Display status report"""

    def mode_started(self):
        tiny_font = self.game.fonts['tiny7']
        player = self.game.current_player()

        report_title_layer = TextLayer(128/2, 9, tiny_font, 'center').set_text('Status Report')
        extra_ball_layer = TextLayer(128/2, 19, tiny_font, 'center').set_text('Extra Balls: ' + str(player.extra_balls))
        main_title_layer = GroupedLayer(128, 32, [report_title_layer, extra_ball_layer])

        # chain features
        attempted_layer = TextLayer(128/2, 9, tiny_font, 'center').set_text('Chain features: ' + str(player.getState('num_chain_features', 0)))
        completed_layer = TextLayer(128/2, 19, tiny_font, 'center').set_text('Hurry Ups: ' + str(player.getState('num_hurry_ups', 0)))
        chain_layer = GroupedLayer(128, 32, [attempted_layer, completed_layer])

        # city blocks
        # if block war is currently playing, next block war is in 4 blocks
        current_block = player.getState('current_block', 0)
        num_blocks = player.getState('num_blocks', 0)
        block_title_layer = TextLayer(128/2, 7, tiny_font, 'center').set_text('Blocks')
        current_block_layer = TextLayer(128/2, 16, tiny_font, 'center').set_text('Current Block: ' + str(current_block + 1) + '/' + str(self.game.blocks_required))
        block_war_layer = TextLayer(128/2, 25, tiny_font, 'center').set_text('Next Block War in ' + str(4-(num_blocks % 4)) + ' blocks')
        block_layer = GroupedLayer(128, 32, [block_title_layer, current_block_layer, block_war_layer])

        # combos
        combo_title_layer = TextLayer(128/2, 7, tiny_font, 'center').set_text('Best Combos')
        inner_loops_layer = TextLayer(128/2, 16, tiny_font, 'center').set_text('Inner Loops: ' + str(player.getState('best_inner_loops', 0)).rjust(3))
        outer_loops_layer = TextLayer(128/2, 25, tiny_font, 'center').set_text('Outer Loops: ' + str(player.getState('best_outer_loops', 0)).rjust(3))
        combo_layer = GroupedLayer(128, 32, [combo_title_layer, inner_loops_layer, outer_loops_layer])

        self.report_layers = [main_title_layer, chain_layer, block_layer, combo_layer]
        self.index = 0
        self.index_max = len(self.report_layers) - 1
        self.update_display()

    def mode_stopped(self):
        self.cancel_delayed('delayed_progression')
        self.report_layers = []

    def update_display(self):
        self.layer = self.report_layers[self.index]
        self.delay(name='delayed_progression', event_type=None, delay=3.0, handler=self.progress, param=1)

    def progress(self, step):
        self.cancel_delayed('delayed_progression')
        self.index += step
        if self.index < 0:
            self.index = self.index_max
        elif self.index > self.index_max:
            self.index = 0
        self.update_display()

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
        self.game.modes.remove(self)
        # this mode owns no lamps so no need to update lamps
