from procgame.game import Mode
from procgame.modes import BasicDropTargetBank

class Multiball(Mode):
    """3-ball Multiball activated by locking balls in the Deadworld planet"""

    def __init__(self, game, priority):
        super(Multiball, self).__init__(game, priority)

        self.deadworld_mod_installed = self.game.user_settings['Machine']['Deadworld mod installed']
        self.ball_save_time = self.game.user_settings['Gameplay']['Multiball ballsave time']

        self.drops = BasicDropTargetBank(self.game, priority=priority + 1, prefix='dropTarget', letters='JUDGE')
        self.drops.on_advance = self.on_drops_advance
        self.drops.on_completed = self.on_drops_completed
        self.drops.auto_reset = False

    def mode_started(self):
        # restore player state
        player = self.game.current_player()
        self.num_balls_locked = player.getState('num_balls_locked', 0)
        self.num_locks_lit = player.getState('num_locks_lit', 0)
        # multiball_played, multiball_jackpot_collected and multiball_active are accessed directly in the player state

        if self.deadworld_mod_installed and self.game.deadworld.num_balls_locked < self.num_balls_locked:
            # The planet holds fewer balls than the player has locked balls.
            # The player must unfortunately re-lock the balls he lost to another player
            self.num_balls_locked = self.game.deadworld.num_balls_locked

        self.state = 'load'
        self.jackpot_lit = False
        self.physical_lock_enabled = False
        self.num_ramp_shots = 0
        self.ramp_shots_required = 1
        self.game.deadworld.stop_spinning()
        self.game.modes.add(self.drops)
        self.configure_lock()

    def mode_stopped(self):
        # remove switch rule
        self.disable_lock()

        # save player state
        player = self.game.current_player()
        player.setState('multiball_active', player.getState('multiball_active', 0) & ~0x1) # in case of tilt
        player.setState('num_balls_locked', self.num_balls_locked)
        player.setState('num_locks_lit', self.num_locks_lit)

        self.game.remove_modes([self.drops])

    def reset(self):
        # multiball_jackpot_collected is sticky until it is reset at the end of Ultimate Challenge
        self.game.setPlayerState('multiball_jackpot_collected', False)

    def start_multiball(self):
        # start a 3-ball multiball or up to 4 balls when stacked with BlockWar
        self.state = 'multiball'
        self.game.base_play.display('Multiball')
        self.game.sound.play_voice('multiball')
        self.delay(name='multiball_instructions', event_type=None, delay=10, handler=self.multiball_instructions)
        self.num_locks_lit = 0
        self.num_balls_locked = 0
        self.num_ramp_shots = 0
        self.ramp_shots_required = 1
        self.jackpot_lit = False
        self.disable_lock()

        # launch the balls for a 3 ball multiball and up to 4 balls when stacked with BlockWar
        if self.deadworld_mod_installed:
            # all balls coming from deadworld planet
            self.game.deadworld.eject_balls(3)
            # Need to convert previously locked balls to balls in play.
            # Impossible for trough logic to do it itself.
            self.game.trough.num_balls_in_play += 2
        else:
            # 1 ball from the planet and 2 from the trough
            self.game.deadworld.eject_balls(1)
            self.game.launch_balls(2)

        self.game.ball_save_start(time=self.ball_save_time, now=True, allow_multiple_saves=True)
        self.start_callback()
        self.game.addPlayerState('multiball_active', 0x1)
        self.game.update_lamps()

    def end_multiball(self):
        self.state = 'load'
        self.cancel_delayed(['trip_check', 'multiball_instructions'])
        self.game.coils.flasherGlobe.disable()
        self.jackpot_lit = False
        self.game.setPlayerState('multiball_played', True)
        self.game.addPlayerState('multiball_active', -0x1)
        self.end_callback()
        self.drops.reset_drop_target_bank()
        self.game.update_lamps()

    def evt_ball_drained(self):
        # End multiball if there is now only one ball in play
        if self.state == 'multiball':
            if self.game.num_balls_requested() == 1:
                self.end_multiball()

    def multiball_instructions(self):
        voice = 'shoot the subway' if self.jackpot_lit else 'shoot the left ramp'
        self.game.sound.play_voice(voice)
        self.delay(name='multiball_instructions', event_type=None, delay=10, handler=self.multiball_instructions)

    def install_diverter_rule(self, enable):
        self.physical_lock_enabled = enable
        for switch in ['leftRampEnter', 'leftRampEnterAlt']:
            switch_num = self.game.switches[switch].number
            self.game.install_switch_rule_coil_schedule(switch_num, 'closed_debounced', 'diverter', 0x00000fff, 1, True, True, enable)

    def configure_lock(self, sneaky_ball_adjust=0):
        # Decide between enabling a physical lock, a virtual lock or disabling locks altogether.
        # Without the Deadworld mod, we lock each ball physically and eject it immediately.
        #   We never use a virtual lock unlike the original game.
        # With the Deadworld mod, we physically lock 3 balls.
        #   A virtual lock happens if the mod-ed planet holds more balls than
        #   the player has locked balls, allowing the count to catch up to the planet.
        # The planet counts a sneaky lock as a real lock.
        #   If we know there is a sneaky lock ball currently being ejected,
        #   we need to remove it from the count to get the real number of locked balls in the planet.

        # make sure multiball did not start in the meantime, this can happen if BlockWar is running
        if self.state == 'load':
            dw_num_balls_locked = self.game.deadworld.num_balls_locked - sneaky_ball_adjust
            if (self.deadworld_mod_installed and self.num_locks_lit > 0 and
                        dw_num_balls_locked > self.num_balls_locked):
                self.virtual_locks_needed = dw_num_balls_locked - self.num_balls_locked
            else:
                self.virtual_locks_needed = 0
    
            if self.num_balls_locked < self.num_locks_lit:
                self.enable_lock()
            else:
                self.disable_lock()

    def enable_lock(self):
        self.install_diverter_rule(enable=self.virtual_locks_needed == 0)
        self.game.deadworld.start_spinning()
        self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)

    def disable_lock(self):
        self.install_diverter_rule(enable=False)

    def light_lock(self, sneaky_ball_adjust=0):
        if self.state == 'load' and self.num_locks_lit < 3:
            self.num_locks_lit = (self.num_locks_lit + 1) if self.game.getPlayerState('multiball_played', False) else 3
            self.configure_lock(sneaky_ball_adjust)
            self.game.base_play.display('Lock is Lit')
            self.game.sound.play_voice('locks lit')
            self.game.update_lamps()

    def ball_locked(self, launch_ball=True):
        # a ball was locked through a physical or a virtual lock
        # BEWARE: This method can only be called when self.state is 'load'
        self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)

        self.num_balls_locked += 1
        if self.num_balls_locked == 3:
            self.start_multiball()
        else:
            self.game.base_play.display('Ball ' + str(self.num_balls_locked) + ' Locked')
            self.game.sound.play_voice('ball ' + str(self.num_balls_locked) + ' locked')
            self.configure_lock()

            if launch_ball:
                # Not yet multiball, put one ball back in play
                if self.deadworld_mod_installed:
                    # launch a new ball each time a ball is physically locked.
                    # Use stealth launch so another ball isn't counted in play.
                    self.game.trough.launch_balls(1, self.game.no_op_callback, stealth=True)
                else:
                    # eject the ball immediately since an un-moded planet can't physically hold balls
                    self.game.deadworld.eject_balls(1, self.configure_lock)

            self.game.update_lamps()

    def sneaky_lock(self):
        # A ball trickled into the ramp to lock when the physical lock is disabled
        # Award a lock light and eject the sneaky ball
        # BEWARE: This method can only be called when self.state is 'load'
        self.game.set_status('SNEAKY LOCK')
        self.light_lock(sneaky_ball_adjust=1)
        self.game.deadworld.eject_balls(1, self.configure_lock)

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

    def on_drops_advance(self, drops):
        pass

    def on_drops_completed(self, drops):
        drops.animated_reset(seconds=1.0)
        self.light_lock()

    def sw_leftRampToLock_active(self, sw):
        if self.state == 'load':
            if self.physical_lock_enabled:
                self.ball_locked()
            else:
                self.sneaky_lock()
        else:
            self.game.deadworld.eject_balls(1)

    def sw_leftRampExit_active(self, sw):
        if self.state == 'load':
            if self.virtual_locks_needed > 0:
                self.virtual_locks_needed -= 1
                self.ball_locked(launch_ball=False)
        elif self.state == 'multiball':
            if not self.jackpot_lit:
                self.num_ramp_shots += 1
                if self.num_ramp_shots == self.ramp_shots_required:
                    self.light_jackpot()
                else:
                    self.game.sound.play_voice('again')

    def sw_subwayEnter2_active(self, sw):
        if self.jackpot_lit:
            self.jackpot_lit = False
            self.jackpot()
            self.game.update_lamps()

    def light_jackpot(self):
        self.jackpot_lit = True
        self.game.sound.play_voice('jackpot is lit')
        self.trip_check()
        self.game.update_lamps()

    def jackpot(self):
        self.game.setPlayerState('multiball_jackpot_collected', True)
        self.game.base_play.display('Jackpot')
        self.game.sound.play_voice('jackpot')
        self.game.lampctrl.play_show('jackpot', False, self.game.update_lamps)
        self.game.score(100000)
        self.num_ramp_shots = 0
        self.ramp_shots_required += 1

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

            # the 3 lock lights are off or are chasing towards the ramp
            schedules = [0, 0, 0] if self.jackpot_lit else [0x000f000f, 0x003c003c, 0x00f000f0]
            for i in range(1, 4):
                self.game.lamps['lock' + str(i)].schedule(schedules[i-1], cycle_seconds=0, now=False)

        style = 'slow' if self.jackpot_lit else 'off'
        self.game.drive_lamp('multiballJackpot', style)
