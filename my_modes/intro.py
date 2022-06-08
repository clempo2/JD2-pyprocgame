from procgame.game import Mode

class Introduction(Mode):
    """Display instructions for a mode"""

    def __init__(self, game, priority):
        super(Introduction, self).__init__(game, priority)
        self.exit_callback = None

    def setup(self, intro_layer):
        # expecting a ScriptedLayer because of the on_complete callback we install
        intro_layer.on_complete = self.finish
        self.intro_layer = intro_layer

    def mode_started(self):
        self.intro_layer.reset()
        self.layer = self.intro_layer

    def finish(self):
        self.game.remove_modes([self])
        if self.exit_callback:
            self.exit_callback()

    def sw_flipperLwL_active(self, sw):
        self.finish()

    def sw_flipperLwR_active(self, sw):
        self.finish()

    def sw_fireL_active(self, sw):
        self.finish()

    def sw_fireR_active(self, sw):
        self.finish()
