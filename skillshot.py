import locale
from procgame import *
	
class SkillShot(game.Mode):
	"""Skillshot when the ball starts"""
	def __init__(self, game, priority):
		super(SkillShot, self).__init__(game, priority)
		self.text_layer = dmd.TextLayer(128/2, 7, self.game.fonts['07x5'], "center")
		self.award_layer = dmd.TextLayer(128/2, 17, self.game.fonts['num_14x10'], "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.text_layer, self.award_layer])
	
	def mode_started(self):
		self.shots_hit = 0
		self.update_lamps()

	def begin(self):
		self.delay(name='skill_shot_delay', event_type=None, delay=7.0, handler=self.skill_shot_expired)
		self.update_lamps()

	def update_lamps(self):
		self.game.lamps.perp4W.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		self.game.lamps.perp4R.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		self.game.lamps.perp4Y.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		self.game.lamps.perp4G.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def award(self):
		self.game.sound.stop('good shot')
		self.game.sound.play('good shot')
		self.shots_hit += 1
		score = self.shots_hit * 5000
		self.game.score(score)
		self.text_layer.set_text("Skill Shot!",3)
		self.award_layer.set_text(locale.format("%d",score,True),3)
		self.cancel_delayed('skill_shot_delay')
		self.delay(name='skill_shot_delay', event_type=None, delay=3.0, handler=self.skill_shot_expired)
		self.update_lamps()

	def skill_shot_expired(self):
		# timer expired or external caller cancels the skillshot (for example after a ball save)
		self.cancel_delayed('skill_shot_delay')
		self.game.lamps.perp4W.disable()
		self.game.lamps.perp4R.disable()
		self.game.lamps.perp4Y.disable()
		self.game.lamps.perp4G.disable()
		self.game.modes.remove(self)	

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1:
			self.award()
