import locale
from random import shuffle
from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Scoring_Mode

lamp_colors = ['G', 'Y', 'R', 'W']

class Crimescenes(Scoring_Mode):
	"""Crime scenes mode"""
	
	def __init__(self, game, priority):
		super(Crimescenes, self).__init__(game, priority)
		# we always award the most difficult target that remains in the current level  
		self.target_award_order = [1,3,0,2,4]
		self.extra_ball_level = 4

		difficulty = self.game.user_settings['Gameplay']['Crimescene shot difficulty']
		if difficulty == 'easy':
			self.level_pick_from = [
				[2,4], [2,4], [2,4], [2,4], 
				[0,2,4], [0,2,4], [0,2,4], [0,2,4], [0,2,4], [0,2,4], 
				[0,2,3,4], [0,2,3,4], [0,2,3,4], [0,2,3,4], 
				[0,1,2,3,4], [0,1,2,3,4]
			]
			self.level_num_shots = [ 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5 ]
		elif difficulty == 'medium':
			self.level_pick_from = [
				[2,4], [2,4], [2,4], [2,4], 
				[0,2,4], [0,2,4], [0,2,4], [0,2,4], 
				[0,2,3,4], [0,2,3,4], [0,2,3,4], [0,2,3,4], 
				[0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4]
			]
			self.level_num_shots = [ 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ]
		else:
			self.level_pick_from = [
				[0,2,4], [0,2,4], [0,2,4], [0,2,4], 
				[0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], 
				[0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], 
				[0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4]
			]
			self.level_num_shots = [ 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ]

		self.block_war = BlockWar(game, priority+5)

	# restart crime scenes from the first level
	def reset(self):
		p = self.game.current_player()
		p.setState('crimescenes_level', 0)
		p.setState('crimescenes_mode', 'init')
		p.setState('crimescenes_complete', False)

	def mode_started(self):
		# restore player state
		p = self.game.current_player()
		self.level = p.getState('crimescenes_level', 0)
		self.total_levels = p.getState('crimescenes_total_levels', 0)
		self.mode = p.getState('crimescenes_mode', 'init')
		self.targets = p.getState('crimescenes_targets', None)
		self.complete = p.getState('crimescenes_complete', False)

		self.num_advance_hits = 0
		self.bonus_shot = 0
		self.mb_active = False

		if self.mode == 'init':
			self.init_level(0)

	def mode_stopped(self):
		if not self.complete:
			self.mode = "levels"

		# save player state
		p = self.game.current_player()
		p.setState('crimescenes_level', self.level)
		p.setState('crimescenes_total_levels', self.total_levels)
		p.setState('crimescenes_mode', self.mode)
		p.setState('crimescenes_targets', self.targets)
		p.setState('crimescenes_complete', self.complete)
		
		if self.mode == 'bonus' or self.mode == 'block_war':
			self.cancel_delayed('rotate_bonus_target')
			self.game.modes.remove(self.block_war)

		for i in range(1,6):
			for j in range(0,4):
				lampname = 'perp' + str(i) + lamp_colors[j]
				self.game.drive_lamp(lampname, 'off')

		for i in range(1,5):
			lampname = 'crimeLevel' + str(i)
			self.game.drive_lamp(lampname, 'off')

	def complete(self):
		return self.complete

	def is_multiball_active(self):
		return self.mode == 'block_war' or self.mode == 'bonus'

	def get_status_layers(self):
		tiny_font = self.game.fonts['tiny7']
		title_layer = TextLayer(128/2, 7, tiny_font, "center").set_text('Crime Scenes')
		level_layer = TextLayer(128/2, 16, tiny_font, "center").set_text('Current Level: ' + str(self.level + 1) + '/16')
		block_layer = TextLayer(128/2, 25, tiny_font, "center").set_text('Block War in ' + str(4-(self.level % 4)) + ' levels')
		status_layer = GroupedLayer(128, 32, [title_layer, level_layer, block_layer])
		return [status_layer]

	#
	# Advance Crime Level
	#

	def sw_threeBankTargets_active(self, sw):
		if self.mode == 'levels':
			self.num_advance_hits += 1
			if self.num_advance_hits == 3:	
				self.award_hit()
				self.num_advance_hits = 0
			self.update_lamps()

	def award_hit(self):
		for award_shot in self.target_award_order:
			if self.targets[award_shot]:
				self.switch_hit(award_shot)
				return True

	#
	# Crime Scene Shots
	#

	def init_level(self, level):
		if level >= self.game.user_settings['Gameplay']['Crimescene levels for finale']:
			self.complete = True
			self.crimescenes_completed()
			self.mode = 'complete'
		else:
			# the level consists of num_to_pick many targets chosen among the targets listed in pick_from  
			self.mode = 'levels'
			pick_from = self.level_pick_from[level]
			shuffle(pick_from)

			num_to_pick = self.level_num_shots[level]
			if num_to_pick > len(pick_from):
				raise ValueError("Number of targets necessary for level " + level + " exceeds the list of targets in the template")

			# Now fill targets according to shuffled template
			self.targets = [0] * 5
			for i in range(0, num_to_pick):
				self.targets[pick_from[i]] = 1
		self.update_lamps()

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.switch_hit(1)

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.switch_hit(3)

	def sw_topCenterRollover_active(self, sw):
		#See if ball came around right loop 
		#Give it 2 seconds as ball trickles this way.  Might need to adjust.
		if self.game.switches.topRightOpto.time_since_change() < 2:
			self.switch_hit(3)

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)

	def switch_hit(self, shot):
		if self.mode == 'levels':
			if self.targets[shot]:
				self.targets[shot] = 0
				self.game.score(1000)
				if self.all_targets_hit():
					self.level_complete()
				else:
					self.game.sound.play_voice('crime')
				self.update_lamps()
		elif self.mode == 'block_war':
			block_war_multiplier = self.get_num_modes_completed() + 1
			self.block_war.switch_hit(shot, block_war_multiplier)
			if self.block_war.all_shots_hit():
				self.block_war_round_complete()
			else:
				self.game.sound.play_voice('good shot')
				self.update_lamps()
		elif self.mode == 'bonus':
			if shot == self.bonus_shot:
				self.cancel_delayed('rotate_bonus_target')
				self.bonus_round_collected()

	# return whether all targets making up the current level have been hit
	def all_targets_hit(self):
		return not any(self.targets)

	#
	# Block War
	#

	def block_war_round_complete(self):
		self.game.score(10000)
		self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
		self.start_bonus_round()

	def end_multiball(self):
		self.cancel_delayed('rotate_bonus_target')
		self.game.modes.remove(self.block_war)
		self.mode = 'levels'
		self.level += 1
		self.init_level(self.level)
		self.mb_end_callback()

	#
	# Level Complete
	#

	def level_complete(self):
		self.game.score(10000)
		self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
		self.total_levels += 1
		self.level += 1
		if self.level == self.extra_ball_level:
			self.light_extra_ball_function()

		if (self.level % 4) == 3:
			self.mode = 'block_war'
			self.game.modes.add(self.block_war)
			self.mb_start_callback()
		else:
			self.display_level_complete(self.level,10000)
			self.game.sound.play_voice('block complete ' + str(self.level))
			self.init_level(self.level)

	def display_level_complete(self, level, points):
		title_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], "center").set_text("Advance Crimescene", 1.5);
		level_layer = TextLayer(128/2, 14, self.game.fonts['07x5'], "center").set_text("Level " + str(level) + " complete", 1.5);
		award_layer = TextLayer(128/2, 21, self.game.fonts['07x5'], "center").set_text("Award: " + locale.format("%d",points,True) + " points", 1.5);
		self.layer = GroupedLayer(128, 32, [title_layer, level_layer, award_layer])

	#
	# Bonus Round
	#

	def start_bonus_round(self):
		self.mode = 'bonus'
		self.bonus_shot = 0
		self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=1)
		self.game.sound.play_voice('jackpot is lit')
		self.update_lamps()

	def rotate_bonus_target(self, bonus_step):
		if self.bonus_shot == 5:
			bonus_step = -1
		self.bonus_shot += bonus_step
		if self.bonus_shot == -1:
			self.bonus_round_over(False)
		else:
			self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=bonus_step)
		self.update_lamps()

	def bonus_round_collected(self):
		self.game.score(10000)
		self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
		self.bonus_round_over(True)

	# called when the bonus round is finished because it completed or expired
	def bonus_round_over(self, collect_bonus):
		self.mode = 'block_war'
		self.block_war.next_round(collect_bonus)

	#
	# Lamps
	#

	def update_lamps(self):
		if self.mode == 'block_war':
			self.block_war.update_lamps()
		elif self.mode == 'levels':
			self.update_levels_lamps()
		elif self.mode == 'bonus':
			self.update_bonus_lamps()
		elif self.mode == 'complete':
			self.update_crimescenes_complete_lamps()
		self.update_center_lamps()

	def update_levels_lamps(self):
		styles = ['on', 'slow', 'fast', 'off']
		style = styles[self.num_advance_hits] 
		self.game.drive_lamp('advanceCrimeLevel', style)
			
		for i in range(0, 5):
			lamp_color_num = self.level%4
			for j in range(0, 4):
				lampname = 'perp' + str(i+1) + lamp_colors[j]
				style = 'medium' if self.targets[i] and lamp_color_num == j else 'off'
				self.game.drive_lamp(lampname, style)

	def update_bonus_lamps(self):
		self.game.drive_lamp('advanceCrimeLevel', 'off')
		for i in range(0,5):
			for j in range(1, 4): # skip Green
				lampname = 'perp' + str(i+1) + lamp_colors[j]
				style = 'medium' if self.bonus_shot == i else 'off'
				self.game.drive_lamp(lampname, style)

	def update_crimescenes_complete_lamps(self):
		for i in range(0, 5):
			if self.targets[i]:
				for j in range(0, 4):
					lampname = 'perp' + str(i+1) + lamp_colors[j]
					self.game.drive_lamp(lampname, 'off')

	def update_center_lamps(self):
		# Use 4 center crimescene lamps to indicate block.
		# 4 levels per block.
		for i in range (1,5):
			lampnum = int(self.level / 4) + 1
			lampname = 'crimeLevel' + str(i)
			style = 'on' if i <= lampnum else 'off'
			self.game.drive_lamp(lampname, style)

		
class BlockWar(Mode):
	"""Multiball activated by crime scenes"""

	def __init__(self, game, priority):
		super(BlockWar, self).__init__(game, priority)
		self.countdown_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.score_reason_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], "center")
		self.score_value_layer = TextLayer(128/2, 17, self.game.fonts['07x5'], "center")
		self.anim_layer = self.game.animations['blockwars']
		self.layer = GroupedLayer(128, 32, [self.anim_layer, self.countdown_layer, self.banner_layer, self.score_reason_layer, self.score_value_layer])
	
	def mode_started(self):
		self.banner_layer.set_text("Block War!", 3)
		self.game.sound.play_voice('block war start')
		self.bw_shots = 1
		self.shots_required = [1,1,1,1,1]
		self.game.trough.launch_balls(1, self.start_callback)

	def mode_stopped(self):
		pass

	# trough callback
	def start_callback(self):
		ball_save_time = self.game.user_settings['Gameplay']['Block Wars ballsave time']
		# 1 ball added already from launcher.  So ask ball_save to save
		# new total of balls in play.
		local_num_balls_to_save = self.game.trough.num_balls_in_play
		self.game.ball_save.start(num_balls_to_save=local_num_balls_to_save, time=ball_save_time, now=False, allow_multiple_saves=True)

	def next_round(self, collect_bonus):
		if collect_bonus:
			if self.bw_shots < 4:
				self.bw_shots += 1
			self.bonus_hit()
		self.shots_required = [self.bw_shots] * 5

	def all_shots_hit(self):
		return not any(self.shots_required)

	def switch_hit(self, shot, multiplier):
		if self.shots_required[shot] > 0:
			self.shots_required[shot] -= 1
			score = 5000 * multiplier
			self.score_value_layer.set_text(str(score), 2)
			self.game.score(score)
			self.game.sound.play('block_war_target')
			if self.shots_required[shot] == 0:
				self.score_reason_layer.set_text("Block " + str(shot+1) + " secured!", 2)

	def bonus_hit(self):
		self.banner_layer.set_text("Jackpot!", 2)
		self.game.sound.play_voice('jackpot')
		self.game.score(500000)

	def update_lamps(self):
		self.game.drive_lamp('advanceCrimeLevel', 'off')
		for i in range(0, 5):
			for j in range(0, 4):
				lampname = 'perp' + str(i+1) + lamp_colors[j]
				style = 'medium' if j < self.shots_required[i] else 'off'
				self.game.drive_lamp(lampname, style)
