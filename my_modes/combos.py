from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class Combos(Mode):
	"""Award combos for repeated loop shots"""

	def __init__(self, game, priority):
		super(Combos, self).__init__(game, priority)

	def mode_started(self):
		player = self.game.current_player()
		self.best_inner_loops = player.getState('best_inner_loops', 0)
		self.best_outer_loops = player.getState('best_outer_loops', 0)

		self.outer_loop_active = False
		self.inner_loop_active = False
		self.inner_loop_combos = 0
		self.outer_loop_combos = 0
		
	def mode_stopped(self):
		player = self.game.current_player()
		player.setState('best_inner_loops', self.best_inner_loops)
		player.setState('best_outer_loops', self.best_outer_loops)
		
		self.cancel_delayed(['inner_loop', 'outer_loop'])

	def get_status_layers(self):
		tiny_font = self.game.fonts['tiny7']
		title_layer = TextLayer(128/2, 7, tiny_font, "center").set_text('Best Combos')
		inner_loops_layer = TextLayer(128/2, 16, tiny_font, "center").set_text('Inner Loops: ' + str(self.best_inner_loops).rjust(3))
		outer_loops_layer = TextLayer(128/2, 25, tiny_font, "center").set_text('Outer Loops: ' + str(self.best_outer_loops).rjust(3))
		status_layer = GroupedLayer(128, 32, [title_layer, inner_loops_layer, outer_loops_layer])
		return [status_layer]

	def sw_topRightOpto_active(self, sw):
		# See if ball came around inner left loop
		if self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.inner_loop_active = True
			self.game.sound.play('inner_loop')
			self.inner_loop_combos += 1
			if self.inner_loop_combos > self.best_inner_loops:
				self.best_inner_loops = self.inner_loop_combos
			score = 10000 * self.inner_loop_combos
			self.game.score(score)
			self.game.base_play.show_on_display('inner loop: ' + str(self.inner_loop_combos), score, 'mid')
			anim = self.game.animations['bike_across_screen']
			self.game.base_play.play_animation(anim, 'mid', repeat=False, hold=False, frame_time=3)
			self.game.update_lamps()
			self.cancel_delayed('inner_loop')
			self.delay(name='inner_loop', event_type=None, delay=3.0, handler=self.inner_loop_combo_expired)

	def sw_leftRollover_active(self, sw):
		# See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1:
			self.outer_loop_active = True
			self.game.sound.play('outer_loop')
			self.outer_loop_combos += 1
			if self.outer_loop_combos > self.best_outer_loops:
				self.best_outer_loops = self.outer_loop_combos
			score = 1000 * self.outer_loop_combos
			self.game.score(score)
			self.game.base_play.show_on_display('outer loop: ' + str(self.outer_loop_combos), score, 'mid')
			anim = self.game.animations['bike_across_screen']
			self.game.base_play.play_animation(anim, 'mid', repeat=False, hold=False, frame_time=3)
			self.game.update_lamps()
			self.cancel_delayed('outer_loop')
			self.delay(name='outer_loop', event_type=None, delay=3.0, handler=self.outer_loop_combo_expired )

	def inner_loop_combo_expired(self):
		self.inner_loop_combos = 0
		self.inner_loop_active = False
		self.game.update_lamps()

	def outer_loop_combo_expired(self):
		self.outer_loop_combos = 0
		self.outer_loop_active = False
		self.game.update_lamps()
		
	def update_lamps(self):
		style = 'slow' if self.inner_loop_active else 'off'
		for lamp_name in ['perp2W', 'perp2R', 'perp2Y', 'perp2G']:
			self.game.drive_lamp(lamp_name, style)

		style = 'slow' if self.outer_loop_active else 'off'
		for lamp_name in ['perp4W', 'perp4R', 'perp4Y', 'perp4G']:
			self.game.drive_lamp(lamp_name, style)

