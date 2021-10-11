import procgame
from procgame import *
import locale
import os
import pinproc

import asset_loader
from asset_loader import AssetLoader
import my_modes
from my_modes.attract import Attract
from my_modes.base_mode import BaseGameMode
from my_modes.deadworld import Deadworld, DeadworldTest

import logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

curr_file_path = os.path.dirname(os.path.abspath( __file__ ))
settings_path = curr_file_path + "/config/settings.yaml"
game_data_path = curr_file_path + "/config/game_data.yaml"
game_data_template_path = curr_file_path + "/config/game_data_template.yaml"
settings_template_path = curr_file_path + "/config/settings_template.yaml"

font_tiny7 = dmd.font_named('04B-03-7px.dmd')
font_jazz18 = dmd.font_named("Jazz18-18px.dmd")
font_14x10 = dmd.font_named("Font14x10.dmd")
font_18x12 = dmd.font_named("Font18x12.dmd")
font_07x4 = dmd.font_named("Font07x4.dmd")
font_07x5 = dmd.font_named("Font07x5.dmd")
font_09Bx7 = dmd.font_named("Font09Bx7.dmd")

# Workaround to deal with latency of flipper rule programming.
# Need to make sure flippers deativate when the flipper buttons are
# released.  The flipper rules will automatically activate the flippers
# if the buttons are held while the enable ruler is programmed, but 
# if the buttons are released immediately after that, the deactivation
# would be missed without this workaround.
class FlipperWorkaroundMode(game.Mode):
	"""Workaround to deal with latency of flipper rule programming"""
	def __init__(self, game):
		super(FlipperWorkaroundMode, self).__init__(game, 2)
		self.flipper_enable_workaround_active = False

	def enable_flippers(self, enable=True):
		if enable:
			self.flipper_enable_workaround_active = True
			self.delay(name='flipper_workaround', event_type=None, delay=0.1, handler=self.end_flipper_workaround)

	def end_flipper_workaround(self):
		self.flipper_enable_workaround_active = False

	#def sw_flipperLwL_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperLwLMain'].pulse(34)
	#		self.game.coils['flipperLwLHold'].pulse(0)

	def sw_flipperLwL_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperLwLMain'].disable()
			self.game.coils['flipperLwLHold'].disable()

	#def sw_flipperLwR_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperLwRMain'].pulse(34)
	#		self.game.coils['flipperLwRHold'].pulse(0)

	def sw_flipperLwR_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperLwRMain'].disable()
			self.game.coils['flipperLwRHold'].disable()

	#def sw_flipperUpL_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperUpLMain'].pulse(34)
	#		self.game.coils['flipperUpLHold'].pulse(0)

	def sw_flipperUpL_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperUpLMain'].disable()
			self.game.coils['flipperUpLHold'].disable()

	#def sw_flipperUpR_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperUpRMain'].pulse(34)
	#		self.game.coils['flipperUpRHold'].pulse(0)

	def sw_flipperUpR_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperUpRMain'].disable()
			self.game.coils['flipperUpRHold'].disable()


class JDPlayer(game.Player):
	"""Keeps the progress of one player to allow the player
	   to resume where he left off in a multi-player game"""

	crimescenes = 0

	def __init__(self, name):
		super(JDPlayer, self).__init__(name)
		self.state_tracking = {}

	def setState(self, key, val):
		self.state_tracking[key] = val

	def getState(self, key, default = None):
		return self.state_tracking.get(key,default)


class JDGame(game.BasicGame):
	"""Judge Dredd pinball game"""
	
	def __init__(self):
		super(JDGame, self).__init__(pinproc.MachineTypeWPC)
		self.sound = procgame.sound.SoundController(self)
		self.lampctrl = procgame.lamps.LampController(self)
		self.logging_enabled = False
		self.shooting_again = False
		self.setup()
	
	def create_player(self, name):
		return JDPlayer(name)
	
	def save_settings(self):
		self.save_settings(settings_path)

	def save_game_data(self):
		super(JDGame, self).save_game_data(game_data_path)
		
	def setup(self):
		self.load_config('config/JD.yaml')
		self.load_settings(settings_template_path, settings_path)
		self.sound.music_volume_offset = self.user_settings['Machine']['Music volume offset']
		self.sound.set_volume(self.user_settings['Machine']['Initial volume'])
		self.load_game_data(game_data_template_path, game_data_path)
		
		logging.info("Stats:")
		logging.info(self.game_data)
		logging.info("Settings:")
		logging.info(self.settings)
		logging.info("Initial switch states:")
		for sw in self.switches:
			logging.info("  %s:\t%s" % (sw.name, sw.state_str()))

		self.balls_per_game = self.user_settings['Gameplay']['Balls per game']

		self.setup_ball_search()

		self.score_display.set_left_players_justify(self.user_settings['Display']['Left side score justify'])

		# Instantiate basic game features
		self.attract_mode = Attract(self)
		self.base_game_mode = BaseGameMode(self)
		self.flipper_workaround_mode = FlipperWorkaroundMode(self)
		self.deadworld = Deadworld(self, 20, self.settings['Machine']['Deadworld mod installed'])
		self.ball_save = procgame.modes.BallSave(self, self.lamps.drainShield, 'shooterR')

		trough_switchnames = []
		for i in range(1,7):
			trough_switchnames.append('trough' + str(i))
		early_save_switchnames = ['outlaneR', 'outlaneL']
		self.trough = procgame.modes.Trough(self,trough_switchnames,'trough6','trough', early_save_switchnames, 'shooterR', self.drain_callback)

		# Link ball_save to trough
		self.trough.ball_save_callback = self.ball_save.launch_callback
		self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
		self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

		self.deadworld_test = DeadworldTest(self,200,font_tiny7)

		# Setup and instantiate service mode
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7,[self.deadworld_test])
		
		asset_loader = AssetLoader(self)
		asset_loader.load_assets(curr_file_path)
		self.animations = asset_loader.animations 
		
		# Setup fonts
		self.fonts = {}
		self.fonts['tiny7'] = font_tiny7
		self.fonts['jazz18'] = font_jazz18
		self.fonts['num_14x10'] = font_14x10
		self.fonts['18x12'] = font_18x12
		self.fonts['num_07x4'] = font_07x4
		self.fonts['07x5'] = font_07x5
		self.fonts['num_09Bx7'] = font_09Bx7

		self.lampshow_keys = ['attract0', 'attract1']

		# High Score stuff
		self.highscore_categories = []
		
		cat = highscore.HighScoreCategory()
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=500000,inits='GSS'),\
				  highscore.HighScore(score=400000,inits='ASP'),\
				  highscore.HighScore(score=300000,inits='JRP'),\
				  highscore.HighScore(score=200000,inits='JAG'),\
				  highscore.HighScore(score=100000,inits='JTW')]
		cat.game_data_key = 'ClassicHighScoreData'
		self.highscore_categories.append(cat)
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'CrimescenesHighScoreData'
		cat.scores = [highscore.HighScore(score=2,inits='GSS')]
		cat.titles = ['Crimescene Champ']
		cat.score_for_player = lambda player: player.crimescenes
		cat.score_suffix_singular = ' level'
		cat.score_suffix_plural = ' levels'
		self.highscore_categories.append(cat)
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'InnerLoopsHighScoreData'
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=2,inits='GSS')]
		cat.titles = ['Inner Loop Champ']
		cat.score_for_player = lambda player: player.getState('best_inner_loops', 0)
		cat.score_suffix_singular = ' loop'
		cat.score_suffix_plural = ' loops'
		self.highscore_categories.append(cat)

		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'OuterLoopsHighScoreData'
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=2,inits='GSS')]
		cat.titles = ['Outer Loop Champ']
		cat.score_for_player = lambda player: player.getState('best_outer_loops', 0)
		cat.score_suffix_singular = ' loop'
		cat.score_suffix_plural = ' loops'
		self.highscore_categories.append(cat)
		
		for category in self.highscore_categories:
			category.load_from_game(self)

		# Instead of resetting everything here as well as when a user
		# initiated reset occurs, do everything in self.reset() and call it
		# now and during a user initiated reset.
		self.reset()

	def reset(self):
		# Reset the entire game framework
		super(JDGame, self).reset()

		# Add the basic modes to the mode queue
		self.modes.add(self.attract_mode)
		self.modes.add(self.ball_search)
		self.modes.add(self.deadworld)
		self.modes.add(self.ball_save)
		self.modes.add(self.trough)
		self.modes.add(self.flipper_workaround_mode)

		self.ball_search.disable()
		self.ball_save.disable()
		self.trough.drain_callback = self.drain_callback

		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)

	# Empty callback just incase a ball drains into the trough before another
	# drain_callback can be installed by a gameplay mode.
	def drain_callback(self):
		pass

	# Override to create a flag signaling extra ball.
	def shoot_again(self):
		super(JDGame, self).shoot_again()
		self.shooting_again = True

	def ball_starting(self):
		super(JDGame, self).ball_starting()
		self.modes.add(self.base_game_mode)

	def end_ball(self):
		self.shooting_again = False
		super(JDGame, self).end_ball()

		self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
		self.game_data['Audits']['Balls Played'] += 1

	def calc_time_average_string(self, prev_total, prev_x, new_value):
		prev_time_list = prev_x.split(':')
		prev_time = (int(prev_time_list[0]) * 60) + int(prev_time_list[1])
		avg_game_time = int((int(prev_total) * int(prev_time)) + int(new_value)) / (int(prev_total) + 1)
		avg_game_time_min = avg_game_time/60
		avg_game_time_sec = str(avg_game_time%60)
		if len(avg_game_time_sec) == 1:
			avg_game_time_sec = '0' + avg_game_time_sec

		return_str = str(avg_game_time_min) + ':' + avg_game_time_sec
		return return_str

	def calc_number_average(self, prev_total, prev_x, new_value):
		avg_game_time = int((prev_total * prev_x) + new_value) / (prev_total + 1)
		return int(avg_game_time)
		
	def ball_ended(self):
		self.modes.remove(self.base_game_mode)
		super(JDGame, self).ball_ended()

	def start_game(self):
		super(JDGame, self).start_game()
		self.game_data['Audits']['Games Started'] += 1
		
	def game_ended(self):
		super(JDGame, self).game_ended()
		# Make sure nothing unexpected happens if a ball drains
		# after a game ends (due possibly to a ball search).
		self.trough.drain_callback = self.drain_callback
		self.modes.remove(self.base_game_mode)
		#self.modes.add(self.attract_mode)
		self.deadworld.mode_stopped()
		# Restart attract mode lampshows

		# High Score Stuff
		seq_manager = highscore.EntrySequenceManager(game=self, priority=2)
		seq_manager.finished_handler = self.highscore_entry_finished
		seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
		seq_manager.ready_handler = self.highscore_entry_ready_to_prompt
		self.modes.add(seq_manager)

	def highscore_entry_ready_to_prompt(self, mode, prompt):
		self.sound.play_voice('high score')
		banner_mode = game.Mode(game=self, priority=8)
		markup = dmd.MarkupFrameGenerator()
		markup.font_plain = dmd.font_named('04B-03-7px.dmd')
		markup.font_bold = dmd.font_named('04B-03-7px.dmd')
		text = '\n[GREAT JOB]\n#%s#\n' % (prompt.left.upper()) # we know that the left is the player name
		frame = markup.frame_for_markup(markup=text, y_offset=0)
		banner_mode.layer = dmd.ScriptedLayer(width=128, height=32, script=[{'seconds':4.0, 'layer':dmd.FrameLayer(frame=frame)}])
		banner_mode.layer.on_complete = lambda: self.highscore_banner_complete(banner_mode=banner_mode, highscore_entry_mode=mode)
		self.modes.add(banner_mode)

	def highscore_banner_complete(self, banner_mode, highscore_entry_mode):
		self.modes.remove(banner_mode)
		highscore_entry_mode.prompt()

	def highscore_entry_finished(self, mode):
		self.modes.remove(mode)

		self.modes.add(self.attract_mode)

		#self.attract_mode.change_display(99)
		# setup display sequence in Attract.
		self.attract_mode.game_over_display()

		# Handle stats for last ball here
		self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
		self.game_data['Audits']['Balls Played'] += 1
		# Also handle game stats.
		for i in range(0,len(self.players)):
			game_time = self.get_game_time(i)
			self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string( self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
			self.game_data['Audits']['Games Played'] += 1

		for i in range(0,len(self.players)):
			self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
		self.save_game_data()

	def set_status(self, text):
		self.dmd.set_message(text, 3)
	
	def extra_ball(self):
		p = self.current_player()
		p.extra_balls += 1

	def getPlayerState(self, key, default = None):
		p = self.current_player()
		return p.getState(key, default)

	def setPlayerState(self, key, val):
		p = self.current_player()
		p.setState(key, val)

	def setup_ball_search(self):

		# Currently there are no special ball search handlers.  The deadworld
		# could be one, but running it while balls are locked would screw up
		# the multiball logic.  There is already logic in the multiball logic
		# to eject balls that enter the deadworld when lock isn't lit; so it 
		# shouldn't be necessary to search the deadworld.  (unless a ball jumps
		# onto the ring rather than entering through the feeder.)
		special_handler_modes = []
		self.ball_search = procgame.modes.BallSearch(self, priority=100, \
					 countdown_time=10, coils=self.ballsearch_coils, \
					 reset_switches=self.ballsearch_resetSwitches, \
					 stop_switches=self.ballsearch_stopSwitches, \
					 special_handler_modes=special_handler_modes)

	def enable_flippers(self, enable=True):
		super(JDGame, self).enable_flippers(enable)
		self.flipper_workaround_mode.enable_flippers(enable)
		
	def update_gi(self, on):
		for gi in ['gi01', 'gi02', 'gi03', 'gi04', 'gi05']:
			if on:
				self.lamps[gi].pulse(0)
			else:
				self.lamps[gi].disable()
		
def main():
	game = None
	try:
	 	game = JDGame()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
