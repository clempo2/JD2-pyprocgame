from procgame.game import Mode

class Introduction(Mode):
    """Display instructions for a mode"""

    def mode_started(self):
        self.game.enable_flippers(False)
        self.delay(name='finish', event_type=None, delay=self.layer.duration(), handler=self.finish)

    def mode_stopped(self):
        self.cancel_delayed('finish')
        self.game.enable_flippers(True)

    def setup(self, mode):
        self.layer = mode.get_instruction_layer()

    def sw_flipperLwL_active(self, sw):
        self.finish()

    def sw_flipperLwR_active(self, sw):
        self.finish()

    def finish(self):
        self.game.modes.remove(self)
        self.exit_callback()
