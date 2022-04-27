from procgame.game import Mode

class Boring(Mode):
    """Taunt player if nothing happens for a while"""

    def __init__(self, game, priority):
        super(Boring, self).__init__(game, priority)
        for switch in ['subwayEnter2', 'rightRampExit', 'leftRampExit', 'leftRollover', 'outlaneR', 'outlaneL', 'craneRelease', 'leftRampToLock', 
                       'trough1', 'trough6', 'dropTargetJ', 'dropTargetU', 'dropTargetD', 'dropTargetG', 'dropTargetE']:
            self.add_switch_handler(name=switch, event_type='active', delay=None, handler=self.reset)

    def mode_started(self):
        self.enable_reset = False
        self.reset()

    def timer_expired(self):
        self.delay(name='timer', event_type=None, delay=8, handler=self.timer_expired)
        self.game.sound.play('boring')

    def pause(self):
        self.cancel_delayed('timer')

    def reset(self, sw=None):
        self.cancel_delayed('timer')
        self.delay(name='timer', event_type=None, delay=20, handler=self.timer_expired)

    def popper_active(self):
        self.pause()
        self.enable_reset = True

    def popper_inactive(self):
        if self.enable_reset:
            self.enable_reset = False
            self.reset()

    def sw_popperR_active_for_1s(self, sw):
        self.popper_active()

    def sw_popperR_inactive_for_1s(self, sw):
        self.popper_inactive()

    def sw_popperL_active_for_1s(self, sw):
        self.popper_active()

    def sw_popperL_inactive_for_1s(self, sw):
        self.popper_inactive()

    def sw_shooterL_active_for_1s(self, sw):
        self.popper_active()

    def sw_shooterL_inactive_for_1s(self, sw):
        self.popper_inactive()

    def sw_shooterR_active(self, sw):
        self.pause()

    def sw_shooterR_inactive_for_1s(self, sw):
        self.reset()
