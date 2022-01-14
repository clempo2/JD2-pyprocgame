from procgame.game import Mode

class Introduction(Mode):
    """Display instructions for a mode"""

    def __init__(self, game, priority, delay=0, gi=True):
        super(Introduction, self).__init__(game, priority)
        self.start_delay = delay
        self.gi = gi
        self.exit_callback = None

    def setup(self, intro_layer):
        # expecting a ScriptedLayer because of the on_complete callback
        intro_layer.on_complete = self.finish
        self.intro_layer = intro_layer

    def mode_started(self):
        self.layer = None
        self.delay(name='start', event_type=None, delay=self.start_delay, handler=self.start)

    def mode_stopped(self):
        self.cancel_delayed(['start'])

    def start(self):
        self.intro_layer.reset()
        self.layer = self.intro_layer

    def finish(self):
        self.game.modes.remove(self)
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

    def update_lamps(self):
        self.game.enable_gi(self.gi)
