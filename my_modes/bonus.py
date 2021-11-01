from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class Bonus(Mode):
	"""Display end of ball bonus"""
	
	def __init__(self, game, priority, font_big, font_small):
		super(Bonus, self).__init__(game, priority)
		self.title_layer = TextLayer(128/2, 7, font_big, "center")
		self.element_layer = TextLayer(128/2, 7, font_small, "center")
		self.value_layer = TextLayer(128/2, 20, font_small, "center")
		self.layer = GroupedLayer(128, 32, [self.title_layer, self.element_layer, self.value_layer])

	def mode_started(self):
		self.delay_time = 1

	def mode_stopped(self):
		pass

	def compute(self, exit_function):
		self.game.sound.play('drain')
		self.exit_function = exit_function
		self.total_base = 0
		
		p = self.game.current_player()
		self.x = p.getState("bonus_x")
		
		self.bonus_items = []
		
		num_modes_attempted = p.getState("num_modes_attempted")
		self.bonus_items.append({'name':'Modes Attempted: ' + str(num_modes_attempted), 'value':num_modes_attempted * 4000})
		
		num_modes_completed = p.getState("num_modes_completed")
		self.bonus_items.append({'name':'Modes Completed: ' + str(num_modes_completed), 'value':num_modes_completed * 12000})

		crimescenes_total_levels = p.getState("crimescenes_total_levels")
		self.bonus_items.append({'name':'Crimescene Levels: ' + str(crimescenes_total_levels), 'value':crimescenes_total_levels * 2000})

		self.delay(name='bonus_items', event_type=None, delay=self.delay_time, handler=self.show_bonus_items, param=0)
		self.title_layer.set_text('BONUS', self.delay_time)

	def show_bonus_items(self, item_index):
		self.game.sound.play('bonus')
		bonus_item = self.bonus_items[self.item_index]
		self.element_layer.set_text(bonus_item['name'])
		self.value_layer.set_text(str(bonus_item['value']))
		self.total_base += self.value[self.item_index]

		if self.step < len(self.bonus_items):
			self.delay(name='bonus_items', event_type=None, delay=self.delay_time, handler=self.show_bonus_items, param=item_index + 1)
		else:
			self.delay(name='bonus_calculation', event_type=None, delay=self.delay_time, handler=self.show_bonus_calculation, param=0)

	def show_bonus_calculation(self, step):
		if step == 3:
			self.exit_function()
			
		self.game.sound.play('bonus')
		if step == 0:
			text = 'Total Base:'
			value = self.total_base
		elif step == 1:
			text = 'Multiplier:'
			value = self.x
		elif step == 2:
			text = 'Total Bonus:'  
			value = self.total_base * self.x
			self.game.score(value)

		self.element_layer.set_text(text)
		self.value_layer.set_text(str(value))
		self.delay(name='bonus_calculation', event_type=None, delay=self.delay_time, handler=self.show_bonus_calculation, param=step + 1)

	def sw_flipperLwL_active(self, sw):
		self.delay_time = 0.2

	def sw_flipperLwR_active(self, sw):
		self.delay_time = 0.2
