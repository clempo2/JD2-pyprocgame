import locale
from procgame.dmd import GroupedLayer, MarkupFrameGenerator, PanningLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Scoring_Mode
from chain import Chain
from crimescenes import CrimeScenes
from multiball import Multiball
from boring import Boring
from skillshot import SkillShot
from missile import MissileAwardMode

class RegularPlay(Scoring_Mode):
	"""Controls all play except ultimate challenge"""

	def __init__(self, game, priority):
		super(RegularPlay, self).__init__(game, priority)

		# Instantiate sub-modes
		self.game_intro = GameIntro(self.game, priority + 1)
		self.boring = Boring(self.game, priority + 1)
		self.skill_shot = SkillShot(self.game, priority + 5)
		self.chain = Chain(self.game, priority)
		
		self.crime_scenes = CrimeScenes(game, priority + 1)
		
		self.multiball = Multiball(self.game, priority + 1)
		self.multiball.start_callback = self.multiball_started
		self.multiball.end_callback = self.multiball_ended
		
		self.missile_award_mode = MissileAwardMode(game, priority + 10)

	def reset_modes(self):
		self.state = 'idle'
		self.chain.reset()
		self.crime_scenes.reset()
		self.multiball.reset_jackpot_collected()
		self.missile_award_mode.reset()
		self.mystery_lit = False
		self.game.update_lamps()

	def mode_started(self):
		# restore player state
		player = self.game.current_player()
		self.state = player.getState('state', 'idle')
		self.mystery_lit = player.getState('mystery_lit', False)

		# disable auto-plunging for the start of ball
		# Force player to hit the right Fire button.
		self.auto_plunge = False

		self.ball_starting = True
		self.skill_shot_added = False
		self.mystery_lit = True

		for mode in [self.chain, self.crime_scenes, self.missile_award_mode]:
			self.game.modes.add(mode)
		
		if self.state != 'challenge_ready':
			self.game.modes.add(self.multiball)

		self.setup_next_mode()

		for flasher in ['flasherFear', 'flasherMortis', 'flasherDeath', 'flasherFire']:
			self.game.coils[flasher].disable()
		self.game.enable_gi(True)
		self.game.update_lamps()

	def mode_stopped(self):
		# Remove modes from the mode Q
		for mode in [self.boring, self.skill_shot, self.chain, self.crime_scenes, self.multiball]:
			self.game.modes.remove(mode)

		# Disable all flashers.
		for coil in self.game.coils:
			if coil.name.startswith('flasher', 0):
				coil.disable()

		# save player state
		player = self.game.current_player()
		player.setState('state', self.state)
		player.setState('mystery_lit', self.mystery_lit)

	def sw_popperR_active_for_200ms(self, sw):
		if not self.any_multiball_active():
			if self.state == 'idle':
				self.chain.start_chain_mode()
			elif self.state == 'challenge_ready':
				self.start_ultimate_challenge()
			else:
				self.popperR_eject()
		else:
			self.popperR_eject()
		self.game.update_lamps()

	# called right after a mode has ended to decide what to do next
	def setup_next_mode(self):
		# don't offer a new mode when multiball is still running
		if not self.any_multiball_active():
			self.game.sound.fadeout_music()
			self.game.sound.play_music('background', loops=-1)

			if self.is_ultimate_challenge_ready():
				# shoot the right popper to start the finale 
				self.state = 'challenge_ready'
				self.game.modes.remove(self.multiball)
				self.game.lamps.ultChallenge.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			elif not self.chain.is_complete():
				# shoot the right popper to start the next chain mode 
				self.state = 'idle'
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			else:
				self.state = 'chain_complete'

	def crime_scenes_completed(self):
		self.setup_next_mode()

	#
	# Message
	#

	def welcome(self):
		if self.game.ball == 1 or self.game.shooting_again:
			self.game.modes.add(self.game_intro)

	def high_score_mention(self):
		if self.game.ball == self.game.balls_per_game:
			if self.base_play.replay.replay_achieved[0]:
				text = 'Highest Score'
				score = str(self.game.game_data['ClassicHighScoreData'][0]['inits']) + locale.format("  %d",self.game.game_data['ClassicHighScoreData'][0]['score'],True)
			else:
				text = 'Replay'
				score = locale.format("%d", self.base_play.replay.replay_scores[0], True)
			self.game.base_play.show_on_display(text, score, 'high')

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
		self.game.base_play.inc_bonus_x()

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

			elif self.chain.is_active():
				self.chain.mode.add(10)
				self.game.set_status('Adding 10 seconds')
			else:
				self.game.ball_save.callback = self.ball_save_callback
				self.game.ball_save.start(num_balls_to_save=1, time=10, now=True, allow_multiple_saves=True)
				self.game.set_status('+10 second ball saver')
				self.missile_award_mode.light_missile_award()

	#
	# Fire Buttons
	#
	
	def sw_fireR_active(self, sw):
		if self.game.switches.shooterR.is_active():
			self.game.coils.shooterR.pulse(50)
			if self.ball_starting:
				self.game.sound.stop_music()
				self.game.sound.play_music('background', loops=-1)

	#
	# Shooter Lanes
	#
	
	def sw_shooterR_inactive_for_300ms(self,sw):
		self.game.sound.play('ball_launch')

		anim = self.game.animations['bikeacrosscity']
		self.game.base_play.play_animation(anim, 'high', repeat=False, hold=False, frame_time=5)

	# Enable auto-plunge soon after the new ball is launched (by the player).
	def sw_shooterR_inactive_for_1s(self,sw):
		self.auto_plunge = True

		if self.ball_starting and not self.game.base_play.tilt.tilted:
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
		if self.any_multiball_active():
			self.game.coils.shooterL.pulse()

	def sw_shooterL_inactive_for_200ms(self, sw):
		self.game.sound.play('shooterL_launch')

	#
	# Lamps
	#

	def update_lamps(self):
		style = 'on' if self.mystery_lit else 'off'
		self.game.drive_lamp('mystery', style)

		if self.state == 'idle':
			if self.game.switches.popperR.is_inactive() and not self.any_multiball_active():
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		elif self.state == 'challenge_ready':
			self.game.drive_lamp('ultChallenge', 'slow') 
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			self.game.disable_drop_lamps()
			self.game.lamps.advanceCrimeLevel.disable()
			self.game.lamps.mystery.disable()

	#
	# Coils
	#

	def sw_popperL_active_for_200ms(self, sw):
		self.game.base_play.flash_then_pop('flashersLowerLeft', 'popperL', 50)
	
	def popperR_eject(self):
		self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)

	#
	# Multiball
	#
	
	def any_multiball_active(self):
		return self.multiball.is_active() or self.crime_scenes.is_multiball_active()

	def multiball_started(self):
		# Make sure no other multiball was already active before preparing for multiball.
		# One multiball is the caller, so if both are active it means the other multiball was already active
		if not (self.multiball.is_active() and self.crime_scenes.is_multiball_active()):
			self.game.sound.fadeout_music()
			self.game.sound.play_music('multiball', loops=-1)

			# No modes can be started when multiball is active
			self.game.lamps.rightStartFeature.disable()
			# Light mystery once for free.
			self.game.drive_lamp('mystery', 'on')
			self.mystery_lit = True
			self.game.modes.remove(self.missile_award_mode)

	def multiball_ended(self):
		if not self.any_multiball_active():
			self.game.modes.add(self.missile_award_mode)
		self.setup_next_mode()
	
	#
	# Awards
	#

	def award_hurry_up_award(self, award):
		if award == 'all' or award == '100000 points':
			self.game.score(100000)

		if award == 'all' or award == 'crimescenes':
			self.crime_scenes.level_complete()

	#
	# Ultimate Challenge
	#
	
	def is_ultimate_challenge_ready(self):
		# 3 Criteria for finale: jackpot, crimescenes, all modes attempted.
		return (self.multiball.jackpot_collected and
				self.crime_scenes.is_complete() and
				self.chain.is_complete())

	def start_ultimate_challenge(self):
		self.game.lamps.rightStartFeature.disable()
		for mode in [self, self.boring, self.chain, self.crime_scenes, self.multiball]:
			self.game.modes.remove(mode)
		self.reset_modes()
		self.game.base_play.start_ultimate_challenge()

	#
	# End of ball
	#

	def sw_outlaneL_active(self, sw):
		self.outlane_hit()

	def sw_outlaneR_active(self, sw):
		self.outlane_hit()
		
	def outlane_hit(self):
		self.game.score(1000)
		if self.any_multiball_active() or self.game.trough.ball_save_active:
			self.game.sound.play('outlane')
		else:
			self.game.sound.play_voice('curse')

	def ball_save_callback(self):
		if not self.any_multiball_active():
			self.game.sound.play_voice('ball saved')
			self.game.base_play.show_on_display("Ball Saved!", None, 'mid')
			self.skill_shot.skill_shot_expired()

	def ball_drained(self):
		# Called as a result of a ball draining into the trough.
		# End multiball if there is now only one ball in play (and MB was active).
		self.game.ball_save.callback = None
		if self.game.trough.num_balls_in_play == 1:
			if self.multiball.is_active():
				self.multiball.end_multiball()
			if self.crime_scenes.is_multiball_active():
				self.crime_scenes.end_multiball()


class GameIntro(Mode):
	"""Welcome on first ball or shoot again"""

	def __init__(self, game, priority):
		super(GameIntro, self).__init__(game, priority)

	def mode_started(self):
		self.delay(name='start', event_type=None, delay=1.0, handler=self.start )

	def mode_stopped(self):
		self.cancel_delayed(['finish', 'start'])

	def start(self):
		if self.game.shooting_again:
			self.shoot_again()
		else:
			self.play_intro()

	def shoot_again(self):
		self.game.sound.play_voice('shoot again ' + str(self.game.current_player_index+1))
		big_font = self.game.fonts['jazz18']
		self.again_layer = TextLayer(128/2, 9, big_font, "center").set_text('Shoot Again', 3)
		self.layer = GroupedLayer(128, 32, [self.again_layer])

	def play_intro(self):
		self.game.sound.play_voice('welcome')
		gen = MarkupFrameGenerator()
		if self.game.supergame:
			# each wizard mode has its own intro
			self.finish()
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
