from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Replay
from bonus import Bonus
from info import Info
from regular_play import RegularPlay
from tilt import Tilt

class BasePlay(Mode):
	"""Base rules for all the time the ball is in play"""
	
	def __init__(self, game):
		super(BasePlay, self).__init__(game, 2)
		self.flipper_enable_workaround_active = False

		self.game.trough.drain_callback = self.ball_drained_callback
		
		self.tilt = Tilt(self.game, 1000, self.game.fonts['jazz18'], self.game.fonts['tiny7'], 'tilt', 'slamTilt')
		self.tilt.tilt_callback = self.tilt_callback
		self.tilt.slam_tilt_callback = self.slam_tilt_callback
		self.tilt.num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
		
		self.regular_play = RegularPlay(self.game, 8, self.game.fonts['tiny7'], self.game.fonts['jazz18'])

		self.info = Info(self.game, 28)
		self.info.callback = self.info_ended

		self.replay = Replay(self.game, 18)
		self.replay.replay_callback = self.regular_play.replay_callback
		self.regular_play.replay = self.replay

		self.bonus = Bonus(self.game, 8, self.game.fonts['jazz18'], self.game.fonts['tiny7'])

	def mode_started(self):
		p = self.game.current_player()
		self.best_inner_loops = p.getState('best_inner_loops', 0)
		self.best_outer_loops = p.getState('best_outer_loops', 0)

		self.outer_loop_active = False
		self.inner_loop_active = False
		self.inner_loop_combos = 0
		self.outer_loop_combos = 0


		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Do a quick lamp show
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

		self.game.enable_gi(True)
		self.game.enable_flippers(True) 

		# Start modes
		self.info_on = False

		self.game.modes.add(self.tilt)
		self.game.modes.add(self.replay)
		self.game.modes.add(self.regular_play)

		# Always start the ball with no launch callback.
		self.game.trough.launch_balls(1, self.empty_ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0

	def mode_stopped(self):
		p = self.game.current_player()
		p.setState('best_inner_loops', self.best_inner_loops)
		p.setState('best_outer_loops', self.best_outer_loops)
		
		self.cancel_delayed('inner_loop')
		self.cancel_delayed('outer_loop')

		# Ensure flippers are disabled
		self.game.enable_flippers(False) 

		# Deactivate the ball search logic so it won't search due to no 
		# switches being hit.
		self.game.ball_search.disable()

	#
	# Instant Info
	#

	def sw_flipperLwL_active_for_6s(self, sw):
		self.display_info()

	def sw_flipperLwR_active_for_6s(self, sw):
		self.display_info()

	def display_info(self):
		if not self.info_on:
			self.start_info()
		
	def start_info(self):
		self.info_on = True
		info_layers = self.get_info_layers()
		info_layers.extend(self.regular_play.chain.get_info_layers())
		info_layers.extend(self.regular_play.crimescenes.get_info_layers())
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
	# Ball
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

		# Remove the rules logic from responding to switch events.
		self.game.modes.remove(self.regular_play)
		self.game.modes.remove(self.tilt)

		# Add the bonus mode so bonus can be calculated.
		self.game.modes.add(self.bonus)

		# Only compute bonus if it wasn't tilted away.
		if not self.tilt_status:
			self.bonus.compute(self.end_ball)
		else:
			self.end_ball()

	# Final processing for the ending ball.
	# If bonus was calculated, it is finished by now.
	def end_ball(self):
		self.game.modes.remove(self.replay)
		# Remove the bonus mode since it's finished.
		self.game.modes.remove(self.bonus)
		# Tell the game object it can process the end of ball
		# (to end player's turn or shoot again)
		self.game.end_ball()

		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.

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
	# Slings
	#
	
	def sw_slingL_active(self, sw):
		self.game.sound.play('slingshot')
		self.game.score(100)

	def sw_slingR_active(self, sw):
		self.game.sound.play('slingshot')
		self.game.score(100)

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
