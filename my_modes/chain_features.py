from procgame.game import Mode
from procgame.modes import Scoring_Mode
from procgame.dmd import GroupedLayer, TextLayer
from random import randint
import locale
import logging
import time

class ModeTimer(Mode):
	"""timer for a timed mode"""
	def __init__(self, game, priority):
		super(ModeTimer, self).__init__(game, priority)
		self.timer = 0;

	def mode_stopped(self):
		self.stop()

	def start(self, time):
		# Tell the mode how much time it gets, if it cares.
		self.timer_update(time)
		self.timer = time
		self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)

	def stop(self):
		self.timer = 0
		self.cancel_delayed('decrement timer')

	def add(self,adder):
		self.timer += adder 

	def pause(self, pause_unpause=True):
		if pause_unpause:
			self.cancel_delayed('decrement timer')
		elif self.timer > 0:
			self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)
			self.timer_update(self.timer)
		else:
			logging.info("% 10.3f Timer calling callback" % (time.time()))
			self.failed()
			self.callback()

	def failed(self):
		pass

	def timer_update(self, time):
		pass


class ChainFeature(Scoring_Mode, ModeTimer):
	"""Base class for the chain modes"""
	def __init__(self, game, priority, name, lamp_name):
		super(ChainFeature, self).__init__(game, priority)
		self.name = name
		self.lamp_name = lamp_name
		self.countdown_layer = TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text(name)
		self.score_layer = TextLayer(128/2, 10, self.game.fonts['num_14x10'], "center")
		self.status_layer = TextLayer(128/2, 26, self.game.fonts['tiny7'], "center")
		self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

	def mode_started(self):
		self.shots = 0
		self.completed = False
		# Start the mode timer
		mode_time = self.game.user_settings['Gameplay']['Time per chain feature']
		self.start(mode_time)
		self.play_music()

	def get_difficulty(self, options):
		"""Return the number of required shots depending on the settings and the options for the mode"""
		difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
		if not difficulty in ['easy', 'medium', 'hard']:
			difficulty = 'medium'
		return options[difficulty]

	def register_callback_function(self, function):
		self.callback = function

	def play_music(self):
		self.game.sound.stop_music()
		self.game.sound.play_music('mode', loops=-1)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(name)
		instruction_layers = [[layer1]]
		return instruction_layers

	def mode_tick(self):
		score = self.game.current_player().score
		if score == 0:
			self.score_layer.set_text('00')
		else:
			self.score_layer.set_text(locale.format("%d",score,True))

	def timer_update(self, timer):
		self.countdown_layer.set_text(str(timer))
		
	def start_using_drops(self):
		self.game.base_play.regular_play.multiball.drops.paused = True
		self.reset_drops()

	def stop_using_drops(self):
		self.game.base_play.regular_play.multiball.drops.paused = False
		self.reset_drops()
		
	def reset_drops(self):
		self.game.base_play.regular_play.multiball.drops.animated_reset(.1)
		if (self.game.switches.dropTargetJ.is_active() or
		    	self.game.switches.dropTargetU.is_active() or
		    	self.game.switches.dropTargetD.is_active() or
		    	self.game.switches.dropTargetG.is_active() or
		    	self.game.switches.dropTargetE.is_active()): 
			self.game.coils.resetDropTarget.pulse(40)

class Pursuit(ChainFeature):
	"""Pursuit chain mode"""
	def __init__(self, game, priority):
		super(Pursuit, self).__init__(game, priority, 'Pursuit', 'pursuit')
		self.shots_required_for_completion = self.get_difficulty({'easy':3, 'medium':4, 'hard':5})

	def mode_started(self):
		super(Pursuit, self).mode_started()
		self.update_status()
		self.update_lamps()
		time = self.game.sound.play_voice('pursuit intro')
		self.delay(name='response', event_type=None, delay=time+0.5, handler=self.response)

	def response(self):
		self.game.sound.play_voice('in pursuit')

	def update_lamps(self):
		self.game.coils.flasherPursuitL.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
		self.game.coils.flasherPursuitR.schedule(schedule=0x03000300, cycle_seconds=0, now=True)

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()
		self.game.coils.flasherPursuitR.disable()

	# Award shot if ball diverted for multiball.  Ensure it was a fast
	# shot rather than one that just trickles in.
	def sw_leftRampToLock_active(self, sw):
		if self.game.switches.leftRampEnter.time_since_change() < 0.5:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.game.sound.play_voice('complete')
			self.completed = True
			self.game.score(50000)
			logging.info("% 10.3f Pursuit calling callback" % (time.time()))
			self.callback()
		else:
			self.game.sound.play_voice('good shot')

	def failed(self):
		self.game.sound.play_voice('failed')

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot " + str(self.shots_required_for_completion) + " L/R ramp shots")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers
	
class Blackout(ChainFeature):
	"""Blackout chain mode"""
	def __init__(self, game, priority):
		super(Blackout, self).__init__(game, priority, 'Blackout', 'blackout')
		self.shots_required_for_completion = self.get_difficulty({'easy':2, 'medium':2, 'hard':3})

	def mode_started(self):
		super(Blackout, self).mode_started()
		self.update_status()
		anim = self.game.animations['blackout']
		self.game.base_play.regular_play.play_animation(anim, 'high', repeat=False, hold=False, frame_time=3)
		self.update_lamps()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.game.lamps.blackoutJackpot.disable()
		self.game.coils.flasherBlackout.disable()
		self.game.enable_gi(True)

	def update_lamps(self):
		self.game.enable_gi(False) # disable all gi except gi05
		self.game.lamps.gi05.pulse(0)
		self.game.lamps.blackoutJackpot.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

	def sw_centerRampExit_active(self, sw):
		self.shots += 1
		self.game.score(10000)
		self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion - 1:
			self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
			self.game.score(50000)
		elif self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(110000)
			logging.info("% 10.3f Blackout calling callback" % (time.time()))
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot center ramp")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers

class Sniper(ChainFeature):
	"""Sniper chain mode"""
	def __init__(self, game, priority):
		super(Sniper, self).__init__(game, priority, 'Sniper', 'sniper')
		self.shots_required_for_completion = self.get_difficulty({'easy':2, 'medium':2, 'hard':3})

		self.countdown_layer = TextLayer(127, 1, self.game.fonts['tiny7'], "right")
		self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], "left").set_text("Sniper")
		self.score_layer = TextLayer(127, 10, self.game.fonts['num_14x10'], "right")
		self.status_layer = TextLayer(127, 26, self.game.fonts['tiny7'], "right")
		self.anim_layer = self.game.animations['scope']
		self.layer = GroupedLayer(128, 32, [self.anim_layer,self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

	def mode_started(self):
		super(Sniper, self).mode_started()
		self.update_status()
		self.update_lamps()
		time = randint(2,7)
		self.delay(name='gunshot', event_type=None, delay=time, handler=self.gunshot)

	def gunshot(self):
		self.game.sound.play_voice('sniper - shot')
		time = randint(2,7)
		self.delay(name='gunshot', event_type=None, delay=time, handler=self.gunshot)

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.game.lamps.awardSniper.disable()
		self.cancel_delayed('gunshot')

	def update_lamps(self):
		self.game.lamps.awardSniper.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_popperR_active_for_300ms(self, sw):
		self.shots += 1
		self.game.score(10000)
		anim = self.game.animations['dredd_shoot_at_sniper']
		self.game.base_play.regular_play.play_animation(anim, 'high', repeat=False, hold=False, frame_time=5)
		self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.game.sound.play_voice('sniper - hit')
			self.completed = True
			self.game.score(50000)
			logging.info("% 10.3f Sniper calling callback" % (time.time()))
			self.callback()
		else:
			self.game.sound.play_voice('sniper - miss')

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot Sniper Tower 2 times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class BattleTank(ChainFeature):
	"""Battle tank chain mode"""
	def __init__(self, game, priority):
		super(BattleTank, self).__init__(game, priority, 'Battle Tank', 'battleTank')

	def mode_started(self):
		super(BattleTank, self).mode_started()
		self.shots = {'left':False,'center':False,'right':False}
		self.update_status()
		self.update_lamps()
		self.game.sound.play_voice('tank intro')

	def update_status(self):
		status = 'Shots made: ' + str(self.num_shots) + '/' + str(len(self.shots))
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.game.lamps.tankCenter.disable()
		self.game.lamps.tankLeft.disable()
		self.game.lamps.tankRight.disable()

	def update_lamps(self):
		if not self.shots['center']:
			self.game.lamps.tankCenter.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		if not self.shots['left']:
			self.game.lamps.tankLeft.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		if not self.shots['right']:
			self.game.lamps.tankRight.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_topRightOpto_active(self, sw):
		if not self.shots['left']:
			if self.game.switches.leftRollover.time_since_change() < 1:
				self.game.lamps.tankLeft.disable()
				self.shots['left'] = True
				self.game.score(10000)
				self.num_shots += 1
				self.check_for_completion()

	def sw_centerRampExit_active(self, sw):
		if not self.shots['center']:
			self.game.lamps.tankCenter.disable()
			self.shots['center'] = True
			self.game.score(10000)
			self.num_shots += 1
			self.check_for_completion()

	def sw_threeBankTargets_active(self, sw):
		if not self.shots['right']:
			self.game.lamps.tankRight.disable()
			self.shots['right'] = True
			self.game.score(10000)
			self.num_shots += 1
			self.check_for_completion()

	def check_for_completion(self):
		self.update_status()
		for i in range(1,4):
			self.game.sound.stop('tank hit ' + str(i))
		self.game.sound.play_voice('tank hit ' + str(self.num_shots))
		if self.shots['right'] and self.shots['left'] and self.shots['center']:
			self.completed = True
			self.game.score(50000)
			logging.info("% 10.3f BattleTank calling callback" % (time.time()))
			self.callback()

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot all 3 battle tank shots")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class Meltdown(ChainFeature):
	"""Meltdown chain mode"""
	def __init__(self, game, priority):
		super(Meltdown, self).__init__(game, priority, 'Meltdown', 'meltdown')
		self.shots_required_for_completion = self.get_difficulty({'easy':3, 'medium':4, 'hard':5})

	def mode_started(self):
		super(Meltdown, self).mode_started()
		self.update_status()
		self.update_lamps()
		self.game.sound.play_voice('meltdown intro')

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.game.lamps.stopMeltdown.disable()

	def update_lamps(self):
		self.game.lamps.stopMeltdown.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_captiveBall1_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_captiveBall2_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_captiveBall3_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		self.update_status()

		for m in ['1','2','3','4','all']:
			self.game.sound.stop('meltdown ' + m)	

		if self.shots >= self.shots_required_for_completion:
			self.game.sound.play_voice('meltdown all')
			self.completed = True
			self.game.score(50000)
			logging.info("% 10.3f Meltdown calling callback" % (time.time()))
			self.callback()
		elif self.shots <= 4:
			self.game.sound.play_voice('meltdown ' + str(self.shots))

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Activate " + str(self.shots_required_for_completion) + " captive ball switches")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class Impersonator(ChainFeature):
	"""Bad impersonator chain mode"""
	def __init__(self, game, priority):
		super(Impersonator, self).__init__(game, priority, 'Impersonator', 'impersonator')
		self.shots_required_for_completion = self.get_difficulty({'easy':3, 'medium':5, 'hard':7})
		self.sound_active = False

	def play_music(self):
		pass

	def mode_started(self):
		super(Impersonator, self).mode_started()
		self.delay(name='moving_target', event_type=None, delay=1, handler=self.moving_target)
		self.start_using_drops()
		self.update_status()
		self.update_lamps()
		time = self.game.sound.play('bad impersonator')
		self.delay(name='song_restart', event_type=None, delay=time+0.5, handler=self.song_restart)
		self.delay(name='boo_restart', event_type=None, delay=time+4, handler=self.boo_restart)
		self.delay(name='shutup_restart', event_type=None, delay=time+3, handler=self.shutup_restart)

	def song_restart(self):
		self.game.sound.play('bi - song')
		self.delay(name='song_restart', event_type=None, delay=6, handler=self.song_restart)

	def boo_restart(self):
		time = randint(2,7)
		self.game.sound.play('bi - boo')
		self.delay(name='boo_restart', event_type=None, delay=time, handler=self.boo_restart)

	def shutup_restart(self):
		time = randint(2,7)
		self.game.sound.play('bi - shutup')
		self.delay(name='shutup_restart', event_type=None, delay=time, handler=self.shutup_restart)

	def update_status(self):
		if self.shots > self.shots_required_for_completion:
			extra_shots = self.shots - self.shots_required_for_completion
			status = 'Shots made: ' + str(extra_shots) + ' extra'
		else:
			status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.game.lamps.awardBadImpersonator.disable()
		self.stop_using_drops()
		self.cancel_delayed('moving_target')
		self.cancel_delayed('song_restart')
		self.cancel_delayed('boo_restart')
		self.cancel_delayed('shutup_restart')
		self.cancel_delayed('end_sound')
		self.game.sound.stop('bi - song')
		self.game.sound.stop('bi - boo')

	def update_lamps(self):
		self.game.lamps.awardBadImpersonator.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def end_sound(self):
		self.sound_active = False

	def check_for_completion(self):
		self.game.sound.stop('bi - song')
		if not self.sound_active:
			self.sound_active = True
			self.game.sound.play('bi - ouch')
			self.delay(name='end_sound', event_type=None, delay=1, handler=self.end_sound)
	
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)

	def sw_dropTargetJ_active(self,sw):
		if self.timer%6 == 0:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetU_active(self,sw):
		if self.timer%6 == 0 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetD_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 4 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetG_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 3 or self.timer%6 == 4:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetE_active(self,sw):
		if self.timer%6 == 3:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()
		self.game.coils.resetDropTarget.pulse(40)

	def moving_target(self):
		# ModeTimer is continuously updating self.timer
		self.game.disable_drops()
		if self.timer%6 == 0:
			self.game.lamps.dropTargetJ.pulse(0)
			self.game.lamps.dropTargetU.pulse(0)
		elif self.timer%6 == 1 or self.timer%6==5:
			self.game.lamps.dropTargetU.pulse(0)
			self.game.lamps.dropTargetD.pulse(0)
		elif self.timer%6 == 2 or self.timer%6==4:
			self.game.lamps.dropTargetD.pulse(0)
			self.game.lamps.dropTargetG.pulse(0)
		elif self.timer%6 == 3:
			self.game.lamps.dropTargetG.pulse(0)
			self.game.lamps.dropTargetE.pulse(0)
		self.delay(name='moving_target', event_type=None, delay=1, handler=self.moving_target)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot " + str(self.shots_required_for_completion) + " lit drop targets")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers
		

class Safecracker(ChainFeature):
	"""Safecracker chain mode"""
	def __init__(self, game, priority):
		super(Safecracker, self).__init__(game, priority, 'Safe Cracker', 'safecracker')
		self.shots_required_for_completion = self.get_difficulty({'easy':2, 'medium':3, 'hard':4})
		time = randint(10,20)
		self.delay(name='bad guys', event_type=None, delay=time, handler=self.bad_guys)

	def bad_guys(self):
		time = randint(5,10)
		self.delay(name='bad guys', event_type=None, delay=time, handler=self.bad_guys)
		self.game.sound.play_voice('bad guys')

	def mode_started(self):
		super(Safecracker, self).mode_started()
		self.start_using_drops()
		self.delay(name='trip_check', event_type=None, delay=1, handler=self.trip_check)
		self.update_status()
		self.update_lamps()

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.cancel_delayed('trip_check')
		self.cancel_delayed('bad guys')
		self.game.lamps.awardSafecracker.disable()
		self.stop_using_drops()

	def update_lamps(self):
		self.game.lamps.awardSafecracker.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

	def sw_subwayEnter2_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_dropTargetD_inactive_for_400ms(self, sw):
		self.game.coils.tripDropTarget.pulse(30)

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.game.sound.play_voice('complete')
			self.completed = True
			self.game.score(50000)
			logging.info("% 10.3f Safecracker calling callback" % (time.time()))
			self.callback()
		else:
			self.game.sound.play_voice('shot')

	def trip_check(self):
		if self.game.switches.dropTargetD.is_inactive():
			self.game.coils.tripDropTarget.pulse(40)
			self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot the subway " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class ManhuntMillions(ChainFeature):
	"""ManhuntMillions chain mode"""
	def __init__(self, game, priority):
		super(ManhuntMillions, self).__init__(game, priority, 'Manhunt', 'manhunt')
		self.shots_required_for_completion = self.get_difficulty({'easy':2, 'medium':3, 'hard':4})

	def mode_started(self):
		super(ManhuntMillions, self).mode_started()
		self.update_status()
		self.update_lamps()
		self.game.sound.play_voice('mm - intro')

	def update_lamps(self):
		self.game.coils.flasherPursuitL.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)
		
	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()

	# Award shot if ball diverted for multiball.  Ensure it was a fast
	# shot rather than one that just trickles in.
	def sw_leftRampToLock_active(self, sw):
		if self.game.switches.leftRampEnter.time_since_change() < 0.5:
			self.shots += 1
			self.game.score(10000)
			self.check_for_completion()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		self.update_status()
		if self.shots == self.shots_required_for_completion:
			self.game.sound.play_voice('mm - done')
			self.completed = True
			self.game.score(50000)
			logging.info("% 10.3f Manhunt calling callback" % (time.time()))
			self.callback()
		else:
			self.game.sound.play_voice('mm - shot')

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot the left ramp " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers


class Stakeout(ChainFeature):
	"""Stakeout chain mode"""
	def __init__(self, game, priority):
		super(Stakeout, self).__init__(game, priority, 'Stakeout', 'stakeout')
		self.shots_required_for_completion = self.get_difficulty({'easy':3, 'medium':4, 'hard':5})

	def mode_started(self):
		super(Stakeout, self).mode_started()
		self.update_status()
		self.update_lamps()
		self.delay(name='boring', event_type=None, delay=15, handler=self.boring_expired)

	def boring_expired(self):
		self.game.sound.play_voice('so - boring')
		self.delay(name='boring', event_type=None, delay=5, handler=self.boring_expired)

	def update_lamps(self):
		self.game.coils.flasherPursuitR.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

	def update_status(self):
		status = 'Shots made: ' + str(self.shots) + '/' + str(self.shots_required_for_completion)
		self.status_layer.set_text(status)

	def mode_stopped(self):
		self.cancel_delayed('boring')
		self.game.coils.flasherPursuitR.disable()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		self.cancel_delayed('boring')
		self.update_status()
		self.game.sound.stop('so - boring')
		if self.shots == self.shots_required_for_completion:
			self.completed = True
			self.game.score(50000)
			self.callback()
		elif self.shots == 1:
			self.game.sound.play_voice('so - over there')
		elif self.shots == 2:
			self.game.sound.play_voice('so - surrounded')
		elif self.shots == 3:
			self.game.sound.play_voice('so - move in')

	def get_instruction_layers(self):
		font = self.game.fonts['jazz18']
		font_small = self.game.fonts['tiny7']
		layer1 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer21 = TextLayer(128/2, 7, font, "center").set_text(self.name)
		layer22 = TextLayer(128/2, 24, font_small, "center").set_text("Shoot the right ramp " + str(self.shots_required_for_completion) + " times")
		instruction_layers = [[layer1], [layer21, layer22]]
		return instruction_layers
