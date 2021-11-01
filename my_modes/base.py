from procgame.dmd import AnimatedLayer, GroupedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Replay
from bonus import Bonus
from combos import Combos
from regular import RegularPlay
from status import StatusReport
from tilt import Tilt

class BasePlay(Mode):
	"""Base rules for all the time the ball is in play"""
	
	def __init__(self, game):
		super(BasePlay, self).__init__(game, 2)
		self.flipper_enable_workaround_active = False

		self.game.trough.drain_callback = self.ball_drained_callback
		
		# create modes
		self.tilt = Tilt(self.game, 1000, self.game.fonts['jazz18'], self.game.fonts['tiny7'], 'tilt', 'slamTilt')
		self.tilt.tilt_callback = self.tilt_callback
		self.tilt.slam_tilt_callback = self.slam_tilt_callback
		self.tilt.num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
		
		self.combos = Combos(self.game, 28)
		self.regular_play = RegularPlay(self.game, 8, self.game.fonts['tiny7'], self.game.fonts['jazz18'])
		self.status_report = StatusReport(self.game, 28)

		self.replay = Replay(self.game, 18)
		self.replay.replay_callback = self.regular_play.replay_callback
		self.regular_play.replay = self.replay

		self.bonus = Bonus(self.game, 8, self.game.fonts['jazz18'], self.game.fonts['tiny7'])

		self.priority_display = {'low': ModesDisplay(self.game, 18), 'mid': ModesDisplay(self.game, 21), 'high': ModesDisplay(self.game, 200) }
		self.priority_animation = {'low': ModesAnimation(self.game, 18), 'mid': ModesAnimation(self.game, 22), 'high': ModesAnimation(self.game, 210) }
		self.priority_modes = self.priority_display.values() + self.priority_animation.values()

	def mode_started(self):
		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Do a quick lamp show
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

		self.game.enable_gi(True)

		# Start modes
		self.game.enable_flippers(True) 
		self.game.modes.add(self.tilt)
		self.game.modes.add(self.combos)
		self.game.modes.add(self.regular_play)
		self.game.modes.add(self.replay)
		for mode in self.priority_modes:
			self.game.modes.add(mode)

		# Always start the ball with no launch callback.
		self.game.trough.launch_balls(1, self.empty_ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0

	def mode_stopped(self):
		for mode in self.priority_modes:
			self.game.modes.remove(mode)

		self.game.enable_flippers(False) 
		self.game.ball_search.disable()

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
	# End of Ball
	#
	
	def empty_ball_launch_callback(self):
		pass

	def ball_drained_callback(self):
		# Tell regular_play a ball has drained (but this might not be the last ball).
		self.regular_play.ball_drained()
		
		if self.game.trough.num_balls_in_play == 0:
			# End the ball
			if self.tilt_status:
				self.tilt_delay()
			else:
				self.finish_ball()

	def finish_ball(self):
		self.game.sound.fadeout_music()

		# Make sure the motor isn't spinning between balls.
		self.game.coils.globeMotor.disable()

		self.game.modes.remove(self.regular_play)
		self.game.modes.remove(self.combos)
		self.game.modes.remove(self.tilt)

		self.game.enable_flippers(False) 

		if self.tilt_status:
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
	# Tilt
	#
	
	# Reset game on slam tilt
	def slam_tilt_callback(self):
		self.game.sound.fadeout_music()
		# Need to play a sound and show a slam tilt screen.
		# For now just popup a status message.
		self.game.reset()
		return True

	def tilt_callback(self):
		# Process tilt.
		# First check to make sure tilt hasn't already been processed once.
		# No need to do this stuff again if for some reason tilt already occurred.
		if self.tilt_status == 0:

			self.game.sound.fadeout_music()
			
			# Tell the rules logic tilt occurred
			self.regular_play.tilt = True

			# Disable flippers so the ball will drain.
			self.game.enable_flippers(False) 

			# Make sure ball won't be saved when it drains.
			self.game.ball_save.disable()

			# Make sure the ball search won't run while ball is draining.
			self.game.ball_search.disable()

			# Ensure all lamps are off.
			for lamp in self.game.lamps:
				lamp.disable()

			# Kick balls out of places it could be stuck.
			if self.game.switches.shooterR.is_active():
				self.game.coils.shooterR.pulse(50)
			if self.game.switches.shooterL.is_active():
				self.game.coils.shooterL.pulse(20)
			self.tilt_status = 1
			#play sound
			#play video

	def tilt_delay(self):
		# Make sure tilt switch hasn't been hit for at least 2 seconds before
		# finishing ball to ensure next ball doesn't start with tilt bob still
		# swaying.
		if self.game.switches.tilt.time_since_change() < 2:
			self.delay(name='tilt_bob_settle', event_type=None, delay=2.0, handler=self.tilt_delay)
		else:
			self.finish_ball()


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
			self.score_layer.set_text(str(score),3)
			layers.append(self.score_layer)
		self.layer = GroupedLayer(128, 32, layers)


class ModesAnimation(Mode):
	"""Play an animation when the ball is active"""

	def __init__(self, game, priority):
		super(ModesAnimation, self).__init__(game, priority)

	def play(self, anim, repeat=False, hold=False, frame_time=1):
		self.layer = AnimatedLayer(frames=anim.frames, repeat=repeat, hold=hold, frame_time=frame_time)


