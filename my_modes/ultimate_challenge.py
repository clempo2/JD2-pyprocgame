from procgame.dmd import GroupedLayer, MarkupFrameGenerator, PanningLayer, TextLayer
from procgame.game import Mode, SwitchStop
from procgame.modes import Scoring_Mode
from random import shuffle
import locale

class UltimateChallenge(Scoring_Mode):
	"""Wizard mode"""

	def __init__(self, game, priority):
		super(UltimateChallenge, self).__init__(game, priority)
		self.play_ult_intro = UltimateIntro(self.game, self.priority+1)

		self.mode_fire = Fire(game, self.priority+1)
		self.mode_fear = Fear(game, self.priority+1)
		self.mode_mortis = Mortis(game, self.priority+1)
		self.mode_death = Death(game, self.priority+1)
		self.mode_celebration = Celebration(game, self.priority+1)

		self.mode_fire.complete_callback = self.level_complete_callback
		self.mode_fear.complete_callback = self.level_complete_callback
		self.mode_mortis.complete_callback = self.level_complete_callback
		self.mode_death.complete_callback = self.level_complete_callback
		self.mode_celebration.complete_callback = self.level_complete_callback

		self.mode_list = {
			'fire': self.mode_fire,
			'fear': self.mode_fear,
			'mortis': self.mode_mortis,
			'death': self.mode_death,
			'celebration': self.mode_celebration
		}

		self.active_mode = 'fire'
		self.active = False
		self.completed = False

	def mode_started(self):
		self.active_mode = self.game.getPlayerState('challenge_active_mode', 'fire')
		self.game.coils.resetDropTarget.pulse(40)
		self.active = True
		self.begin()

	def mode_stopped(self):
		self.game.setPlayerState('challenge_active_mode', self.active_mode)
		self.game.modes.remove(self.mode_fire)
		self.game.modes.remove(self.mode_fear)
		self.game.modes.remove(self.mode_mortis)
		self.game.modes.remove(self.mode_death)
		self.active = False

	def is_active(self):
		return self.active

	def begin(self):
		self.game.modes.add(self.mode_list[self.active_mode])
		self.game.sound.play_music('mode', loops=-1)

	def register_callback_function(self, function):
		self.callback = function

	def get_instruction_layers(self):
		font = self.game.fonts['tiny7']
		instr_layer1 = TextLayer(128/2, 15, font, "center").set_text('This')
		instr_layer2 = TextLayer(128/2, 15, font, "center").set_text('is')
		instr_layer3 = TextLayer(128/2, 15, font, "center").set_text('the')
		instr_layer4 = TextLayer(128/2, 15, font, "center").set_text('Ultimate')
		instr_layer5 = TextLayer(128/2, 15, font, "center").set_text('Challenge')
		instruction_layers = [[instr_layer1], [instr_layer2], [instr_layer3], [instr_layer4], [instr_layer5]]
		return instruction_layers

	def timer_update(self, timer):
		self.countdown_layer.set_text(str(timer))

	def update_lamps(self):
		pass

	def sw_shooterL_active_for_200ms(self, sw):
		self.game.coils.shooterL.pulse()
		return SwitchStop	

	def level_complete_callback(self):
		self.game.ball_save.disable()
		self.game.sound.fadeout_music()
		self.game.trough.drain_callback = self.complete_drain_callback

	def complete_drain_callback(self):
		if self.game.trough.num_balls_in_play == 0:
			if self.active_mode == 'fire':
				self.game.modes.remove(self.mode_fire)
				self.active_mode = 'mortis'
				self.play_ult_intro.setup('mortis', self.begin)
				self.game.modes.add(self.play_ult_intro)
			elif self.active_mode == 'mortis':
				self.game.modes.remove(self.mode_mortis)
				self.active_mode = 'fear'
				self.play_ult_intro.setup('fear', self.begin)
				self.game.modes.add(self.play_ult_intro)
			elif self.active_mode == 'fear':
				self.game.modes.remove(self.mode_fear)
				self.active_mode = 'death'
				self.play_ult_intro.setup('death', self.begin)
				self.game.modes.add(self.play_ult_intro)
			elif self.active_mode == 'death':
				self.completed = True
				self.game.modes.remove(self.mode_death)
				self.active_mode = 'celebration'
				self.play_ult_intro.setup('celebration', self.begin)
				self.game.modes.add(self.play_ult_intro)
			# Can get here if in celebration and last balls drain at the same time.
			elif self.active_mode == 'celebration':
				self.game.modes.remove(self.mode_celebration)
				self.game.base_game_mode.ball_drained_callback()
				
			self.game.enable_flippers(True)
			self.game.trough.drain_callback = self.game.base_game_mode.ball_drained_callback
		elif self.game.trough.num_balls_in_play == 1:
			if self.active_mode == 'celebration':
				self.game.modes.remove(self.mode_celebration)
				self.game.trough.drain_callback = self.game.base_game_mode.ball_drained_callback
				self.callback()


class UltimateIntro(Mode):
	"""Display wizard mode instructions"""
	def __init__(self, game, priority):
		super(UltimateIntro, self).__init__(game, priority)
		self.gen = MarkupFrameGenerator()
		self.delay_time = 5
		self.exit_function = None
		self.instructions = self.gen.frame_for_markup("") # empty

	def mode_started(self):
		self.game.sound.stop_music()
		self.game.enable_flippers(False) 
		self.game.enable_gi(False)
		self.game.lamps.rightStartFeature.disable()
		self.game.lamps.ultChallenge.pulse(0)
		self.game.disable_drops()

		self.layer = PanningLayer(width=128, height=32, frame=self.instructions, origin=(0,0), translate=(0,1), bounce=False)
		self.delay(name='finish', event_type=None, delay=self.delay_time, handler=self.finish )

	def mode_stopped(self):
		self.cancel_delayed('intro')
		# Leave GI off for Ultimate Challenge
		self.game.enable_flippers(True) 

	def setup(self, stage, exit_function):
		self.exit_function = exit_function
		self.stage = stage

		if stage == 'fire':
			self.delay_time = 15
			self.instructions = self.gen.frame_for_markup("""

#ULTIMATE#
#CHALLENGE#

Defeat the Dark Judges

Stage 1

Judge Fire is creating chaos by lighting fires all over Mega City One.

Extinguish fires and banish Judge Fire by shooting the lit crimescene shots.

4 ball multiball.  No ball save.
""")

		elif stage == 'mortis':
			self.delay_time = 11.5
			self.instructions = self.gen.frame_for_markup("""

#ULTIMATE#
#CHALLENGE#

Stage 2

Judge Mortis is spreading disease throughout the city.

Banish him by shooting each lit shot twice.

2 ball multiball with temporary ball save.
""")

		elif stage == 'fear':
			self.delay_time = 13
			self.instructions = self.gen.frame_for_markup("""

#ULTIMATE#
#CHALLENGE#

Stage 3

Judge Fear is reigning terror on the city.

Banish him by shooting the lit ramp shots and then the subway before time runs out.

1 ball with temporary ball save.
""")

		elif stage == 'death':
			self.delay_time = 13
			self.instructions = self.gen.frame_for_markup("""

#ULTIMATE#
#CHALLENGE#

Stage 4

Judge Death is on a murder spree.

Banish him by shooting the lit crimescene shots before time expires.  Shots slowly re-light so finish him quickly.

1 ball with temporary ball save.
""")

		else:
			self.delay_time = 8
			self.instructions = self.gen.frame_for_markup("""

#CONGRATS#

The Dark Judges have all been banished.

Enjoy a 6-ball celebration multiball.  All shots score.

Normal play resumes when only 1 ball remains.
""")

	def sw_flipperLwL_active(self, sw):
		self.finish()

	def sw_flipperLwR_active(self, sw):
		self.finish()

	def finish(self):
		self.game.modes.remove(self)
		if self.exit_function:
			self.exit_function()


class Fire(Scoring_Mode):
	"""Dark judge Fire wizard mode"""
	def __init__(self, game, priority):
		super(Fire, self).__init__(game, priority)
		self.complete = False
		self.mystery_lit = True

	def mode_started(self):
		self.mystery_lit = True
		self.game.coils.flasherFire.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.targets = [1,1,1,1,1]
		self.lamp_colors = ['G', 'Y', 'R', 'W']
		self.update_lamps()
		self.complete = False
		if self.game.deadworld.num_balls_locked == 1:
			balls_to_launch = 2
			self.game.deadworld.eject_balls(1)
		elif self.game.deadworld.num_balls_locked == 2:
			balls_to_launch = 1
			self.game.deadworld.eject_balls(2)
		else:
			balls_to_launch = 3

		self.game.trough.launch_balls(balls_to_launch, self.launch_callback)
		self.delay(name='taunt_timer', event_type=None, delay=5, handler=self.taunt)

	def taunt(self):
		self.game.sound.play_voice('fire - taunt')
		self.delay(name='taunt_timer', event_type=None, delay=10, handler=self.taunt)

	def launch_callback(self):
		#ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']
		#self.game.ball_save.start(num_balls_to_save=6, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.cancel_delayed('taunt')
		self.game.coils.flasherFire.disable()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			self.cancel_delayed('taunt')
			self.callback()

	def update_lamps(self):
		for i in range(0,5):
			for j in range(0,4):
				lampname = 'perp' + str(i+1) + self.lamp_colors[j]
				if self.targets[i]:
					self.game.drive_lamp(lampname, 'medium')
				else:
					self.game.drive_lamp(lampname, 'off')
		if self.complete:
			self.game.coils.flasherFire.disable()

		if self.mystery_lit:
			self.game.drive_lamp('mystery', 'on')
		else:
			self.game.drive_lamp('mystery', 'off')

		return True

	def sw_mystery_active(self, sw):
		self.game.sound.play('mystery')
		if self.mystery_lit:
			self.mystery_lit = False
			self.game.set_status('Add 2 balls!')
			self.game.trough.launch_balls(2, self.launch_callback)
		return SwitchStop

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return SwitchStop

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1:
			self.switch_hit(1)

		return SwitchStop

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return SwitchStop

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.switch_hit(3)
		return SwitchStop

	def sw_topCenterRollover_active(self, sw):
		#See if ball came around right loop 
		#Give it 2 seconds as ball trickles this way.  Might need to adjust.
		if self.game.switches.topRightOpto.time_since_change() < 2:
			self.switch_hit(3)
		return SwitchStop

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)
		return SwitchStop

	def switch_hit(self, num):
		if self.targets[num]:
			self.targets[num] = 0
			self.target_hit(num)
			if self.all_targets_hit():
				self.finish()
			self.update_lamps()

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def target_hit(self, num):
		self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
		self.game.score(10000)

	def all_targets_hit(self):
		for i in range(0,5):
			if self.targets[i]:
				return False
		return True

	def finish(self):
		self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Fire Defeated!')
		self.game.coils.flasherFire.disable()
		self.game.lamps.ultChallenge.disable()
		self.game.enable_flippers(False)
		self.mystery_lit = False
		self.update_lamps()
		self.complete = True
		self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.


class Fear(Scoring_Mode):
	"""Dark judge Fear wizard mode"""
	def __init__(self, game, priority):
		super(Fear, self).__init__(game, priority)
		self.complete = False
		self.mystery_lit = True
		self.countdown_layer = TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text('Fear')
		self.score_layer = TextLayer(128/2, 10, self.game.fonts['num_14x10'], "center")
		self.status_layer = TextLayer(128/2, 26, self.game.fonts['tiny7'], "center")
		self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

	def mode_started(self):
		self.state = 'ramps'
		self.ramp_shots_required = 4
		self.ramp_shots_hit = 0
		self.active_ramp = 'left'
		self.timer = 20
		self.mystery_lit = True
		self.update_lamps()
		self.complete = False
		if self.game.switches.popperR.is_inactive():
			self.game.trough.launch_balls(1, self.launch_callback)
		self.game.coils.flasherFear.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.already_collected = False
		self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
		self.delay(name='taunt_timer', event_type=None, delay=5, handler=self.taunt)

	def launch_callback(self):
		ball_save_time = 10
		self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.cancel_delayed('taunt')
		self.game.coils.flasherFire.disable()

	def taunt(self):
		self.game.sound.play_voice('fear - taunt')
		self.delay(name='taunt_timer', event_type=None, delay=10, handler=self.taunt)

	def update_lamps(self):
		if self.mystery_lit:
			self.game.drive_lamp('mystery', 'on')
		else:
			self.game.drive_lamp('mystery', 'off')

		if self.state == 'finished':
			self.game.coils.flasherFear.disable()
			self.game.coils.flasherPursuitR.disable()
			self.game.coils.flasherPursuitL.disable()
			self.game.lamps.pickAPrize.disable()
			self.game.lamps.awardSafecracker.disable()
			self.game.lamps.awardBadImpersonator.disable()
			self.game.lamps.multiballJackpot.disable()
		elif self.state == 'ramps':
			if self.active_ramp == 'left':
				self.game.coils.flasherPursuitL.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
				self.game.coils.flasherPursuitR.disable()
			else:
				self.game.coils.flasherPursuitR.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
				self.game.coils.flasherPursuitL.disable()
		else:
			if self.game.switches.dropTargetD.is_inactive():
				self.game.lamps.dropTargetD.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			else:
				self.game.lamps.dropTargetD.disable()
			self.game.coils.flasherPursuitR.disable()
			self.game.lamps.pickAPrize.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			self.game.lamps.awardSafecracker.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			self.game.lamps.awardBadImpersonator.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			self.game.lamps.multiballJackpot.schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
			
		return True

	def sw_mystery_active(self, sw):
		self.game.sound.play('mystery')
		if self.mystery_lit:
			self.timer = 20
			self.mystery_lit = False
		return SwitchStop

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return SwitchStop

	def sw_leftRampExit_active(self, sw):
		if self.state == 'ramps':
			if self.active_ramp == 'left':
				self.ramp_shots_hit += 1
				self.ramp_shot_hit()
		return SwitchStop

	def sw_rightRampExit_active(self, sw):
		if self.state == 'ramps':
			if self.active_ramp == 'right':
				self.ramp_shots_hit += 1
				self.ramp_shot_hit()
		return SwitchStop

	def sw_popperR_active_for_300ms(self, sw):
		return SwitchStop

	def ramp_shot_hit(self):
		if self.ramp_shots_hit == self.ramp_shots_required:
			self.state = 'subway'
		else:
			self.switch_ramps()
		self.timer = 20
		self.update_lamps()

	def switch_ramps(self):
		self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
		self.game.score(10000)
		if self.active_ramp == 'left':
			self.active_ramp = 'right'
		else:
			self.active_ramp = 'left'

	def sw_dropTargetD_inactive_for_400ms(self, sw):
		if self.state == 'subway':
			self.game.coils.tripDropTarget.pulse(60)

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		if self.state == 'ramps':
			self.drop_targets()
		else:
			self.update_lamps()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		if self.state != 'subway':
			self.game.coils.resetDropTarget.pulse(40)
		return True

	def sw_subwayEnter1_closed(self, sw):
		if self.state == 'subway':
			self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
			self.game.score(10000)
			self.finish()
			self.cancel_delayed(['grace', 'countdown'])
			self.already_collected = True
		return SwitchStop
	
	# Ball might jump over first switch.  Use 2nd switch as a catchall.
	def sw_subwayEnter2_closed(self, sw):
		if self.state == 'subway' and not self.already_collected:
			self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
			self.game.score(10000)
			self.banner_layer.set_text('Well Done!')
			self.finish()
			self.cancel_delayed(['grace', 'countdown'])
		return SwitchStop

	def finish(self, success = True):
		self.cancel_delayed('taunt')
		self.state = 'finished'
		self.game.enable_flippers(False)
		self.update_lamps()
		self.game.lamps.ultChallenge.disable()
		if success:
			self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Fear Defeated!')
			self.complete = True
			self.complete_callback()
		else:
			self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('You lose!')
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

	def mode_tick(self):
		score = self.game.current_player().score
		if score == 0:
			self.score_layer.set_text('00')
		else:
			self.score_layer.set_text(locale.format("%d",score,True))

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
			self.countdown_layer.set_text(str(self.timer))
		else:
			self.finish(False)


class Mortis(Scoring_Mode):
	"""Dark judge Mortis wizard mode"""
	def __init__(self, game, priority):
		super(Mortis, self).__init__(game, priority)
		self.complete = False

	def mode_started(self):
		self.state = 'ramps'
		self.shots_required = [2, 2, 2, 2, 2]
		self.update_lamps()
		self.complete = False
		if self.game.switches.popperR.is_active():
			self.game.trough.launch_balls(1, self.launch_callback)
		else:
			self.game.trough.launch_balls(2, self.launch_callback)
		self.game.coils.flasherMortis.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.already_collected = False
		self.delay(name='taunt_timer', event_type=None, delay=5, handler=self.taunt)

	def taunt(self):
		self.game.sound.play_voice('mortis - taunt')
		self.delay(name='taunt_timer', event_type=None, delay=10, handler=self.taunt)

	def launch_callback(self):
		ball_save_time = 20
		self.game.ball_save.start(num_balls_to_save=2, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.cancel_delayed('taunt')
		self.game.coils.flasherMortis.disable()

	def update_lamps(self):
		self.drive_shot_lamp(0, 'mystery')
		self.drive_shot_lamp(1, 'perp1W')
		self.drive_shot_lamp(1, 'perp1R')
		self.drive_shot_lamp(1, 'perp1Y')
		self.drive_shot_lamp(1, 'perp1G')
		self.drive_shot_lamp(2, 'perp3W')
		self.drive_shot_lamp(2, 'perp3R')
		self.drive_shot_lamp(2, 'perp3Y')
		self.drive_shot_lamp(2, 'perp3G')
		self.drive_shot_lamp(3, 'perp5W')
		self.drive_shot_lamp(3, 'perp5R')
		self.drive_shot_lamp(3, 'perp5Y')
		self.drive_shot_lamp(3, 'perp5G')
		self.drive_shot_lamp(4, 'stopMeltdown')
		return True

	def drive_shot_lamp(self, index, lampname):
		req_shots = self.shots_required[index]
		if req_shots == 0:
			self.game.lamps[lampname].disable()
		elif req_shots == 1:
			self.game.lamps[lampname].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		else:
			self.game.lamps[lampname].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)

	def sw_mystery_active(self, sw):
		self.switch_hit(0)
		return SwitchStop

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(1)
		return SwitchStop

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return SwitchStop

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(3)
		return SwitchStop

	def sw_captiveBall3_active(self, sw):
		self.switch_hit(4)
		return SwitchStop

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return SwitchStop

	def switch_hit(self, index):
		if self.shots_required[index] > 0:
			self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
			self.game.score(10000)
			self.shots_required[index] -= 1
			self.update_lamps()
			self.check_for_completion()

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def check_for_completion(self):
		for i in range(0,5):
			if self.shots_required[i] > 0:
				return False
		self.finish()

	def finish(self, success = True):
		self.cancel_delayed('taunt')
		self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Mortis Defeated!')
		self.state = 'finished'
		self.game.enable_flippers(False)

		for lamp in ['perp1W', 'perp1R', 'perp1Y', 'perp1G', 'perp3W', 'perp3R', 'perp3Y', 'perp3G', 
		             'perp5W', 'perp5R', 'perp5Y', 'perp5G', 'mystery', 'stopMeltdown', 'ultChallenge']: 
			self.game.lamps[lamp].disable()

		self.game.coils.flasherMortis.disable()

		if success:
			self.complete = True
			self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.


class Death(Scoring_Mode):
	"""Dark judge Death wizard mode"""
	def __init__(self, game, priority):
		super(Death, self).__init__(game, priority)
		self.complete = False
		self.countdown_layer = TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text('Death')
		self.score_layer = TextLayer(128/2, 10, self.game.fonts['num_14x10'], "center")
		self.status_layer = TextLayer(128/2, 26, self.game.fonts['tiny7'], "center")
		self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

	def mode_started(self):
		self.current_shot_index = 0
		self.total_timer = 180
		self.timer = 10
		self.active_shots = [1, 1, 1, 1, 1]
		self.shot_order = [4,2,0,3,1]
		self.update_lamps()
		self.complete = False
		if self.game.switches.popperR.is_inactive():
			self.game.trough.launch_balls(1, self.launch_callback)
		self.game.coils.flasherDeath.schedule(schedule=0x80808080, cycle_seconds=0, now=True)
		self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
		self.already_collected = False
		self.game.coils.resetDropTarget.pulse(40)
		self.delay(name='taunt_timer', event_type=None, delay=5, handler=self.taunt)

	def taunt(self):
		self.game.sound.play_voice('death - taunt')
		self.delay(name='taunt_timer', event_type=None, delay=10, handler=self.taunt)

	def launch_callback(self):
		ball_save_time = 20
		self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.cancel_delayed('taunt')
		self.game.coils.flasherDeath.disable()

	def update_lamps(self):
		self.drive_shot_lamp(0, 'perp1W')
		self.drive_shot_lamp(0, 'perp1R')
		self.drive_shot_lamp(0, 'perp1Y')
		self.drive_shot_lamp(0, 'perp1G')
		self.drive_shot_lamp(1, 'perp2W')
		self.drive_shot_lamp(1, 'perp2R')
		self.drive_shot_lamp(1, 'perp2Y')
		self.drive_shot_lamp(1, 'perp2G')
		self.drive_shot_lamp(2, 'perp3W')
		self.drive_shot_lamp(2, 'perp3R')
		self.drive_shot_lamp(2, 'perp3Y')
		self.drive_shot_lamp(2, 'perp3G')
		self.drive_shot_lamp(3, 'perp4W')
		self.drive_shot_lamp(3, 'perp4R')
		self.drive_shot_lamp(3, 'perp4Y')
		self.drive_shot_lamp(3, 'perp4G')
		self.drive_shot_lamp(4, 'perp5W')
		self.drive_shot_lamp(4, 'perp5R')
		self.drive_shot_lamp(4, 'perp5Y')
		self.drive_shot_lamp(4, 'perp5G')
		return True

	def drive_shot_lamp(self, index, lampname):
		if self.active_shots[index] == 0:
			self.game.lamps[lampname].disable()
		else:
			self.game.lamps[lampname].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)

	def sw_mystery_active(self, sw):
		self.switch_hit(0)
		return SwitchStop

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.switch_hit(1)

		return SwitchStop

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)
		return SwitchStop

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.switch_hit(3)

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)
		return SwitchStop

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return SwitchStop

	def switch_hit(self, index):
		if self.active_shots[index]:
			self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
			self.game.score(10000)
			self.active_shots[index] = 0
			self.timer += 10
			self.check_for_completion()
			self.update_lamps()

	def add_shot(self):
		for i in range(0, 5):
			if not self.active_shots[self.shot_order[i]]:
				self.active_shots[self.shot_order[i]] = 1
				break
		self.update_lamps()

	def sw_dropTargetJ_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		self.drop_targets()

	def drop_targets(self):
		self.game.coils.resetDropTarget.pulse(40)
		return True

	def check_for_completion(self):
		for i in range(0,5):
			if self.active_shots[i]:
				return False
		self.finish()

	def finish(self, success = True):
		self.cancel_delayed('taunt')
		self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], "center", True).set_text('Death Defeated!')
		self.cancel_delayed('countdown')
		self.game.enable_flippers(False)

		for lamp in ['perp1W', 'perp1R', 'perp1Y', 'perp1G', 'perp3W', 'perp3R', 'perp3Y', 'perp3G', 
		             'perp5W', 'perp5R', 'perp5Y', 'perp5G', 'mystery', 'stopMeltdown', 'ultChallenge']: 
			self.game.lamps[lamp].disable()

		self.game.coils.flasherDeath.disable()

		if success:
			self.complete = True
			self.complete_callback()
		
		# Call callback back to ult-challenge.
		# in ult-challenge, change trough callback so that mode can 
		# transition when all balls drain.  It should keep track of 
		# original callback so it can replace it while modes are active.

	def mode_tick(self):
		score = self.game.current_player().score
		if score == 0:
			self.score_layer.set_text('00')
		else:
			self.score_layer.set_text(locale.format("%d",score,True))

	def decrement_timer(self):
		if self.total_timer == 0:
			self.finish(False)
		elif self.timer > 0:
			self.timer -= 1
			self.total_timer -= 1
			self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
			self.countdown_layer.set_text(str(self.total_timer))
		else:
			self.add_shot()
			self.timer = 10
			self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)


class Celebration(Scoring_Mode):
	"""Final multiball wizard mode after all dark judges have been defeated"""
	def __init__(self, game, priority):
		super(Celebration, self).__init__(game, priority)

	def mode_started(self):
		# Call callback now to set up drain callback, which will decide
		# when multiball should end... probably when 1 ball is left.
		self.complete_callback()

		if self.game.deadworld.num_balls_locked == 1:
			balls_to_launch = 5
			self.game.deadworld.eject_balls(1)
		elif self.game.deadworld.num_balls_locked == 2:
			balls_to_launch = 4
			self.game.deadworld.eject_balls(2)
		else:
			balls_to_launch = 6

		self.game.trough.launch_balls(balls_to_launch, self.launch_callback)
		self.update_lamps()

	def launch_callback(self):
		ball_save_time = 20
		self.game.ball_save.start(num_balls_to_save=6, time=ball_save_time, now=False, allow_multiple_saves=True)
		pass

	def mode_stopped(self):
		self.game.coils.flasherDeath.disable()
		for lamp in self.game.lamps:
			if lamp.name.startswith('gi0'):
				lamp.pulse(0)
			else:
				lamp.disable()

	def update_lamps(self):
		for lamp in self.game.lamps:
			if lamp.name.find('gi0', 0) != -1:
				lamp.pulse(0)

		lamp_schedules = []
		for i in range(0,32):
			lamp_schedules.append(0xffff0000 >> i)
			if i > 16:
				lamp_schedules[i] = (lamp_schedules[i] | (0xffff << (32-(i-16)))) & 0xffffffff

		shuffle(lamp_schedules)
		i = 0
		for lamp in self.game.lamps:
			if lamp.name.find('gi0', 0) == -1 and \
					lamp.name != 'startButton' and lamp.name != 'buyIn' and \
					lamp.name != 'drainShield' and lamp.name != 'superGame' and \
					lamp.name != 'judgeAgain': 
				lamp.schedule(schedule=lamp_schedules[i%32], cycle_seconds=0, now=False)
				i += 1

		return True

	def sw_mystery_active(self, sw):
		self.game.score(5000)
		return SwitchStop

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		if self.game.switches.leftRollover.time_since_change() < 1:
			self.game.score(5000)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.game.score(5000)

		return SwitchStop

	def sw_popperR_active_for_300ms(self, sw):
		self.game.score(1000)
		return SwitchStop

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1.5:
			self.game.score(5000)

	def sw_rightRampExit_active(self, sw):
		self.game.score(1000)
		return SwitchStop

	def sw_leftRampToLock_active(self, sw):
		self.game.deadworld.eject_balls(1)
		return SwitchStop

	def sw_dropTargetJ_active_for_250ms(self,sw):
		return self.drop_targets()

	def sw_dropTargetU_active_for_250ms(self,sw):
		return self.drop_targets()

	def sw_dropTargetD_active_for_250ms(self,sw):
		return self.drop_targets()

	def sw_dropTargetG_active_for_250ms(self,sw):
		return self.drop_targets()

	def sw_dropTargetE_active_for_250ms(self,sw):
		return self.drop_targets()

	def drop_targets(self):
		self.game.score(1000)
		self.game.coils.resetDropTarget.pulse(40)
		return True

