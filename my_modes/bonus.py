from procgame import *

class Bonus(game.Mode):
	"""Display end of ball bonus"""
	def __init__(self, game, priority, font_big, font_small):
		super(Bonus, self).__init__(game, priority)
		self.font_big = font_big
		self.font_small = font_small
		self.title_layer = dmd.TextLayer(128/2, 7, font_big, "center")
		self.element_layer = dmd.TextLayer(128/2, 7, font_small, "center")
		self.value_layer = dmd.TextLayer(128/2, 20, font_small, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.title_layer,self.element_layer, self.value_layer])

	def mode_started(self):
		# Disable the flippers
		self.game.enable_flippers(False) 
		self.step = 0
		self.delay_time = 1

	def mode_stopped(self):
		# Enable the flippers
		self.game.enable_flippers(True) 

	def compute(self, exit_function):
		self.game.sound.play('drain')
		self.exit_function = exit_function
		self.total_base = 0
		
		p = self.game.current_player()
		self.x = p.getState("bonus_x")
		
		self.elements = []
		self.value = []
		
		num_modes_attempted = p.getState("num_modes_attempted")
		self.elements.append('Modes Attempted: ' + str(num_modes_attempted))
		self.value.append(num_modes_attempted * 4000)
		
		num_modes_completed = p.getState("num_modes_completed")
		self.elements.append('Modes Completed: ' + str(num_modes_completed))
		self.value.append(num_modes_completed * 12000)

		crimescenes_total_levels = p.getState("crimescenes_total_levels")
		self.elements.append('Crimescene Levels: ' + str(crimescenes_total_levels))
		self.value.append(crimescenes_total_levels * 2000)

		self.delay(name='bonus_computer', event_type=None, delay=self.delay_time, handler=self.bonus_computer)
		self.title_layer.set_text('BONUS:', self.delay_time)

	def bonus_computer(self):
		self.game.sound.play('bonus')
		self.title_layer.set_text('')
		self.element_layer.set_text(self.elements[self.step])
		self.value_layer.set_text(str(self.value[self.step]))
		self.total_base += self.value[self.step]
		self.step += 1

		if self.step == len(self.elements) or len(self.elements) == 0:
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
			self.step = 0
		else:
			self.delay(name='bonus_computer', event_type=None, delay=self.delay_time, handler=self.bonus_computer)

	def bonus_finish(self):
		if self.step == 0:
			self.game.sound.play('bonus')
			self.element_layer.set_text('Total Base:')
			self.value_layer.set_text(str(self.total_base))
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		elif self.step == 1:
			self.game.sound.play('bonus')
			self.element_layer.set_text('Multiplier:')
			self.value_layer.set_text(str(self.x))
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		elif self.step == 2:
			self.game.sound.play('bonus')
			total_bonus = self.total_base * self.x
			self.element_layer.set_text('Total Bonus:')
			self.value_layer.set_text(str(total_bonus))
			self.game.score(total_bonus)
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		else:
			self.exit_function()
		self.step += 1

	def sw_flipperLwL_active(self, sw):
		self.delay_time = 0.2

	def sw_flipperLwR_active(self, sw):
		self.delay_time = 0.2

