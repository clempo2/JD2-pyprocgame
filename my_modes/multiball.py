from procgame.game import Mode
from procgame.modes import BasicDropTargetBank

class Multiball(Mode):
    """Multiball activated by locking balls in the Deadworld planet"""

    def __init__(self, game, priority):
        super(Multiball, self).__init__(game, priority)

        self.deadworld_mod_installed = self.game.user_settings['Machine']['Deadworld mod installed']
        self.ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']

        self.drops = BasicDropTargetBank(self.game, priority=priority + 1, prefix='dropTarget', letters='JUDGE')
        self.drops.on_advance = self.on_drops_advance
        self.drops.on_completed = self.possibly_light_lock
        self.drops.auto_reset = True

    def mode_started(self):
        # restore player state
        player = self.game.current_player()
        self.num_balls_locked = player.getState('num_balls_locked', 0)
        self.num_locks_lit = player.getState('num_locks_lit', 0)
        self.multiball_played = player.getState('multiball_played', False)

        self.state = 'load'
        self.jackpot_lit = False
        self.lock_enabled = False
        self.num_ramp_shots = 0
        self.ramp_shots_required = 1

        self.game.deadworld.stop_spinning()
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
            self.game.base_play.display('Lock is Lit')
            self.num_balls_locked = self.game.deadworld.num_balls_locked
        elif self.virtual_locks_needed > 0:
            self.enable_virtual_lock()
        elif self.num_balls_locked < self.num_locks_lit:
            self.enable_lock()
            self.game.base_play.display('Lock is Lit')

    def mode_stopped(self):
        # save player state
        player = self.game.current_player()
        player.setState('multiball_active', player.getState('multiball_active', 0) & ~0x1) # in case of tilt
        player.setState('num_balls_locked', self.num_balls_locked)
        player.setState('num_locks_lit', self.num_locks_lit)
        player.setState('multiball_played', self.multiball_played)
        # multiball_jackpot_collected is sticky until it is reset at the end of Ultimate Challenge

        self.game.remove_modes([self.drops])

    def reset(self):
        self.game.setPlayerState('multiball_jackpot_collected', False)

    def on_drops_advance(self, mode):
        pass

    def start_multiball(self):
        self.game.sound.play_voice('multiball')
        self.delay(name='multiball_instructions', event_type=None, delay=10, handler=self.multiball_instructions)
        self.state = 'multiball'
        self.game.base_play.display('Multiball')
        self.num_balls_locked = 0
        self.num_ramp_shots = 0
        self.ramp_shots_required = 1
        self.jackpot_lit = False
        self.start_callback()
        self.game.addPlayerState('multiball_active', 0x1)
        self.game.update_lamps()

    def end_multiball(self):
        self.cancel_delayed(['trip_check', 'multiball_instructions'])
        self.game.coils.flasherGlobe.disable()
        self.state = 'load'
        self.num_locks_lit = 0
        self.jackpot_lit = False
        self.multiball_played = True
        self.game.addPlayerState('multiball_active', -0x1)
        self.end_callback()
        self.reset_active_drops()
        self.game.update_lamps()

    def multiball_instructions(self):
        voice = 'shoot the subway' if self.jackpot_lit else 'shoot the left ramp'
        self.game.sound.play_voice(voice)
        self.delay(name='multiball_instructions', event_type=None, delay=10, handler=self.multiball_instructions)

    def install_rule(self, enable):
        switch_num = self.game.switches['leftRampEnter'].number
        self.game.install_switch_rule_coil_schedule(switch_num, 'closed_debounced', 'diverter', 0x00000fff, 1, True, True, enable)
        switch_num = self.game.switches['leftRampEnterAlt'].number
        self.game.install_switch_rule_coil_schedule(switch_num, 'closed_debounced', 'diverter', 0x00000fff, 1, True, True, enable)

    def stop_globe(self):
        self.game.deadworld.stop_spinning()

    def evt_ball_drained(self):
        # End multiball if there is now only one ball in play
        if self.state == 'multiball':
            if self.game.trough.num_balls_in_play == 1:
                self.end_multiball()

    def light_jackpot(self):
        self.jackpot_lit = True
        self.game.sound.play_voice('jackpot is lit')
        self.trip_check()

    def jackpot(self):
        self.game.setPlayerState('multiball_jackpot_collected', True)
        self.game.base_play.display('Jackpot')
        self.game.sound.play_voice('jackpot')
        self.game.lampctrl.play_show('jackpot', False, self.game.update_lamps)
        self.num_ramp_shots = 0
        self.ramp_shots_required += 1
        self.game.score(100000)

    def disable_lock(self):
        self.lock_enabled = False
        self.install_rule(enable=False)

    def enable_lock(self):
        self.lock_enabled = True
        self.game.deadworld.enable_lock()
        self.install_rule(enable=True)
        self.game.sound.play_voice('locks lit')
        self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)

    def enable_virtual_lock(self):
        # Make sure deadworld will eject a ball if one happens to enter.
        self.lock_enabled = False
        self.game.deadworld.enable_lock()
        self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)

    def possibly_light_lock(self, mode):
        # called when drops are completed or there was a sneaky lock
        dw_balls_locked_adj = 0
        if mode == 'sneaky':
            dw_balls_locked_adj = 1
            self.game.set_status('Sneaky Lock')

        if self.state == 'load':
            # Prepare to lock
            if self.num_locks_lit < 3:
                if self.multiball_played:
                    self.num_locks_lit += 1
                    new_num_to_lock = self.num_locks_lit - self.num_balls_locked
                    extra_in_dw = (self.game.deadworld.num_balls_locked - dw_balls_locked_adj) - self.num_balls_locked
                    self.virtual_locks_needed = min(new_num_to_lock, extra_in_dw)
                else:
                    # first time player starts multiball
                    self.num_locks_lit = 3
                    if self.deadworld_mod_installed:
                        self.virtual_locks_needed = self.game.deadworld.num_balls_locked - dw_balls_locked_adj

                # Don't enable locks if doing virtual locks.
                if self.virtual_locks_needed <= 0:
                    self.enable_lock()
                else:
                    self.enable_virtual_lock()
                self.game.base_play.display('Lock is Lit')

            self.game.update_lamps()

    def multiball_launch_callback(self):
        # Balls launched are already in play.
        local_num_balls_to_save = self.game.trough.num_balls_in_play
        self.game.ball_save_start(num_balls_to_save=local_num_balls_to_save, time=self.ball_save_time, now=True, allow_multiple_saves=True)

    def start_ballsave(self):
        local_num_balls_to_save = self.game.trough.num_balls_in_play + 2
        self.game.ball_save_start(num_balls_to_save=local_num_balls_to_save, time=self.ball_save_time, now=True, allow_multiple_saves=True)

    def reset_active_drops(self):
        if (self.game.switches.dropTargetJ.is_active() or
                self.game.switches.dropTargetU.is_active() or
                self.game.switches.dropTargetD.is_active() or
                self.game.switches.dropTargetG.is_active() or
                self.game.switches.dropTargetE.is_active()):
            self.game.coils.resetDropTarget.pulse(40)

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        # newly detected raised letter D
        if self.jackpot_lit:
            self.trip_drop_target()

    def trip_drop_target(self):
        # drop letter D and run a delayed handler to verify it stayed down
        self.game.coils.tripDropTarget.pulse(40)
        self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def trip_check(self):
        if self.game.switches.dropTargetD.is_inactive():
            self.trip_drop_target()

    def sw_leftRampToLock_active(self, sw):
        if self.lock_enabled:
            self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)
            self.num_balls_locked += 1
            self.game.base_play.display('Ball ' + str(self.num_balls_locked) + ' Locked')
            if self.num_balls_locked <= 2:
                self.game.sound.play_voice('ball ' + str(self.num_balls_locked) + ' locked')

            if self.num_balls_locked == 3:
                self.disable_lock()
                if self.deadworld_mod_installed:
                    # 3 ball multiball with all balls coming from deadworld planet
                    self.game.deadworld.eject_balls(3)
                    self.start_ballsave()
                    # Need to convert previously locked balls to balls in play.
                    # Impossible for trough logic to do it itself, as is.
                    self.game.trough.num_balls_in_play += 2
                else:
                    self.game.deadworld.eject_balls(1)
                    self.game.ball_save.start_lamp()
                    # launch 2 more balls for 3 ball multiball
                    self.game.trough.launch_balls(2, self.multiball_launch_callback)
                    self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
                self.start_multiball()
            elif self.num_balls_locked == self.num_locks_lit:
                self.disable_lock()
                if self.deadworld_mod_installed:
                    # Use stealth launch so another ball isn't counted in play.
                    self.game.trough.launch_balls(1, self.game.no_op_callback, stealth=True)
                else:
                    self.game.deadworld.eject_balls(1)

            # When not yet multiball, launch a new ball each time one is locked.
            elif self.deadworld_mod_installed:
                # Use stealth launch so another ball isn't counted in play.
                self.game.trough.launch_balls(1, self.game.no_op_callback, stealth=True)
            else:
                self.game.deadworld.eject_balls(1)

        else:
            self.possibly_light_lock('sneaky')
            self.game.deadworld.eject_balls(1)

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
                self.num_ramp_shots += 1
                if self.num_ramp_shots == self.ramp_shots_required:
                    self.light_jackpot()
                else:
                    self.game.sound.play_voice('again')

        self.game.update_lamps()

    def sw_subwayEnter2_active(self, sw):
        if self.jackpot_lit:
            self.jackpot_lit = False
            self.jackpot()
            self.game.update_lamps()

    def update_lamps(self):
        if self.state == 'load':
            for i in range(1, 4):
                if i <= self.num_balls_locked:
                    style = 'on'
                elif i <= self.num_locks_lit:
                    style = 'slow'
                else:
                    style = 'off'
                self.game.drive_lamp('lock' + str(i), style)

        elif self.state == 'multiball':
            self.game.coils.flasherGlobe.schedule(schedule=0x88888888, cycle_seconds=0, now=True)

            schedules = [0, 0, 0] if self.jackpot_lit else [0x000f000f, 0x003c003c, 0x00f000f0]
            for i in range(1, 4):
                self.game.lamps['lock' + str(i)].schedule(schedules[i-1], cycle_seconds=0, now=False)

        style = 'slow' if self.jackpot_lit else 'off'
        self.game.drive_lamp('multiballJackpot', style)
