from procgame.dmd import AnimatedLayer, GroupedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Replay
from bonus import Bonus
from challenge import UltimateChallenge
from combos import Combos
from regular import RegularPlay
from status import StatusReport
from tilt import TiltMonitorMode

class BasePlay(Mode):
	"""Base rules for all the time the ball is in play"""
	
	def __init__(self, game):
		super(BasePlay, self).__init__(game, 2)
		self.flipper_enable_workaround_active = False

		self.game.trough.drain_callback = self.ball_drained_callback
		
		# Instantiate sub-modes
		self.tilt = TiltMonitorMode(self.game, 1000, 'tilt', 'slamTilt')
		self.tilt.num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
		
		self.combos = Combos(self.game, 28)
		self.status_report = StatusReport(self.game, 28)
		self.regular_play = RegularPlay(self.game, 8)
		
		self.ultimate_challenge = UltimateChallenge(game, 8)
		self.ultimate_challenge.exit_callback = self.ultimate_challenge_over

		self.bonus = Bonus(self.game, 8)

		self.replay = Replay(self.game, 18)
		self.replay.replay_callback = self.replay_callback

		self.priority_display = {'low': ModesDisplay(self.game, 18), 'mid': ModesDisplay(self.game, 21), 'high': ModesDisplay(self.game, 200) }
		self.priority_animation = {'low': ModesAnimation(self.game, 18), 'mid': ModesAnimation(self.game, 22), 'high': ModesAnimation(self.game, 210) }
		self.priority_modes = self.priority_display.values() + self.priority_animation.values()

	def mode_started(self):
		# init player state
		player = self.game.current_player()
		self.extra_balls_lit = player.getState('extra_balls_lit', 0)
		self.total_extra_balls_lit = player.getState('total_extra_balls_lit', 0)

		bonus_x = player.getState('bonus_x', 1) if player.getState('hold_bonus_x', False) else 1
		player.setState('bonus_x', bonus_x)
		player.setState('hold_bonus_x', False)

		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Do a quick lamp show
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

		self.game.enable_gi(True)

		# Always start the ball with no launch callback.
		self.game.trough.launch_balls(1, self.empty_ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Start modes
		self.game.enable_flippers(True)
		self.game.modes.add(self.tilt)
		self.game.modes.add(self.combos)
		self.game.modes.add(self.replay)
		for mode in self.priority_modes:
			self.game.modes.add(mode)

		if player.getState('supergame', self.game.supergame):
			self.start_ultimate_challenge(False)
		else:
			self.game.modes.add(self.regular_play)

	def mode_stopped(self):
		for mode in self.priority_modes:
			self.game.modes.remove(mode)

		self.game.enable_flippers(False) 
		self.game.ball_search.disable()

		player = self.game.current_player()
		player.setState('extra_balls_lit', self.extra_balls_lit)
		player.setState('total_extra_balls_lit', self.total_extra_balls_lit)

	#
	# Priority Display
	#
	
	def show_on_display(self, text=None, score=None, priority='low'):
		display_mode = self.priority_display[priority]
		display_mode.display(text, score)

	def play_animation(self, anim, priority='low', repeat=False, hold=False, frame_time=1):
		animation_mode = self.priority_animation[priority]
		animation_mode.play(anim, repeat, hold, frame_time)
	
	#
	# Status Report
	#

	def sw_flipperLwL_active_for_6s(self, sw):
		self.display_status_report()

	def sw_flipperLwR_active_for_6s(self, sw):
		self.display_status_report()

	def display_status_report(self):
		if not self.status_report in self.game.modes:
			self.game.modes.add(self.status_report)

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
			self.game.drive_lamp('extraBall2', 'on')
			self.game.base_play.show_on_display("Extra Ball Lit!", None, 'high')

	def sw_leftScorePost_active(self, sw):
		self.extra_ball_switch_hit()

	def sw_rightTopPost_active(self, sw):
		self.extra_ball_switch_hit()

	def extra_ball_switch_hit(self):
		self.game.sound.play('extra_ball_target')
		if self.extra_balls_lit > 0:
			self.extra_balls_lit -= 1
			self.extra_ball()
	
	def extra_ball(self):
		player = self.current_player()
		player.extra_balls += 1
		self.game.base_play.show_on_display("Extra Ball!", None,'high')
		anim = self.game.animations['EBAnim']
		self.game.base_play.play_animation(anim, 'high', repeat=False, hold=False)
		self.game.update_lamps()

	def update_lamps(self):
		style = 'on' if self.game.current_player().extra_balls > 0 else 'off'
		self.game.drive_lamp('judgeAgain', style)

		style = 'off' if self.extra_balls_lit == 0 else 'slow'
		self.game.drive_lamp('extraBall2', style)

	#
	# Ultimate Challenge
	#

	def start_ultimate_challenge(self, eject):
		# eject is True if ball is in popperR, False if ball is in shooterR
		self.game.modes.remove(self.regular_play)
		self.game.modes.add(self.ultimate_challenge)
		self.ultimate_challenge.start_challenge(eject)

	def ultimate_challenge_over(self):
		self.game.modes.remove(self.ultimate_challenge)	
		self.game.modes.add(self.regular_play)

	#
	# Replay
	#
	
	def replay_callback(self):
		award = self.game.user_settings['Replay']['Replay Award']
		self.game.coils.knocker.pulse(50)
		self.show_on_display('Replay', None, 'mid')
		if award == 'Extra Ball':
			self.extra_ball()
		#else add a credit in your head

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
	# Slings
	#
	
	def sw_slingL_active(self, sw):
		self.game.sound.play('slingshot')
		self.game.score(100)

	def sw_slingR_active(self, sw):
		self.game.sound.play('slingshot')
		self.game.score(100)

	#
	# Inlanes
	#

	def sw_inlaneL_active(self, sw):
		self.game.sound.play('inlane')

	def sw_inlaneR_active(self, sw):
		self.game.sound.play('inlane')

	def sw_inlaneFarR_active(self, sw):
		self.game.sound.play('inlane')

	#
	# Coil
	#

	def flash_then_pop(self, flasher, coil, pulse):
		self.game.coils[flasher].schedule(0x00555555, cycle_seconds=1, now=True)
		self.delay(name='delayed_pop', event_type=None, delay=1.0, handler=self.delayed_pop, param=[coil, pulse])

	def delayed_pop(self, coil_pulse):
		self.game.coils[coil_pulse[0]].pulse(coil_pulse[1])	

	#
	# End of Ball
	#
	
	def empty_ball_launch_callback(self):
		pass

	def ball_drained_callback(self):
		# Tell regular_play a ball has drained (but this might not be the last ball).
		self.regular_play.ball_drained()
		
		if self.game.trough.num_balls_in_play == 0:
			# End the ball
			if self.tilt.tilted:
				self.tilt.tilt_delay(self.finish_ball)
			else:
				self.finish_ball()

	def finish_ball(self):
		self.game.sound.fadeout_music()

		# Make sure the motor isn't spinning between balls.
		self.game.coils.globeMotor.disable()

		self.game.modes.remove(self.combos)
		self.game.modes.remove(self.tilt)
		self.game.modes.remove(self.regular_play)
		self.game.modes.remove(self.ultimate_challenge)

		self.game.enable_flippers(False) 

		if self.tilt.tilted:
			# ball tilted, skip bonus
			self.end_ball()
		else:
			self.game.modes.add(self.bonus)
			self.bonus.compute(self.end_ball)

	# Final processing for the ball
	# If bonus was calculated, it is finished by now.
	def end_ball(self):
		self.game.modes.remove(self.bonus)
		self.game.modes.remove(self.replay)
		
		self.game.enable_flippers(True)

		# Tell the game object it can process the end of ball
		# (to end player's turn or shoot again)
		self.game.end_ball()

		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.

	#
	# Bonus
	#
	
	def inc_bonus_x(self):
		player = self.game.current_player()
		bonus_x = player.getState('bonus_x') + 1
		player.setState('bonus_x', bonus_x)
		self.show_on_display('Bonus at ' + str(bonus_x) + 'X', None, 'mid')

	def hold_bonus_x(self):
		self.game.setPlayerState('hold_bonus_x', True)
		self.game.base_play.show_on_display('Hold Bonus X', None, 'mid')


class ModesDisplay(Mode):
	"""Display some text when the ball is active"""

	def __init__(self, game, priority):
		super(ModesDisplay, self).__init__(game, priority)
		self.big_text_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.small_text_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], "center")
		self.score_layer = TextLayer(128/2, 17, self.game.fonts['num_14x10'], "center")

	def display(self, text=None, score=None):
		layers = []
		if text:
			text_layer = self.small_text_layer if score else self.big_text_layer
			text_layer.set_text(text, 3)
			layers.append(text_layer)
		if score:
			self.score_layer.set_text(str(score), 3)
			layers.append(self.score_layer)
		self.layer = GroupedLayer(128, 32, layers)


class ModesAnimation(Mode):
	"""Play an animation when the ball is active"""

	def __init__(self, game, priority):
		super(ModesAnimation, self).__init__(game, priority)

	def play(self, anim, repeat=False, hold=False, frame_time=1):
		self.layer = AnimatedLayer(frames=anim.frames, repeat=repeat, hold=hold, frame_time=frame_time)
