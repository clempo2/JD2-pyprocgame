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

        self.report_layers = ([main_title_layer] +
            self.game.base_play.regular_play.chain.get_status_layers() +
            self.game.base_play.regular_play.crime_scenes.crime_scene_levels.get_status_layers() +
            self.game.base_play.combos.get_status_layers())

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
