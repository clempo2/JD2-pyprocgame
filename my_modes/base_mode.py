import procgame
from procgame import *
from tilt import Tilt
from jd_modes import JD_Modes
from bonus import Bonus

class BaseGameMode(game.Mode):
	"""Game play when no playable mode is active"""
	
	def __init__(self, game):
		super(BaseGameMode, self).__init__(game, 2)
		self.tilt = Tilt(self.game, 1000, self.game.fonts['jazz18'], self.game.fonts['tiny7'], 'tilt', 'slamTilt')
		self.flipper_enable_workaround_active = False

	def mode_started(self):
		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Do a quick lamp show
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

		# Turn on all GIs
		self.game.update_gi(True)

		# Enable the flippers
		self.game.enable_flippers(enable=True)

		# Create jd_modes, which handles all of the game rules
		self.jd_modes = JD_Modes(self.game, 8, self.game.fonts['tiny7'], self.game.fonts['jazz18'])

		# Create mode to check for replay
		self.replay = procgame.modes.Replay(self.game, 18)
		self.game.modes.add(self.replay)
		self.replay.replay_callback = self.jd_modes.replay_callback
		self.jd_modes.replay = self.replay

		# Start modes
		self.game.modes.add(self.jd_modes)
		self.tilt.tilt_callback = self.tilt_callback
		self.tilt.slam_tilt_callback = self.slam_tilt_callback
		self.tilt.num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
		self.game.modes.add(self.tilt)

		# Load the player data saved from the previous ball.
		# It will be empty if this is the first ball.
		self.jd_modes.restore_player_state()
		if self.game.attract_mode.play_super_game:
			self.jd_modes.multiball.jackpot_collected = True
			self.jd_modes.crimescenes.complete = True
			self.jd_modes.modes_not_attempted = []
		self.jd_modes.begin_processing()

		# Put the ball into play and start tracking it.
		# self.game.coils.trough.pulse(40)
		# Always start the ball with no launch callback.
		self.game.trough.launch_balls(1, self.empty_ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0

		# In case a higher priority mode doesn't install it's own ball_drained
		# handler.
		self.game.trough.drain_callback = self.ball_drained_callback

	def empty_ball_launch_callback(self):
		pass

	def mode_stopped(self):
		# Ensure flippers are disabled
		self.game.enable_flippers(enable=False)

		# Deactivate the ball search logic so it won't search due to no 
		# switches being hit.
		self.game.ball_search.disable()

	def ball_drained_callback(self):
		if self.game.trough.num_balls_in_play == 0:
			# Give jd_modes a chance to do any ball processing
			self.jd_modes.ball_drained()
			# End the ball
			if self.tilt_status:
				self.tilt_delay()
			else:
				self.finish_ball()
		else:
			# Tell jd_modes a ball has drained (but not the last ball).
			self.jd_modes.ball_drained()

	def tilt_delay(self):
		# Make sure tilt switch hasn't been hit for at least 2 seconds before
		# finishing ball to ensure next ball doesn't start with tilt bob still
		# swaying.
		if self.game.switches.tilt.time_since_change() < 2:
			self.delay(name='tilt_bob_settle', event_type=None, delay=2.0, handler=self.tilt_delay)
		else:
			self.finish_ball()

	def finish_ball(self):
		self.game.sound.fadeout_music()

		# Make sure the motor isn't spinning between balls.
		self.game.coils.globeMotor.disable()

		# Remove the rules logic from responding to switch events.
		self.game.modes.remove(self.jd_modes)
		self.game.modes.remove(self.tilt)

		# save the player's data
		self.jd_modes.save_player_state()

		# Create the bonus mode so bonus can be calculated.
		self.bonus = Bonus(self.game, 8, self.game.fonts['jazz18'], self.game.fonts['tiny7'])
		self.game.modes.add(self.bonus)

		# Only compute bonus if it wasn't tilted away.
		if not self.tilt_status:
			self.bonus.compute(self.jd_modes.get_bonus_base(), self.jd_modes.get_bonus_x(), self.end_ball)
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

	def sw_startButton_active(self, sw):
		if self.game.ball == 1:
			if len(self.game.players) < 4:
				p = self.game.add_player()
				self.game.set_status(p.name + " added!")
		elif self.game.user_settings['Gameplay']['Allow restarts']:
			self.game.set_status("Hold for 2s to reset.")

	def sw_startButton_active_for_2s(self, sw):
		if self.game.ball > 1 and self.game.user_settings['Gameplay']['Allow restarts']:
			self.game.set_status("Reset!")

			# Need to build a mechanism to reset AND restart the game.  If one ball
			# is already in play, the game can restart without plunging another ball.
			# It would skip the skill shot too (if one exists). 

			# Currently just reset the game. This forces the ball(s) to drain and
			# the game goes to attrack mode. This makes it painfully slow to restart,
			# but it's better than nothing.
			self.game.reset()
			return procgame.game.SwitchStop

	# Allow service mode to be entered during a game.
	def sw_enter_active(self, sw):
		del self.game.service_mode
		self.game.service_mode = procgame.service.ServiceMode(self.game,100,self.game.fonts['tiny7'],[self.game.deadworld_test])
		self.game.modes.add(self.game.service_mode)
		return procgame.game.SwitchStop

	# Outside of the service mode, up/down control audio volume.
	def sw_down_active(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return procgame.game.SwitchStop

	def sw_up_active(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return procgame.game.SwitchStop

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
			self.jd_modes.tilt = True

			# Disable flippers so the ball will drain.
			self.game.enable_flippers(enable=False)

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
	
	def sw_slingL_active(self, sw):
		self.game.score(100)

	def sw_slingR_active(self, sw):
		self.game.score(100)
