import locale
from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode
from chain_features import Pursuit, Blackout, Sniper, BattleTank, Impersonator, Meltdown, Safecracker, ManhuntMillions, Stakeout

class Chain(Mode):
	"""Controls the progress through the chain modes"""
	
	def __init__(self, game, priority):
		super(Chain, self).__init__(game, priority)

		self.play_intro = PlayIntro(self.game, self.priority+1)

		pursuit = Pursuit(game, priority+1)
		blackout = Blackout(game, priority+1)
		sniper = Sniper(game, priority+1)
		battleTank = BattleTank(game, priority+1)
		impersonator = Impersonator(game, priority+1)
		meltdown = Meltdown(game, priority+1)
		safecracker = Safecracker(game, priority+1)
		manhunt = ManhuntMillions(game, priority+1)
		stakeout = Stakeout(game, priority+1)

		self.all_chain_modes = [pursuit, blackout, sniper, battleTank, impersonator, meltdown, safecracker, manhunt, stakeout]
		for mode in self.all_chain_modes:
			mode.exit_callback = self.chain_mode_over
		
		self.mode_completed_hurryup = ModeCompletedHurryUp(game, priority+1)
		self.mode_completed_hurryup.collected = self.hurryup_collected
		self.mode_completed_hurryup.expired = self.hurryup_over

	def mode_started(self):
		# restore player state
		p = self.game.current_player()
		self.modes_not_attempted = p.getState('modes_not_attempted', self.all_chain_modes[:])
		self.modes_not_attempted_ptr = p.getState('modes_not_attempted_ptr', 0)
		self.modes_attempted = p.getState('modes_attempted', [])
		self.modes_completed = p.getState('modes_completed', [])
		self.num_modes_attempted = p.getState('num_modes_attempted', 0)
		self.num_modes_completed = p.getState('num_modes_completed', 0)
		
		self.mode = None

	def mode_stopped(self):
		# save player state
		p = self.game.current_player()
		p.setState('modes_not_attempted', self.modes_not_attempted)
		p.setState('modes_not_attempted_ptr', self.modes_not_attempted_ptr)
		p.setState('modes_attempted', self.modes_attempted)
		p.setState('modes_completed', self.modes_completed)
		p.setState('num_modes_completed', self.num_modes_completed)
		p.setState('num_modes_attempted', self.num_modes_attempted)
		
		if self.mode != None:
			self.game.modes.remove(self.mode)

	def reset(self):
		p = self.game.current_player()
		p.setState('modes_not_attempted', self.all_chain_modes[:])
		p.setState('modes_not_attempted_ptr', 0)
		p.setState('modes_attempted', [])
		p.setState('modes_completed', [])

	def get_status_layers(self):
		tiny_font = self.game.fonts['tiny7']
		attempted_layer = TextLayer(128/2, 9, tiny_font, "center").set_text('Modes attempted: ' + str(self.num_modes_attempted))
		completed_layer = TextLayer(128/2, 19, tiny_font, "center").set_text('Modes completed: ' + str(self.num_modes_completed))
		status_layer = GroupedLayer(128, 32, [attempted_layer, completed_layer])
		return [status_layer]

	def sw_slingL_active(self, sw):
		self.rotate_modes(-1)

	def sw_slingR_active(self, sw):
		self.rotate_modes(1)

	# move the pointer to the next available mode to the left or right
	def rotate_modes(self, step):
		self.modes_not_attempted_ptr += step
		if self.modes_not_attempted_ptr < 0:
			self.modes_not_attempted_ptr = len(self.modes_not_attempted) - 1
		elif self.modes_not_attempted_ptr >= len(self.modes_not_attempted):
			self.modes_not_attempted_ptr = 0
		
		self.game.update_lamps()

	# start a chain mode by showing the instructions
	def start_chain_mode(self):
		self.game.lamps.rightStartFeature.disable()
		self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
		self.play_intro.setup(self.mode, self.activate_chain_mode)
		self.game.modes.add(self.play_intro)
		self.game.base_play.regular_play.intro_playing = True

	# activate a chain mode after showing the instructions
	def activate_chain_mode(self):
		self.game.modes.remove(self.play_intro)
		self.game.base_play.regular_play.intro_playing = False
		self.game.base_play.regular_play.save_missile_award()

		# Update the mode lists.
		self.modes_not_attempted.remove(self.mode)
		self.modes_attempted.append(self.mode)
		self.num_modes_attempted += 1
		self.rotate_modes(0)

		# Add the mode to the mode Q to activate it.
		self.game.base_play.regular_play.state = 'mode'
		self.game.modes.add(self.mode)
		self.mode.play_music()
		
		# Put the ball back into play
		self.game.base_play.regular_play.popperR_eject()

	# called when the mode has completed or expired but before the hurry up
	def chain_mode_over(self):
		self.game.modes.remove(self.mode)
		# Turn on mode lamp to show it has been attempted
		self.game.drive_lamp(self.mode.lamp_name, 'on')
		
		if self.mode.completed:
			# mode was completed successfully, start hurry up award
			self.modes_completed.append(self.mode)
			self.num_modes_completed += 1
			self.game.modes.add(self.mode_completed_hurryup)
		else:
			# mode not successful, skip the hurry up
			self.hurryup_over()

	# called when a successful mode hurry up was achieved
	def hurryup_collected(self):
		if self.game.base_play.regular_play.any_multiball_active():
			award = 'all'
		else:
			award = 'crimescenes'
		self.award_hurryup_award(award)
		self.hurryup_over()

	# called when the mode is over including the hurry up selection
	def hurryup_over(self):
		self.game.modes.remove(self.mode_completed_hurryup)
		self.game.base_play.regular_play.setup_next_mode()


class PlayIntro(Mode):
	"""Displays the instructions when a chain mode starts"""
	def __init__(self, game, priority):
		super(PlayIntro, self).__init__(game, priority)

	def mode_started(self):
		self.frame_counter = 0
		self.next_frame()
		self.game.enable_gi(False)
		self.game.enable_flippers(False) 

	def mode_stopped(self):
		self.cancel_delayed('intro')
		self.game.enable_gi(True)
		self.game.enable_flippers(True) 

	def setup(self, mode, exit_function):
		self.mode = mode
		self.exit_function = exit_function
		self.instruction_layers = mode.get_instruction_layers()
		self.layer = GroupedLayer(128, 32, self.instruction_layers[0])

	def sw_flipperLwL_active(self, sw):
		if self.game.switches.flipperLwR.is_active():
			self.exit_function()

	def sw_flipperLwR_active(self, sw):
		if self.game.switches.flipperLwL.is_active():
			self.exit_function()

	def next_frame(self):
		if self.frame_counter != len(self.instruction_layers):
			self.delay(name='intro', event_type=None, delay=2, handler=self.next_frame)
			self.layer = GroupedLayer(128, 32, self.instruction_layers[self.frame_counter])
			self.frame_counter += 1
		else:
			self.exit_function()	


class ModeCompletedHurryUp(Mode):
	"""Hurry up to subway after a chain mode is successfully completed"""
	def __init__(self, game, priority):
		super(ModeCompletedHurryUp, self).__init__(game, priority)
		self.countdown_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], "center")
		self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.banner_layer])
	
	def mode_started(self):
		self.banner_layer.set_text("HURRY-UP!", 3)
		self.seconds_remaining = 13
		self.update_and_delay()
		self.update_lamps()
		self.game.coils.tripDropTarget.pulse(40)
		self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)
		self.already_collected = False

	def trip_check(self):
		if self.game.switches.dropTargetD.is_inactive():
			self.game.coils.tripDropTarget.pulse(40)
			self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

	def sw_dropTargetD_inactive_for_400ms(self, sw):
		self.game.coils.tripDropTarget.pulse(40)
		self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

	def update_lamps(self):
		self.game.lamps.pickAPrize.schedule(schedule=0x33333333, cycle_seconds=0, now=True)

	def mode_stopped(self):
		self.game.lamps.pickAPrize.disable()
		self.cancel_delayed(['grace', 'countdown', 'trip_check'])
	
	def sw_subwayEnter1_closed(self, sw):
		self.collect_hurry_up()
	
	# Ball might jump over first switch.  Use 2nd switch as a catchall.
	def sw_subwayEnter2_closed(self, sw):
		if not self.already_collected:
			self.collect_hurry_up()
			
	def collect_hurry_up(self):
		self.collected()
		self.game.sound.play_voice('collected')
		self.cancel_delayed(['grace', 'countdown', 'trip_check'])
		self.already_collected = True
		self.banner_layer.set_text('Well Done!')
		self.layer = GroupedLayer(128, 32, [self.banner_layer])
	
	def update_and_delay(self):
		self.countdown_layer.set_text("%d seconds" % (self.seconds_remaining))
		self.delay(name='countdown', event_type=None, delay=1, handler=self.one_less_second)
		
	def one_less_second(self):
		self.seconds_remaining -= 1
		if self.seconds_remaining >= 0:
			self.update_and_delay()
		else:
			self.delay(name='grace', event_type=None, delay=2, handler=self.delayed_removal)
			
	def delayed_removal(self):
		self.expired()
