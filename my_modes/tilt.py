from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class TiltMonitorMode(Mode):
	"""Monitor tilt warnings and slam tilt"""

	def __init__(self, game, priority, tilt_sw=None, slam_tilt_sw=None):
		super(TiltMonitorMode, self).__init__(game, priority)
		font_big = self.game.fonts['jazz18']
		self.text_layer = TextLayer(128/2, 7, font_big, "center")
		if tilt_sw:
			self.add_switch_handler(name=tilt_sw, event_type='active', delay=None, handler=self.tilt_handler)
		if slam_tilt_sw:
			self.add_switch_handler(name=slam_tilt_sw, event_type='active', delay=None, handler=self.slam_tilt_handler)
		self.num_tilt_warnings = 0
		self.tilted = False

	def mode_started(self):
		self.times_warned = 0
		self.layer = None
		self.tilted = False

	def tilt_handler(self, sw):
		if self.times_warned == self.num_tilt_warnings:
			if not self.tilted:
				self.tilted = True
				self.tilt_callback()
		else:
			self.game.sound.stop('tilt warning')
			self.times_warned += 1
			self.game.sound.play('tilt warning')
			self.text_layer.set_text('Warning', 3)
		self.layer = GroupedLayer(128, 32, [self.text_layer])

	def slam_tilt_handler(self, sw):
		self.slam_tilt_callback()

	def tilt_delay(self, fn, secs_since_bob_tilt=2.0):
		""" calls the specified `fn` if it has been at least `secs_since_bob_tilt`
			(make sure the tilt isn't still swaying)
		"""
		if self.tilt_sw.time_since_change() < secs_since_bob_tilt:
			self.delay(name='tilt_bob_settle', event_type=None, delay=secs_since_bob_tilt, handler=self.tilt_delay, param=fn)
		else:
			return fn()

	def tilt_callback(self):
		self.game.sound.fadeout_music()
		self.game.sound.play('tilt')
		self.text_layer.set_text('TILT')
		self.game.enable_flippers(False) 
		self.game.ball_save.disable()
		self.game.ball_search.disable()

		# all lamps off.
		for lamp in self.game.lamps:
			lamp.disable()

		# Kick balls out of places it could be stuck.
		if self.game.switches.shooterR.is_active():
			self.game.coils.shooterR.pulse(50)
		if self.game.switches.shooterL.is_active():
			self.game.coils.shooterL.pulse(20)
		
	def slam_tilt_callback(self):
		self.game.sound.play('slam_tilt')
		self.text_layer.set_text('SLAM TILT')
		self.layer = GroupedLayer(128, 32, [self.text_layer])

		self.game.sound.fadeout_music()
		self.game.reset()
