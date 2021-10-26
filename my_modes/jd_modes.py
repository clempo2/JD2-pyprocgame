import locale
from procgame.dmd import AnimatedLayer, GroupedLayer, PanningLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Scoring_Mode
from chain import Chain
from crimescenes import Crimescenes
from ultimate_challenge import UltimateChallenge, UltimateIntro
from multiball import Multiball
from boring import Boring
from skillshot import SkillShot
from info import Info
from missile_award import MissileAwardMode
from shooting_gallery import ShootingGallery

class JD_Modes(Scoring_Mode):
	"""Controls playable modes"""
	
	def __init__(self, game, priority, font_small, font_big):
		super(JD_Modes, self).__init__(game, priority)

		self.cow_video_mode_lit = False # TODO: this should be a game settings

		# Instantiate sub-modes
		self.game_intro = GameIntro(self.game, self.priority+1)
		self.info = Info(game, priority+20)
		self.info.callback = self.info_ended
		self.boring = Boring(self.game, self.priority+1)
		self.skill_shot = SkillShot(self.game, priority + 5)
		self.chain = Chain(self.game, self.priority)
		
		self.crimescenes = Crimescenes(game, priority+1)
		self.crimescenes.get_block_war_multiplier = lambda: self.num_modes_completed
		self.crimescenes.crimescenes_completed = self.crimescenes_completed
		self.crimescenes.mb_start_callback = self.multiball_started
		self.crimescenes.mb_end_callback = self.multiball_ended
		self.crimescenes.light_extra_ball_function = self.light_extra_ball

		self.multiball = Multiball(self.game, priority + 1, self.game.user_settings['Machine']['Deadworld mod installed'], font_big)
		self.multiball.start_callback = self.multiball_started
		self.multiball.end_callback = self.multiball_ended

		self.video_mode = ShootingGallery(self.game, priority+11, self.cow_video_mode_lit)
		self.video_mode.on_complete = self.video_mode_complete
		
		self.missile_award_mode = MissileAwardMode(game, priority+10, font_small)
		self.missile_award_mode.callback = self.award_missile_award

		self.play_ult_intro = UltimateIntro(self.game, self.priority+1)
		self.ultimate_challenge = UltimateChallenge(game, priority+10)
		self.ultimate_challenge.callback = self.ultimate_challenge_over
		
		self.low_priority_display = ModesDisplay(self.game, priority)
		self.mid_priority_display = ModesDisplay(self.game, priority + 3)
		self.high_priority_display = ModesDisplay(self.game, priority + 200)
		self.low_priority_animation = ModesAnimation(self.game, priority)
		self.mid_priority_animation = ModesAnimation(self.game, priority + 4)
		self.high_priority_animation = ModesAnimation(self.game, priority + 210)

	def reset_modes(self):
		self.state = 'idle'
		self.chain.reset()
		self.crimescenes.reset()
		self.multiball.reset_jackpot_collected()
		self.game.update_lamps()

	def mode_started(self):
		# restore player state
		p = self.game.current_player()
		self.state = p.getState('state', 'idle')
		self.supergame = p.getState('supergame', self.game.supergame)
		self.mystery_lit = p.getState('mystery_lit', False)
		self.missile_award_lit = p.getState('missile_award_lit', False)
		self.video_mode_lit = p.getState('video_mode_lit', True)
		self.extra_balls_lit = p.getState('extra_balls_lit', 0)
		self.total_extra_balls_lit = p.getState('total_extra_balls_lit', 0)
		self.best_inner_loops = p.getState('best_inner_loops', 0)
		self.best_outer_loops = p.getState('best_outer_loops', 0)
		self.bonus_x = p.getState('bonus_x', 1) if p.getState('hold_bonus_x', False) else 1
		self.hold_bonus_x = False

		# disable auto-plunging for the start of ball
		# Force player to hit the right Fire button.
		self.auto_plunge = False

		self.ball_starting = True
		self.skill_shot_added = False
		self.info_on = False
		self.intro_playing = False
		self.outer_loop_active = False
		self.inner_loop_active = False
		self.inner_loop_combos = 0
		self.outer_loop_combos = 0
		self.mystery_lit = True
		self.tilt = False

		# Add modes that are always active
		self.game.modes.add(self.chain)
		self.game.modes.add(self.crimescenes)
		self.game.modes.add(self.multiball)
		self.game.modes.add(self.low_priority_display)
		self.game.modes.add(self.mid_priority_display)
		self.game.modes.add(self.high_priority_display)
		self.game.modes.add(self.low_priority_animation)
		self.game.modes.add(self.mid_priority_animation)
		self.game.modes.add(self.high_priority_animation)

		self.missile_award_lit_save = self.missile_award_lit
		self.setup_next_mode(True)

		for flasher in ['flasherFear', 'flasherMortis', 'flasherDeath', 'flasherFire']:
			self.game.coils[flasher].disable()
		self.game.enable_gi(True)
		self.game.update_lamps()

	def mode_stopped(self):
		# Remove modes from the mode Q
		self.game.modes.remove(self.boring)
		self.game.modes.remove(self.skill_shot)
		self.game.modes.remove(self.chain)
		self.game.modes.remove(self.crimescenes)
		self.game.modes.remove(self.multiball)
		self.game.modes.remove(self.ultimate_challenge)
		self.game.modes.remove(self.low_priority_display)
		self.game.modes.remove(self.mid_priority_display)
		self.game.modes.remove(self.high_priority_display)
		self.game.modes.remove(self.low_priority_animation)
		self.game.modes.remove(self.mid_priority_animation)
		self.game.modes.remove(self.high_priority_animation)
		self.game.modes.remove(self.mode_completed_hurryup)

		# Disable all flashers.
		for coil in self.game.coils:
			if coil.name.startswith('flasher', 0) != -1:
				coil.disable()

		self.cancel_delayed('inner_loop')
		self.cancel_delayed('outer_loop')

		# save player state
		p = self.game.current_player()
		p.setState('state', self.state)
		p.setState('supergame', self.supergame)
		p.setState('video_mode_lit', self.video_mode_lit)
		p.setState('mystery_lit', self.mystery_lit)
		p.setState('missile_award_lit', self.missile_award_lit or self.missile_award_lit_save)
		p.setState('extra_balls_lit', self.extra_balls_lit)
		p.setState('total_extra_balls_lit', self.total_extra_balls_lit)
		p.setState('best_inner_loops', self.best_inner_loops)
		p.setState('best_outer_loops', self.best_outer_loops)
		p.setState('bonus_x', self.bonus_x)
		p.setState('hold_bonus_x', self.hold_bonus_x)

	def sw_popperR_active_for_200ms(self, sw):
		if not self.any_multiball_active():
			if self.state == 'idle':
				self.chain.start_chain_mode()
			elif self.state == 'pre_ultimate_challenge':
				self.start_ultimate_challenge()
			else:
				self.popperR_eject()
		else:
			self.popperR_eject()
		self.game.update_lamps()

	# called right after a mode has ended
	# show next available mode if no mode is currently running
	def setup_next_mode(self, after_multiball=False):
		if self.supergame:
			self.start_ultimate_challenge()
		elif not self.any_multiball_active():
			# all multiballs finished so we can decide what happens next
			self.game.sound.fadeout_music()
			self.game.sound.play_music('background', loops=-1)
			
			if after_multiball:
				# last concurrent multiball just ended
				self.restore_missile_award()

			if self.is_ultimate_challenge_ready():
				# congratulations, you have reached the finale!
				self.state = 'pre_ultimate_challenge'
				self.game.lamps.ultChallenge.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			elif len(self.chain.modes_not_attempted) > 0:
				# TODO: move this code to chain.py somehow
				# offer next available mode
				self.state = 'idle'
				self.game.drive_lamp(self.chain.modes_not_attempted[self.chain.modes_not_attempted_ptr].lamp_name,'slow')
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			else:
				# all modes attempted, let the player finish the other ultimate challenge requirements 
				self.state = 'modes_complete'

	def crimescenes_completed(self):
		self.setup_next_mode(True)

	#
	# Display
	#
	
	def show_on_display(self, text=None, score=None, priority='low'):
		if priority == 'low':
			self.low_priority_display.display(text,score)
		elif priority == 'mid':
			self.mid_priority_display.display(text,score)
		elif priority == 'high':
			self.high_priority_display.display(text,score)

	def play_animation(self, anim, priority='low', repeat=False, hold=False, frame_time=1):
		if priority == 'low':
			self.low_priority_animation.play(anim, repeat, hold, frame_time)
		elif priority == 'mid':
			self.mid_priority_animation.play(anim, repeat, hold, frame_time)
		elif priority == 'high':
			self.high_priority_animation.play(anim, repeat, hold, frame_time)

	def welcome(self):
		if self.game.ball == 1 or self.game.shooting_again:
			self.game.modes.add(self.game_intro)

	def high_score_mention(self):
		if self.game.ball == self.game.balls_per_game:
			if self.replay.replay_achieved[0]:
				text = 'Highest Score'
				score = str(self.game.game_data['ClassicHighScoreData'][0]['inits']) + locale.format("  %d",self.game.game_data['ClassicHighScoreData'][0]['score'],True)
			else:
				text = 'Replay'
				score = locale.format("%d", self.replay.replay_scores[0], True)
			self.show_on_display(text, score, 'high')

	#
	# Instant Info
	#

	def sw_flipperLwL_active_for_6s(self, sw):
		if not self.any_multiball_active() and not self.info_on:
			self.start_info()

	def sw_flipperLwR_active_for_6s(self, sw):
		if not self.any_multiball_active() and not self.info_on:
			self.start_info()
	
	def start_info(self):
		self.info_on = True
		info_layers = self.get_info_layers()
		info_layers.extend(self.chain.get_info_layers())
		info_layers.extend(self.crimescenes.get_info_layers())
		self.info.set_layers(info_layers)
		self.game.modes.add(self.info)

	def get_info_layers(self):
		title_layer = TextLayer(128/2, 9, self.game.fonts['tiny7'], "center").set_text('Extra Balls:')
		item_layer = TextLayer(128/2, 19, self.game.fonts['tiny7'], "center").set_text(str(self.game.current_player().extra_balls))
		info_layer = GroupedLayer(128, 32, [title_layer, item_layer])
		return [info_layer]

	def info_ended(self):
		self.game.modes.remove(self.info)
		self.info_on = False

	#
	# Drop Targets
	#

	def sw_dropTargetJ_active(self, sw):
		self.game.sound.play('drop_target')
		self.game.score(200)

	def sw_dropTargetU_active(self, sw):
		self.game.sound.play('drop_target')
		self.game.score(200)

	def sw_dropTargetD_active(self, sw):
		#self.game.sound.play('drop_target')
		pass

	def sw_dropTargetG_active(self, sw):
		self.game.sound.play('drop_target')
		self.game.score(200)

	def sw_dropTargetE_active(self, sw):
		self.game.sound.play('drop_target')
		self.game.score(200)

	def sw_subwayEnter2_active(self, sw):
		self.game.score(500)

	#
	# Mystery
	#
	
	def sw_captiveBall1_active(self, sw):
		self.game.sound.play('meltdown')

	def sw_captiveBall2_active(self, sw):
		self.game.sound.play('meltdown')

	def sw_captiveBall3_active(self, sw):
		self.game.sound.play('meltdown')
		self.game.drive_lamp('mystery', 'on')
		self.mystery_lit = True
		self.inc_bonus_x()

	def sw_mystery_active(self, sw):
		self.game.sound.play('mystery')
		if self.mystery_lit:
			self.mystery_lit = False
			self.game.drive_lamp('mystery', 'off')
			if self.any_multiball_active():
				if self.game.ball_save.timer > 0:
					self.game.set_status('+10 second ball saver')
					self.game.ball_save.add(10)
				else:
					self.game.ball_save.callback = None
					self.game.set_status('save ' + str(self.game.trough.num_balls_in_play) + ' balls')
					self.game.ball_save.start(num_balls_to_save=self.game.trough.num_balls_in_play, time=10, now=True, allow_multiple_saves=True)

			elif self.state == 'mode':
				self.chain.mode.add(10)
				self.game.set_status('Adding 10 seconds')
			else:
				self.game.ball_save.callback = self.ball_save_callback
				self.game.ball_save.start(num_balls_to_save=1, time=10, now=True, allow_multiple_saves=True)
				self.game.set_status('+10 second ball saver')
				self.light_missile_award()

	#
	# Fire Buttons
	#
	
	def sw_fireR_active(self, sw):
		if self.game.switches.shooterR.is_inactive():
			self.chain.rotate_modes(1)
		else:
			self.game.coils.shooterR.pulse(50)
			if self.ball_starting:
				self.game.sound.stop_music()
				self.game.sound.play_music('background', loops=-1)

	def sw_fireL_active(self, sw):
		if self.game.switches.shooterL.is_inactive():
			self.chain.rotate_modes(-1)
		elif not self.any_multiball_active() and self.missile_award_mode.active:
			self.game.coils.shooterL.pulse(50)

	#
	# Ramps
	#
	
	def sw_leftRampEnter_active(self, sw):
		self.game.coils.flasherGlobe.schedule(0x33333, cycle_seconds=1, now=False)
		self.game.coils.flasherCursedEarth.schedule(0x33333, cycle_seconds=1, now=False)

	def sw_leftRampExit_active(self, sw):
		self.game.sound.play('left_ramp')
		self.game.score(2000)

	def sw_rightRampExit_active(self, sw):
		self.game.sound.play('right_ramp')
		self.game.coils.flashersRtRamp.schedule(0x33333, cycle_seconds=1, now=False)
		self.game.score(2000)

	#
	# Shooter Lanes
	#
	
	def sw_shooterR_inactive_for_300ms(self,sw):
		self.game.sound.play('ball_launch')

		anim = self.game.animations['bikeacrosscity']
		self.play_animation(anim, 'high', repeat=False, hold=False, frame_time=5)

	# Enable auto-plunge soon after the new ball is launched (by the player).
	def sw_shooterR_inactive_for_1s(self,sw):
		self.auto_plunge = True

		if self.ball_starting and not self.tilt:
			self.skill_shot.begin()
			ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
			self.game.ball_save.callback = self.ball_save_callback
			self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=True, allow_multiple_saves=False)
			self.game.modes.add(self.boring)
			# Tell game to save ball start time now, since ball is now in play.
			self.game.save_ball_start_time()
		self.ball_starting = False
		self.game.modes.remove(self.game_intro)

	def sw_shooterR_active(self,sw):
		if self.ball_starting: 
			# Start skill shot, but not if already started.  Ball
			# might bounce on shooterR switch.  Don't want to
			# use a delayed switch handler because player
			# could launch ball immediately (before delay expires).
			if not self.skill_shot_added:
				self.game.modes.add(self.skill_shot)
				self.skill_shot_added = True
				self.welcome()
				self.high_score_mention()
			self.game.sound.play_music('ball_launch',loops=-1)

	def sw_shooterR_closed_for_700ms(self,sw):
		if self.auto_plunge:
			self.game.coils.shooterR.pulse(50)

	def sw_shooterL_active_for_500ms(self, sw):
		if self.any_multiball_active() or self.state == 'mode':
			self.game.coils.shooterL.pulse()
		elif self.missile_award_lit:
			self.game.sound.stop_music()
			self.disable_missile_award()
			if self.video_mode_lit:
				self.game.modes.add(self.video_mode)
				self.video_mode_lit = False
			else:
				self.game.modes.add(self.missile_award_mode)
		else:
			self.light_missile_award()
			self.game.coils.shooterL.pulse()

	def sw_shooterL_inactive_for_200ms(self, sw):
		self.game.sound.play('shooterL_launch')

	#
	# Lamps
	#

	def update_lamps(self):
		style = 'on' if self.game.current_player().extra_balls > 0 else 'off'
		self.game.drive_lamp('judgeAgain', style)

		style = 'off' if self.extra_balls_lit == 0 else 'slow'
		self.game.drive_lamp('extraBall2', style)

		if self.state != 'ultimate_challenge':
			for mode in self.chain.modes_not_attempted:
				self.game.drive_lamp(mode.lamp_name, 'off')
			for mode in self.chain.modes_attempted:
				self.game.drive_lamp(mode.lamp_name, 'on')

		if self.state == 'idle' or self.state == 'mode' or self.state == 'modes_complete':
			if self.state == 'mode':
				self.game.drive_lamp(self.chain.mode.lamp_name, 'slow')
			else:
				if self.game.switches.popperR.is_inactive() and not self.any_multiball_active() and not self.intro_playing and len(self.chain.modes_not_attempted) > 0:
					self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
				if len(self.chain.modes_not_attempted) > 0:
					self.game.drive_lamp(self.chain.modes_not_attempted[self.chain.modes_not_attempted_ptr].lamp_name, 'slow')
			self.game.drive_lamp('ultChallenge', 'off') 
		elif self.state == 'ultimate_challenge':
			self.game.drive_lamp('ultChallenge', 'on') 
		elif self.state == 'pre_ultimate_challenge':
			self.game.drive_lamp('ultChallenge', 'slow') 
			if not self.any_multiball_active() and not self.intro_playing:
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

		style = 'on' if self.mystery_lit else 'off'
		self.game.drive_lamp('mystery', style)

		style = 'medium' if self.missile_award_lit else 'off'
		self.game.drive_lamp('airRaid', style)

		if self.state != 'ultimate_challenge':
			style = 'slow' if self.inner_loop_active else 'off'
			self.game.drive_lamp('perp2W', style)
			self.game.drive_lamp('perp2R', style)
			self.game.drive_lamp('perp2Y', style)
			self.game.drive_lamp('perp2G', style)

			style = 'slow' if self.outer_loop_active else 'off'
			self.game.drive_lamp('perp4W', style)
			self.game.drive_lamp('perp4R', style)
			self.game.drive_lamp('perp4Y', style)
			self.game.drive_lamp('perp4G', style)

		if self.state == 'pre_ultimate_challenge':
			self.game.lamps.dropTargetJ.disable()
			self.game.lamps.dropTargetU.disable()
			self.game.lamps.dropTargetD.disable()
			self.game.lamps.dropTargetG.disable()
			self.game.lamps.dropTargetE.disable()
			self.game.lamps.advanceCrimeLevel.disable()
			self.game.lamps.mystery.disable()

	#
	# Coils
	#

	def sw_popperL_active_for_200ms(self, sw):
		self.flash_then_pop('flashersLowerLeft', 'popperL', 50)
	
	def popperR_eject(self):
		self.flash_then_pop('flashersRtRamp', 'popperR', 20)

	def flash_then_pop(self, flasher, coil, pulse):
		self.game.coils[flasher].schedule(0x00555555, cycle_seconds=1, now=True)
		self.delay(name='delayed_pop', event_type=None, delay=1.0, handler=self.delayed_pop, param=[coil, pulse])

	def delayed_pop(self, coil_pulse):
		self.game.coils[coil_pulse[0]].pulse(coil_pulse[1])	

	#
	# Multiball
	#
	
	def any_multiball_active(self):
		return self.multiball.is_active() or self.crimescenes.is_multiball_active() or self.ultimate_challenge.is_active()

	def multiball_started(self):
		# Make sure no other multiball was already active before
		# preparing for multiball.
		if not (self.multiball.is_active() and self.crimescenes.is_multiball_active()):
			self.game.sound.fadeout_music()
			self.game.sound.play_music('multiball', loops=-1)

			# No modes can be started when multiball is active
			self.game.lamps.rightStartFeature.disable()
			# Light mystery once for free.
			self.game.drive_lamp('mystery', 'on')
			self.mystery_lit = True
			self.save_missile_award()

	def multiball_ended(self):
		self.setup_next_mode(True)

	def light_missile_award(self):
		self.missile_award_lit_save = False
		self.missile_award_lit = True
		self.game.drive_lamp('airRaid', 'medium')
	
	#
	# Awards
	#
	
	# Disable missile award and don't save it for later
	def disable_missile_award(self):
		self.missile_award_lit_save = False
		self.missile_award_lit = False
		self.game.drive_lamp('airRaid', 'off')

	# Disable missile award but save it for later if lit.
	def save_missile_award(self):
		if self.missile_award_lit:
			self.missile_award_lit_save = True
			self.missile_award_lit = False
			self.game.drive_lamp('airRaid', 'off')

	# Re-enable missile_award if it was lit before multiball started
	def restore_missile_award(self):
		if self.missile_award_lit_save:
			self.light_missile_award()

	# Award missile award indicated by award param.
	def award_missile_award(self, award):
		self.game.sound.play_music('background', loops=-1)
		if award.endswith('Points', 0) != -1:
			award_words = award.rsplit(' ')
			self.game.score(int(award_words[0]))
			self.show_on_display(str(award_words[0]) + ' Points', None, 'mid')
			self.game.set_status(award)
		elif award == 'Light Extra Ball':
			self.light_extra_ball()
		elif award == 'Advance Crimescenes':
			self.crimescenes.level_complete()
			self.show_on_display('Crimes Adv', None, 'mid')
		elif award == 'Bonus +1X':
			self.inc_bonus_x()
		elif award == 'Hold Bonus X':
			self.hold_bonus_x = True
			self.show_on_display('Hold Bonus X', None, 'mid')

	def award_hurryup_award(self, award):
		if award == 'all' or award == '100000 points':
			self.game.score(100000)

		if award == 'all' or award == 'crimescenes':
			self.crimescenes.level_complete(1)

	def video_mode_complete(self, success):
		if self.state == 'mode':
			self.chain.mode.play_music()
		else:
			self.game.sound.stop_music()
		self.game.sound.play_music('background', loops=-1)
		self.game.modes.remove(self.video_mode)
		self.game.coils.shooterL.pulse()
		if success:
			self.light_extra_ball()

	#
	# Ultimate Challenge
	#
	
	def is_ultimate_challenge_ready(self):
		# 3 Criteria for finale: jackpot, crimescenes, all modes attempted.
		return self.multiball.jackpot_collected and \
				self.crimescenes.complete and \
				len(self.chain.modes_not_attempted) == 0

	# start ultimate challenge by showing the instructions
	def start_ultimate_challenge(self):
		self.game.lamps.rightStartFeature.disable()
		self.play_ult_intro.setup(self.ultimate_challenge.active_mode, self.activate_ultimate_challenge)
		self.game.modes.add(self.play_ult_intro)
		self.game.modes.remove(self.multiball)
		self.game.modes.remove(self.crimescenes)
		self.game.modes.remove(self.skill_shot)
		self.game.modes.remove(self.boring)
		self.intro_playing = True

	# start ultimate challenge after showing the instructions
	def activate_ultimate_challenge(self):
		self.game.modes.remove(self.play_ult_intro)
		self.intro_playing = False
		self.mystery_lit = False
		self.disable_missile_award()

		self.state = 'ultimate_challenge'
		self.game.modes.add(self.ultimate_challenge)

		# Put the ball back into play
		self.popperR_eject()

	def ultimate_challenge_over(self):
		self.game.modes.remove(self.ultimate_challenge)	
		self.reset_modes()
		# supergame reverts to normal play for this player
		self.supergame = False

	#
	# Loop Combos
	#

	def sw_topRightOpto_active(self, sw):
		#See if ball came around inner left loop
		if self.game.switches.topCenterRollover.time_since_change() < 1.5:
			self.inner_loop_active = True
			self.game.sound.play('inner_loop')
			self.inner_loop_combos += 1
			if self.inner_loop_combos > self.best_inner_loops:
				self.best_inner_loops = self.inner_loop_combos
			score = 10000 * (self.inner_loop_combos)
			self.game.score(score)
			self.show_on_display('inner loop: ' + str(self.inner_loop_combos), score, 'mid')
			anim = self.game.animations['bike_across_screen']
			self.play_animation(anim, 'mid', repeat=False, hold=False, frame_time=3)
			self.game.update_lamps()
			self.cancel_delayed('inner_loop')
			self.delay(name='inner_loop', event_type=None, delay=3.0, handler=self.inner_loop_combo_expired)

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1:
			self.outer_loop_active = True
			self.game.sound.play('outer_loop')
			self.outer_loop_combos += 1
			if self.outer_loop_combos > self.best_outer_loops:
				self.best_outer_loops = self.outer_loop_combos
			score = 1000 * (self.outer_loop_combos)
			self.game.score(score)
			self.show_on_display('outer loop: ' + str(self.outer_loop_combos), score, 'mid')
			anim = self.game.animations['bike_across_screen']
			self.play_animation(anim, 'mid', repeat=False, hold=False, frame_time=3)
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

	#
	# Extra ball
	#
	
	def light_extra_ball(self):
		if self.total_extra_balls_lit == self.game.user_settings['Gameplay']['Max extra balls per game']:
			self.game.set_status('No more extras this game.')
		elif self.extra_balls_lit == self.game.user_settings['Gameplay']['Max extra balls lit']:
			self.game.set_status('Extra balls lit maxed.')
		else:
			self.extra_balls_lit += 1
			self.total_extra_balls_lit += 1
			self.enable_extra_ball_lamp()
			self.show_on_display("Extra Ball Lit!", None, 'high')

	def award_extra_ball(self):
		self.game.extra_ball()
		self.extra_balls_lit -= 1
		self.show_on_display("Extra Ball!", None,'high')
		anim = self.game.animations['EBAnim']
		self.play_animation(anim, 'high', repeat=False, hold=False)
		self.game.update_lamps()

	def enable_extra_ball_lamp(self):
		self.game.drive_lamp('extraBall2', 'on')

	def sw_leftScorePost_active(self, sw):
		self.game.sound.play('extra_ball_target')
		if self.extra_balls_lit > 0:
			self.award_extra_ball()

	def sw_rightTopPost_active(self, sw):
		self.game.sound.play('extra_ball_target')
		if self.extra_balls_lit > 0:
			self.award_extra_ball()

	#
	# Inlane + ball drain
	#

	def sw_inlaneL_active(self, sw):
		self.game.sound.play('inlane')

	def sw_inlaneR_active(self, sw):
		self.game.sound.play('inlane')

	def sw_inlaneFarR_active(self, sw):
		self.game.sound.play('inlane')

	def sw_outlaneL_active(self, sw):
		self.outlane_active()

	def sw_outlaneR_active(self, sw):
		self.outlane_active()
		
	def outlane_active(self):
		self.game.score(1000)
		if self.any_multiball_active() or self.game.trough.ball_save_active:
			self.game.sound.play('outlane')
		else:
			self.game.sound.play_voice('curse')

	def ball_save_callback(self):
		if not self.any_multiball_active():
			self.game.sound.play_voice('ball saved')
			self.show_on_display("Ball Saved!", None, 'mid')
			self.skill_shot.skill_shot_expired()

	def ball_drained(self):
		# Called as a result of a ball draining into the trough.
		# End multiball if there is now only one ball in play (and MB was active).
		self.game.ball_save.callback = None
		if self.game.trough.num_balls_in_play == 1:
			if self.multiball.is_active():
				self.multiball.end_multiball()
			if self.crimescenes.is_multiball_active():
				self.crimescenes.end_mb()

	#
	# Bonus
	#
	
	def inc_bonus_x(self):
		self.bonus_x += 1
		self.show_on_display('Bonus at ' + str(self.bonus_x) + 'X', None, 'mid')

	def replay_callback(self):
		award = self.game.user_settings['Replay']['Replay Award']
		self.game.coils.knocker.pulse(50)
		if award == 'Extra Ball':
			self.award_extra_ball()
		else:
			self.show_on_display('Replay', None, 'mid')


class ModesDisplay(Mode):
	"""Display some text when the ball is active"""
	def __init__(self, game, priority):
		super(ModesDisplay, self).__init__(game, priority)
		self.big_text_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.small_text_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], "center")
		self.score_layer = TextLayer(128/2, 17, self.game.fonts['num_14x10'], "center")

	def display(self, text=None, score=None):
		if score:
			self.score_layer.set_text(str(score),3)
		if text:
			if score:
				self.small_text_layer.set_text(text,3)
				self.layer = GroupedLayer(128, 32, [self.small_text_layer, self.score_layer])
			else:
				self.big_text_layer.set_text(text,3)
				self.layer = GroupedLayer(128, 32, [self.big_text_layer])
		else:
			self.layer = GroupedLayer(128, 32, [self.score_layer])


class ModesAnimation(Mode):
	"""Play an animation when the ball is active"""
	def __init__(self, game, priority):
		super(ModesAnimation, self).__init__(game, priority)

	def play(self, anim, repeat=False, hold=False, frame_time=1):
		self.layer = AnimatedLayer(frames=anim.frames, repeat=repeat, hold=hold, frame_time=frame_time)


class GameIntro(Mode):
	"""Welcome on first ball or shoot again"""
	def __init__(self, game, priority):
		super(GameIntro, self).__init__(game, priority)

	def mode_started(self):
		self.delay(name='start', event_type=None, delay=1.0, handler=self.start )

	def start(self):
		if self.game.shooting_again:
			self.shoot_again()
		else:
			self.play_intro()

	def shoot_again(self):
		self.game.sound.play_voice('shoot again ' + str(self.game.current_player_index+1))
		self.again_layer = TextLayer(128/2, 9, self.game.fonts['jazz18'], "center").set_text('Shoot Again',3)
		self.layer = GroupedLayer(128, 32, [self.again_layer])

	def play_intro(self):
		self.game.sound.play_voice('welcome')
		gen = MarkupFrameGenerator()
		if self.game.supergame:
			self.delay(name='finish', event_type=None, delay=8.0, handler=self.finish)
			instructions = gen.frame_for_markup("""

#INSTRUCTIONS#

[Hit Right Fire to abort]

You have started the SuperGame.  Ultimate Challenge is lit.  Shoot the sniper tower to start the finale.
""")

		else:
			self.delay(name='finish', event_type=None, delay=25.0, handler=self.finish)
			instructions = gen.frame_for_markup("""

#INSTRUCTIONS#

Hit Right Fire to abort

To light Ultimate Challenge:
Attempt all chain features
Complete 16 crimescene levels
Collect a multiball jackpot

Start chain features by shooting the Build Up Chain Feature shot when lit

Chain feature instructions are displayed when starting each feature

Complete crimescene levels by shooting lit crimescene shots

Light locks by completing JUDGE target bank

During multiball, shoot left ramp to light jackpot then shoot subway to collect

""")

		self.layer = PanningLayer(width=128, height=32, frame=instructions, origin=(0,0), translate=(0,1), bounce=False)

	def finish(self):
		self.game.modes.remove(self)

	def mode_stopped(self):
		self.cancel_delayed('finish')
		self.cancel_delayed('start')
