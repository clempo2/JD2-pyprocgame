from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class Bonus(Mode):
	"""Display end of ball bonus"""
	
	def __init__(self, game, priority):
		super(Bonus, self).__init__(game, priority)
		font_big = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		self.title_layer = TextLayer(128/2, 7, font_big, "center")
		self.name_layer = TextLayer(128/2, 7, font_small, "center")
		self.value_layer = TextLayer(128/2, 20, font_small, "center")
		self.layer = GroupedLayer(128, 32, [self.title_layer, self.name_layer, self.value_layer])

	def compute(self, exit_callback):
		self.game.sound.play('drain')
		self.exit_callback = exit_callback
		self.title_layer.set_text('BONUS', self.delay_time)
		
		p = self.game.current_player()
		num_modes_attempted = p.getState("num_modes_attempted")
		attempted = ['Modes Attempted: ' + str(num_modes_attempted), num_modes_attempted * 4000]
		
		num_modes_completed = p.getState("num_modes_completed")
		completed = ['Modes Completed: ' + str(num_modes_completed), num_modes_completed * 12000]

		crimescenes_total_levels = p.getState("crimescenes_total_levels")
		crimescenes = ['Crimescene Levels: ' + str(crimescenes_total_levels), crimescenes_total_levels * 2000]

		base = attempted[1] + completed[1] + crimescenes[1]
		total_base = ['Total Base:', base]
		
		bonus_x = p.getState('bonus_x')
		multiplier = ['Multiplier:', bonus_x]

		self.total = base * bonus_x
		total_bonus = ['Total Bonus:', self.total]
		
		self.item_index = 0
		self.delay_time = 1
		self.bonus_items = [attempted, completed, crimescenes, total_base, multiplier, total_bonus]
		self.delay(name='show_bonus', event_type=None, delay=self.delay_time, handler=self.show_bonus_item)

	def show_bonus_items(self):
		if self.index == len(self.bonus_items):
			# wait till the end to update score, no bonus if player tilts early
			self.game.score(self.total)
			self.exit_callback()

		self.game.sound.play('bonus')
		
		text, value = self.bonus_items[self.item_index]
		self.name_layer.set_text(text)
		self.value_layer.set_text(str(value))

		self.item_index += 1
		self.delay(name='show_bonus', event_type=None, delay=self.delay_time, handler=self.show_bonus_items)

	def sw_flipperLwL_active(self, sw):
		# speed up
		self.delay_time = 0.2

	def sw_flipperLwR_active(self, sw):
		# skip to total
		self.item_index = len(self.bonus_items) - 1
