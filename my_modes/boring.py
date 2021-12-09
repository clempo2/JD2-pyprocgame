from procgame.game import Mode

class Boring(Mode):
	"""Taunt player if nothing happens for a while"""
	
	def __init__(self, game, priority):
		super(Boring, self).__init__(game, priority)
	
	def mode_started(self):
		self.enable_reset = False
		self.reset()
		
	def mode_stopped(self):
		self.cancel_delayed('timer')

	def timer_expired(self):
		self.delay(name='timer', event_type=None, delay=8, handler=self.timer_expired)
		self.game.sound.play('boring')

	def pause(self):
		self.cancel_delayed('timer')

	def reset(self):
		self.cancel_delayed('timer')
		self.delay(name='timer', event_type=None, delay=20, handler=self.timer_expired)

	def popper_active(self):
		self.pause()
		self.enable_reset = True

	def popper_inactive(self):
		if self.enable_reset:
			self.enable_reset = False
			self.reset()
		
	def sw_subwayEnter2_active(self, sw):
		self.reset()

	def sw_rightRampExit_active(self, sw):
		self.reset()

	def sw_leftRampExit_active(self, sw):
		self.reset()

	def sw_popperR_active_for_1s(self, sw):
		self.popper_active()

	def sw_popperR_inactive_for_1s(self, sw):
		self.popper_inactive()

	def sw_popperL_active_for_1s(self, sw):
		self.pause()
		self.enable_reset = True

	def sw_popperL_inactive_for_1s(self, sw):
		self.popper_inactive()

	def sw_shooterL_active_for_1s(self, sw):
		self.pause()
		self.enable_reset = True

	def sw_shooterL_inactive_for_1s(self, sw):
		if self.enable_reset:
			self.reset()
			self.enable_reset = False

	def sw_shooterR_active(self, sw):
		self.pause()

	def sw_shooterR_inactive_for_1s(self, sw):
		self.reset()

	def sw_leftRollover_active(self, sw):
		self.reset()

	def sw_outlaneR_active(self, sw):
		self.reset()

	def sw_outlaneL_active(self, sw):
		self.reset()

	def sw_craneRelease_active(self, sw):
		self.reset()

	def sw_leftRampToLock_active(self, sw):
		self.reset()

	def sw_trough1_active(self, sw):
		self.reset()

	def sw_trough6_active(self, sw):
		self.reset()

	def sw_dropTargetJ_active(self, sw):
		self.reset()

	def sw_dropTargetU_active(self, sw):
		self.reset()

	def sw_dropTargetD_active(self, sw):
		self.reset()

	def sw_dropTargetG_active(self, sw):
		self.reset()

	def sw_dropTargetE_active(self, sw):
		self.reset()
	