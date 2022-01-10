from procgame.dmd import GroupedLayer, TextLayer
from procgame.modes import BasicDropTargetBank, Scoring_Mode

class Multiball(Scoring_Mode):
    """Multiball activated by locking balls in the Deadworld planet"""

    def __init__(self, game, priority):
        super(Multiball, self).__init__(game, priority)

        self.deadworld_mod_installed = self.game.user_settings['Machine']['Deadworld mod installed']

        self.drops = BasicDropTargetBank(self.game, priority=priority+1, prefix='dropTarget', letters='JUDGE')
        self.drops.on_advance = self.on_drops_advance
        self.drops.on_completed = self.possibly_light_lock
        self.drops.auto_reset = True

        font = self.game.fonts['jazz18']
        self.banner_layer = TextLayer(128/2, 7, font, 'center')
        self.layer = GroupedLayer(128, 32, [self.banner_layer])

    def voice_instructions(self):
        self.delay(name='voice instructions', event_type=None, delay=10, handler=self.voice_instructions)
        if self.state == 'multiball':
            if self.jackpot_lit:
                self.game.sound.play_voice('shoot the subway')
            else:
                self.game.sound.play_voice('shoot the left ramp')

    def mode_started(self):
        # restore player state
        player = self.game.current_player()
        self.state = player.getState('multiball_state', 'load')
        self.num_balls_locked = player.getState('multiball_num_balls_locked', 0)
        self.num_locks_lit = player.getState('multiball_num_locks_lit', 0)
        self.num_times_played = player.getState('multiball_num_times_played', 0)
        self.lock_level = player.getState('multiball_lock_level', 1)
        self.jackpot_collected = player.getState('multiball_jackpot_collected', False)

        self.lock_enabled = 0
        self.num_balls_to_eject = 0
        self.virtual_locks_needed = 0
        self.paused = False
        self.num_left_ramp_shots_hit = 0
        self.num_left_ramp_shots_needed = 1
        self.jackpot_lit = False

        self.delay(name='voice instructions', event_type=None, delay=10, handler=self.voice_instructions)
        self.game.coils.globeMotor.disable()
        self.game.deadworld.initialize()
        self.install_rule(enable=False)
        self.game.modes.add(self.drops)

        # Virtual locks are needed when there are more balls physically locked
        # than the player has locked through play.  This happens when
        # another player locks more balls than the current player.  Use
        # Virtual locks > 0 for this case.
        # Use Virtual locks < 0 when the player has locked more balls than are
        # physically locked.  This could happen when another player plays
        # multiball and empties the locked balls.
        if self.deadworld_mod_installed and self.num_locks_lit > 0:
            self.virtual_locks_needed = self.game.deadworld.num_balls_locked - self.num_balls_locked
        else:
            self.virtual_locks_needed = 0

        if self.virtual_locks_needed < 0:
            # enable the lock so the player can quickly re-lock
            self.enable_lock()
            self.display_text('Lock is Lit!')
            self.num_balls_locked = self.game.deadworld.num_balls_locked
            #self.num_locks_lit = 0 - self.virtual_locks_needed
        elif self.virtual_locks_needed > 0:
            self.enable_virtual_lock()
        elif self.num_balls_locked < self.num_locks_lit:
            self.enable_lock()
            self.display_text('Lock is Lit!')

    def mode_stopped(self):
        # save player state
        player = self.game.current_player()
        player.setState('multiball_state', self.state)
        player.setState('multiball_num_balls_locked', self.num_balls_locked)
        player.setState('multiball_num_locks_lit', self.num_locks_lit)
        player.setState('multiball_num_times_played', self.num_times_played)
        player.setState('multiball_lock_level', self.lock_level)
        player.setState('multiball_jackpot_collected', self.jackpot_collected)

        self.cancel_delayed(name='voice instructions')
        self.game.modes.remove(self.drops)

    def install_rule(self, enable):
        switch_num = self.game.switches['leftRampEnter'].number
        #self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, enable)
        self.game.install_switch_rule_coil_schedule(switch_num, 'closed_debounced', 'diverter', 0x00000fff, 1, True, True, enable)
        switch_num = self.game.switches['leftRampEnterAlt'].number
        #self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, enable)
        self.game.install_switch_rule_coil_schedule(switch_num, 'closed_debounced', 'diverter', 0x00000fff, 1, True, True, enable)

    def on_drops_advance(self, mode):
        pass

    def is_active(self):
        return self.state == 'multiball'

    def start_multiball(self):
        self.game.sound.play_voice('multiball')
        self.num_balls_locked = 0
        self.state = 'multiball'
        self.display_text('Multiball!')
        self.start_callback()
        self.num_left_ramp_shots_hit = 0
        self.num_left_ramp_shots_needed = 1
        self.jackpot_lit = False
        self.game.update_lamps()

    def end_multiball(self):
        self.cancel_delayed(name='trip_check')
        self.game.coils.flasherGlobe.disable()
        self.state = 'load'
        self.end_callback()
        self.jackpot_lit = False
        self.reset_active_drops()
        self.num_locks_lit = 0
        self.lock_level += 1
        self.game.update_lamps()

    def reset_active_drops(self):
        if (self.game.switches.dropTargetJ.is_active() or
                self.game.switches.dropTargetU.is_active() or
                self.game.switches.dropTargetD.is_active() or
                self.game.switches.dropTargetG.is_active() or
                self.game.switches.dropTargetE.is_active()):
            self.game.coils.resetDropTarget.pulse(40)

    def trip_check(self):
        if self.game.switches.dropTargetD.is_inactive():
            self.game.coils.tripDropTarget.pulse(40)
            self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def jackpot(self):
        self.game.score(100000)
        self.num_left_ramp_shots_needed += 1
        self.game.update_lamps()

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        if self.jackpot_lit:
            self.game.coils.tripDropTarget.pulse(40)
            self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def sw_subwayEnter2_active(self, sw):
        if self.jackpot_lit:
            self.display_text('Jackpot!')
            self.game.sound.play_voice('jackpot')
            self.jackpot_lit = False
            self.delay(name='jackpot', event_type=None, delay=1.5, handler=self.jackpot)
            self.num_left_ramp_shots_hit = 0
            self.jackpot_collected = True
            self.game.update_lamps()
            self.game.lampctrl.play_show('jackpot', False, self.game.update_lamps)

    def reset_jackpot_collected(self):
        self.jackpot_collected = False

    def display_text(self, text):
        self.banner_layer.set_text(text, 3)

    def pause(self):
        self.paused = True
        if self.lock_enabled:
            self.disable_lock()

    def resume(self):
        self.paused = False
        if self.lock_enabled:
            self.game.status('resuming')
            self.enable_lock()

    def disable_lock(self):
        self.game.deadworld.disable_lock()
        self.lock_enabled = 0
        self.install_rule(enable=False)

    def enable_lock(self):
        self.game.sound.play_voice('locks lit')
        self.game.deadworld.enable_lock()
        self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)
        self.lock_enabled = True
        self.install_rule(enable=True)

    def enable_virtual_lock(self):
        self.game.deadworld.enable_lock()
        self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)
        # Make sure deadworld will eject a ball if one happens to enter.
        self.lock_enabled = False

    def multiball_launch_callback(self):
        ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']
        # Balls launched are already in play.
        local_num_balls_to_save = self.game.trough.num_balls_in_play
        self.game.ball_save.callback = None
        self.game.ball_save.start(num_balls_to_save=local_num_balls_to_save, time=ball_save_time, now=True, allow_multiple_saves=True)

    def start_ballsave(self):
        ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']
        local_num_balls_to_save = self.game.trough.num_balls_in_play + 2
        self.game.ball_save.callback = None
        self.game.ball_save.start(num_balls_to_save=local_num_balls_to_save, time=ball_save_time, now=True, allow_multiple_saves=True)

    def sw_leftRampToLock_active(self, sw):
        if not self.lock_enabled:
            self.possibly_light_lock('sneaky')
        if self.lock_enabled:
            self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)
            self.num_balls_locked += 1
            self.display_text('Ball ' + str(self.num_balls_locked) + ' Locked!')
            if self.num_balls_locked == 1:
                self.game.sound.play_voice('ball 1 locked')
            elif self.num_balls_locked == 2:
                self.game.sound.play_voice('ball 2 locked')

            if self.num_balls_locked == 3:
                self.disable_lock()
                if self.deadworld_mod_installed:
                    self.game.deadworld.eject_balls(3)
                    #commenting out launch, use 3 ball MB.
                    #self.game.trough.launch_balls(1, self.multiball_launch_callback)
                    #Added for 3 ball MB with no launch
                    self.start_ballsave()
                    # Need to convert previously locked balls to balls in play.
                    # Impossible for trough logic to do it itself, as is.
                    self.game.trough.num_balls_in_play += 2
                else:
                    self.game.deadworld.eject_balls(1)
                    self.game.ball_save.start_lamp()
                    # Was 3 (for 4 ball MB), now 2 for 3 ball MB.
                    self.game.trough.launch_balls(2, self.multiball_launch_callback)
                    self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
                self.start_multiball()
            elif self.num_balls_locked == self.num_locks_lit:
                self.disable_lock()
                if self.deadworld_mod_installed:
                    # Use stealth launch so another ball isn't counted in play.
                    self.game.ball_save.callback = None
                    self.game.trough.launch_balls(1, self.game.no_op_callback, stealth=True)
                else:
                    self.game.deadworld.eject_balls(1)

            # When not yet multiball, launch a new ball each time
            # one is locked.
            elif self.deadworld_mod_installed:
                # Use stealth launch so another ball isn't counted in play.
                self.game.ball_save.callback = None
                self.game.trough.launch_balls(1, self.game.no_op_callback, stealth=True)
            else:
                self.game.deadworld.eject_balls(1)

        else:
            #if self.deadworld_mod_installed:
            self.game.deadworld.eject_balls(1)
        self.game.update_lamps()

    def possibly_light_lock(self, mode):
        dw_balls_locked_adj = 0
        if mode == 'sneaky':
            dw_balls_locked_adj = 1
            self.game.set_status('Sneaky Lock!')

        if self.state == 'load' and not self.paused:
            # Prepare to lock
            if self.num_locks_lit < 3:
                if self.lock_level == 1:
                    self.num_locks_lit = 3
                    if self.deadworld_mod_installed:
                        self.virtual_locks_needed = (self.game.deadworld.num_balls_locked - dw_balls_locked_adj)
                else:
                    self.num_locks_lit += 1
                    # Use calculations if deadwolrd is installed.

                    new_num_to_lock = self.num_locks_lit - self.num_balls_locked
                    extra_in_dw = (self.game.deadworld.num_balls_locked - dw_balls_locked_adj) - self.num_balls_locked
                    if extra_in_dw >= new_num_to_lock:
                        self.virtual_locks_needed = new_num_to_lock
                    else:
                        self.virtual_locks_needed = extra_in_dw

                # Don't enable locks if doing virtual locks.
                if self.virtual_locks_needed <= 0:
                    self.enable_lock()
                    self.display_text('Lock is Lit!')
                else:
                    self.enable_virtual_lock()
                    self.display_text('Lock is Lit!')

            self.game.update_lamps()

    def sw_leftRampExit_active(self, sw):
        if self.state == 'load':
            if self.virtual_locks_needed > 0:
                self.num_balls_locked += 1
                self.virtual_locks_needed -= 1
                if (self.virtual_locks_needed == 0 and
                        self.num_balls_locked < self.num_locks_lit):
                    self.enable_lock()
        elif self.state == 'multiball':
            if not self.jackpot_lit:
                self.num_left_ramp_shots_hit += 1
                if self.num_left_ramp_shots_hit == self.num_left_ramp_shots_needed:
                    self.jackpot_lit = True
                    self.game.sound.play_voice('jackpot is lit')
                else:
                    self.game.sound.play_voice('again')
                if self.game.switches.dropTargetD.is_inactive():
                    self.game.coils.tripDropTarget.pulse(40)
                    self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)
        self.game.update_lamps()

    def update_lamps(self):
        if self.state == 'load':
            for i in range(1, 4):
                lampname = 'lock' + str(i)
                if self.num_locks_lit >= i and not self.paused:
                    if self.num_balls_locked >= i:
                        self.game.lamps[lampname].enable()
                    else:
                        self.game.lamps[lampname].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
                else:
                    self.game.lamps[lampname].disable()

        elif self.state == 'multiball' and not self.jackpot_lit:
            self.game.lamps.lock1.schedule(schedule=0x000f000f, cycle_seconds=0, now=False)
            self.game.lamps.lock2.schedule(schedule=0x003c003c, cycle_seconds=0, now=False)
            self.game.lamps.lock3.schedule(schedule=0x00f000f0, cycle_seconds=0, now=False)

        else:
            self.game.lamps.lock1.disable()
            self.game.lamps.lock2.disable()
            self.game.lamps.lock3.disable()

        if self.jackpot_lit:
            self.game.lamps.multiballJackpot.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
        else:
            self.game.lamps.multiballJackpot.disable()

        if self.state == 'multiball':
            self.game.coils.flasherGlobe.schedule(schedule=0x88888888, cycle_seconds=0, now=True)

    def how_many_balls_locked(self):
        return self.num_balls_locked

    def stop_globe(self):
        self.game.deadworld.mode_stopped()
