from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode
from random import randint

class MissileAwardMode(Mode):
	"""Choose an award while the ball sits in the left shooter lane"""
	
	def __init__(self, game, priority, font):
		super(MissileAwardMode, self).__init__(game, priority)
		
		self.title_layer = TextLayer(128/2, 7, font, "center")
		self.element_layer = TextLayer(128/2, 15, font, "center")
		self.value_layer = TextLayer(128/2, 22, font, "center")
		self.layer = GroupedLayer(128, 32, [self.title_layer,self.element_layer, self.value_layer])

		self.title_layer.set_text("Missile Award")
		self.element_layer.set_text("Left Fire btn collects:")
		
		self.initial_awards = ['Light Extra Ball', 'Advance Crimescenes', '30000 Points', 'Bonus +1X', 'Hold Bonus X']
		self.repeatable_award = [False, True, True, True, False]
		self.current_award_ptr = 0

		self.delay_time = 0.200
		self.active = False

	def mode_started(self):
		self.available_awards = self.game.getPlayerState('available_awards', self.initial_awards[:])
		self.rotate_awards()
		self.timer = 70
		self.active = True
		self.delay(name='missile_update', event_type=None, delay=self.delay_time, handler=self.update)

	def mode_stopped(self):
		self.game.setPlayerState('available_awards', self.available_awards)

	def sw_fireL_active(self, sw):
		self.timer = 3

	def update(self):
		if self.timer == 0:
			self.active = False
			self.game.modes.remove(self)
		elif self.timer == 3:
			self.game.coils.shooterL.pulse()
			self.award()
		elif self.timer > 10:
			self.rotate_awards()
			
		if self.timer > 0:
			self.delay(name='missile_update', event_type=None, delay=self.delay_time, handler=self.update)
			self.timer -= 1

	def award(self):
		self.callback(self.available_awards[self.current_award_ptr])
		if not self.repeatable_award[self.current_award_ptr]:
			self.available_awards[self.current_award_ptr] = str(10000*(self.current_award_ptr + 1)) + ' Points'
		
	def rotate_awards(self):
		self.self.current_award_ptr = (self.current_award_ptr + randint(1,4)) % len(self.available_awards)
		self.value_layer.set_text(self.available_awards[self.current_award_ptr])
