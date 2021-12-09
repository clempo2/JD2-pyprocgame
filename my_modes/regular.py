import locale
from procgame.dmd import GroupedLayer, MarkupFrameGenerator, PanningLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Scoring_Mode
from chain import Chain
from crimescenes import CrimeScenes
from multiball import Multiball
from skillshot import SkillShot
from missile import MissileAwardMode

class RegularPlay(Scoring_Mode):
	"""Controls all play except ultimate challenge"""

	def __init__(self, game, priority):
		super(RegularPlay, self).__init__(game, priority)

		# Instantiate sub-modes
		self.game_intro = GameIntro(self.game, priority + 1)
		self.skill_shot = SkillShot(self.game, priority + 5)
		self.chain = Chain(self.game, priority)
		
		self.crime_scenes = CrimeScenes(game, priority + 1)
		self.crime_scenes.start_multiball_callback = self.multiball_started
		self.crime_scenes.end_multiball_callback = self.multiball_ended
		
		self.multiball = Multiball(self.game, priority + 1)
		self.multiball.start_callback = self.multiball_started
		self.multiball.end_callback = self.multiball_ended
		
		self.missile_award_mode = MissileAwardMode(game, priority + 10)

	def reset_modes(self):
		for mode in [self.chain, self.crime_scenes, self.multiball, self.missile_award_mode]:
			mode.reset()
		
		# reset RegularPlay itself
		self.game.setPlayerState('mystery_lit', False)
		self.game.update_lamps()

	def mode_started(self):
		self.mystery_lit = self.game.getPlayerState('mystery_lit', False)
		self.skill_shot_added = False

		for mode in [self.chain, self.crime_scenes, self.multiball, self.missile_award_mode]:
			self.game.modes.add(mode)

		self.setup_next_mode()

		self.game.enable_gi(True)
		self.game.update_lamps()

	def mode_stopped(self):
		for mode in [self.skill_shot, self.chain, self.crime_scenes, self.multiball]:
			self.game.modes.remove(mode)

		self.game.setPlayerState('mystery_lit', self.mystery_lit)

	#
	# Message
	#

	def sw_shooterR_active(self, sw):
		if self.game.base_play.ball_starting: 
			# Start skill shot, but not if already started.  Ball
			# might bounce on shooterR switch.  Don't want to
			# use a delayed switch handler because player
			# could launch ball immediately (before delay expires).
			if not self.skill_shot_added:
				self.game.modes.add(self.skill_shot)
				self.skill_shot_added = True
				self.welcome()
				self.high_score_mention()

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
	# submodes
	#
	
	# called right after a mode has ended to decide the next state
	# the rule is: multiball can be stacked with a running mode, you cannot start a new mode during multiball
	def setup_next_mode(self):
		# a mode could still be running if modes were stacked, in that case do nothing and stay 'busy'
		if not (self.any_multiball_active() or self.chain.is_active()):
			self.game.sound.fadeout_music()
			self.game.sound.play_music('background', loops=-1)

			if self.is_ultimate_challenge_ready():
				# player needs to shoot the right popper to start the finale 
				self.state = 'challenge_ready'
				self.game.modes.remove(self.multiball)
				self.game.lamps.ultChallenge.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			elif not self.chain.is_complete():
				# player needs to shoot the right popper to start the next chain mode 
				self.state = 'chain_ready'
				self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			else:
				self.state = 'chain_complete'

	# starts a mode if a mode is available
	def sw_popperR_active_for_200ms(self, sw):
		if self.state == 'chain_ready':
			self.state = 'busy'
			self.chain.start_chain_mode()
		elif self.state == 'challenge_ready':
			self.state = 'busy'
			self.start_ultimate_challenge()
		else: # state 'busy' or 'chain_complete'
			self.popperR_eject()
		self.game.update_lamps()

	def crime_scenes_completed(self):
		self.setup_next_mode()

	def chain_mode_completed(self):
		self.setup_next_mode()

	#
	# Multiball
	#
	
	def any_multiball_active(self):
		return self.multiball.is_active() or self.crime_scenes.is_multiball_active()

	def multiball_started(self):
		# Make sure no other multiball was already active before preparing for multiball.
		# One multiball is the caller, so if both are active it means the other multiball was already active
		if not (self.multiball.is_active() and self.crime_scenes.is_multiball_active()):
			self.state = 'busy'
			self.game.sound.fadeout_music()
			self.game.sound.play_music('multiball', loops=-1)

			# No modes can be started when multiball is active
			self.game.lamps.rightStartFeature.disable()
			# Light mystery once for free.
			self.light_mystery()
			self.game.modes.remove(self.missile_award_mode)

	def multiball_ended(self):
		if not self.any_multiball_active():
			self.game.modes.add(self.missile_award_mode)
		self.setup_next_mode()

	#
	# Ultimate Challenge
	#
	
	def is_ultimate_challenge_ready(self):
		# 3 Criteria for finale
		return (self.multiball.jackpot_collected and
				self.crime_scenes.is_complete() and
				self.chain.is_complete())

	def start_ultimate_challenge(self):
		self.game.lamps.rightStartFeature.disable()
		for mode in [self.chain, self.crime_scenes, self.multiball, self]:
			self.game.modes.remove(mode)
		self.reset_modes()
		self.game.base_play.start_ultimate_challenge()

	#
	# Mystery
	#

	def light_mystery(self):
		self.game.drive_lamp('mystery', 'on')
		self.mystery_lit = True
	
	def sw_captiveBall1_active(self, sw):
		self.game.sound.play('meltdown')

	def sw_captiveBall2_active(self, sw):
		self.game.sound.play('meltdown')

	def sw_captiveBall3_active(self, sw):
		self.game.sound.play('meltdown')
		self.light_mystery()
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
	# Lamps
	#

	def update_lamps(self):
		style = 'on' if self.mystery_lit else 'off'
		self.game.drive_lamp('mystery', style)

		if self.state == 'chain_ready':
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
