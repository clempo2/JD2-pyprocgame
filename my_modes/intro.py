from procgame.game import Mode

class Introduction(Mode):
    """Display instructions for a mode"""

    def __init__(self, game, priority, delay=0, gi=True):
        super(Introduction, self).__init__(game, priority)
        self.start_delay = delay
        self.gi = gi
        self.exit_callback = None

    def setup(self, mode):
        # expecting a ScriptedLayer because of the on_complete callback
        self.intro_layer = mode.get_instruction_layer()
        self.intro_layer.on_complete = self.finish
        self.intro_layer.reset()

    def mode_started(self):
        self.delay(name='start', event_type=None, delay=self.start_delay, handler=self.start)

    def mode_stopped(self):
        self.cancel_delayed(['start'])

    def start(self):
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
