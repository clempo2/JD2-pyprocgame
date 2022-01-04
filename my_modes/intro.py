from procgame.game import Mode

class Introduction(Mode):
    """Display instructions for a mode"""

    def __init__(self, game, priority, delay=0):
        super(Introduction, self).__init__(game, priority)
        self.start_delay = delay
        self.exit_callback = None

    def mode_started(self):
        self.delay(name='start', event_type=None, delay=self.start_delay, handler=self.start)

    def mode_stopped(self):
        self.cancel_delayed(['start', 'finish'])

    def start(self):
        self.delay(name='finish', event_type=None, delay=self.layer.duration(), handler=self.finish)

    def setup(self, mode):
        # expecting a ScriptedLayer with a duration()
        self.layer = mode.get_instruction_layer()

    def sw_flipperLwL_active(self, sw):
        self.finish()

    def sw_flipperLwR_active(self, sw):
        self.finish()

    def sw_fireL_active(self, sw):
        self.finish()

    def sw_fireR_active(self, sw):
        self.finish()

    def finish(self):
        self.game.modes.remove(self)
        if self.exit_callback:
            self.exit_callback()
