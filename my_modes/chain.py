from random import randint
from time import time
from procgame.game import AdvancedMode
from timer import TimedMode

class Chain(AdvancedMode):
    """Controls the progress through the chain modes"""

    def __init__(self, game, priority):
        super(Chain, self).__init__(game, priority)

        pursuit = Pursuit(game, priority + 1)
        blackout = Blackout(game, priority + 1)
        sniper = Sniper(game, priority + 1)
        battle_tank = BattleTank(game, priority + 1)
        impersonator = Impersonator(game, priority + 1)
        meltdown = Meltdown(game, priority + 1)
        safecracker = Safecracker(game, priority + 1)
        manhunt = Manhunt(game, priority + 1)
        stakeout = Stakeout(game, priority + 1)

        self.all_chain_modes = [pursuit, blackout, sniper, battle_tank, impersonator, meltdown, safecracker, manhunt, stakeout]
        for mode in self.all_chain_modes:
            mode.exit_callback = self.chain_mode_ended

        self.hurry_up = ChainHurryUp(game, priority + 1)
        self.hurry_up.exit_callback = self.hurry_up_ended

    def reset_progress(self):
        # Erase all progress to start over when ultimate challenge ends,
        # except num_chain_features and num_hurry_ups continue to accrue
        player = self.game.current_player()
        player.setState('modes_remaining', self.all_chain_modes[:])
        player.setState('modes_remaining_ptr', 0)
        player.setState('chain_complete', False)

    def evt_player_added(self, player):
        player.setState('modes_remaining', self.all_chain_modes[:])
        player.setState('modes_remaining_ptr', 0)
        player.setState('chain_active', 0)
        player.setState('chain_complete', False)
        player.setState('num_chain_features', 0)

    def mode_started(self):
        # restore player state
        player = self.game.current_player()
        self.modes_remaining = player.getState('modes_remaining')
        self.modes_remaining_ptr = player.getState('modes_remaining_ptr')

        self.mode = None

    def mode_stopped(self):
        # save player state
        player = self.game.current_player()
        player.setState('modes_remaining', self.modes_remaining)
        player.setState('modes_remaining_ptr', self.modes_remaining_ptr)

        if self.mode != None:
            self.game.remove_modes([self.mode])
            self.game.setPlayerState('chain_active', 0)
        self.game.remove_modes([self.hurry_up])

    def sw_slingL_active(self, sw):
        self.rotate_modes(-1)

    def sw_slingR_active(self, sw):
        self.rotate_modes(1)

    def sw_fireR_active(self, sw):
        self.rotate_modes(1)

    def sw_fireL_active(self, sw):
        self.rotate_modes(-1)

    # move the pointer to the left or right in the list with pacman wrap-around
    def rotate_modes(self, step):
        length = len(self.modes_remaining)
        if length > 0:
            self.modes_remaining_ptr = (self.modes_remaining_ptr + step + length) % length
        self.game.update_lamps()

    def pause(self):
        if self.mode:
            self.mode.pause()

    def resume(self):
        if self.mode:
            self.mode.resume()

    # start a new chain mode after the display becomes available
    def start_chain_mode(self):
        block_busy_until = self.game.getPlayerState('block_busy_until')
        now = time()
        if block_busy_until > now:
            # wait for block mode to finish talking and/or displaying on the screen
            # this is a work-around for the pyprocgame SoundController that does not queue voice callouts
            self.delay('start_chain_mode', None, block_busy_until - now, self.start_chain_mode)
            return

        self.mode = self.modes_remaining[self.modes_remaining_ptr]
        self.game.setPlayerState('chain_active', 1)
        self.modes_remaining.remove(self.mode)
        if len(self.modes_remaining) == 0:
            self.game.setPlayerState('chain_complete', True)
        self.rotate_modes(0)
        self.game.adjPlayerState('num_chain_features', 1)

        self.game.base_play.regular_play.state = 'mode'
        self.game.modes.add(self.mode)
        self.game.update_lamps()

        # Put the ball back into play
        self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR')

    # called when the mode has completed or expired but before the hurry up
    def chain_mode_ended(self, success):
        self.game.remove_modes([self.mode])

        if success:
            # mode was completed successfully, start hurry up award
            self.game.adjPlayerState('num_hurry_ups', 1)
            self.game.modes.add(self.hurry_up)
            self.game.update_lamps()
        else:
            # mode not successful, skip the hurry up
            self.hurry_up_ended(False)

    # called when the mode is over including the hurry up
    def hurry_up_ended(self, success):
        if success:
            # award a block and/or some points
            if self.game.getPlayerState('blocks_complete'):
                self.game.score(10000)
            else:
                self.game.base_play.regular_play.city_blocks.city_block.block_complete()

            if self.game.getPlayerState('multiball_active'):
                self.game.score(100000)

        self.mode = None
        self.game.setPlayerState('chain_active', 0)

        self.game.remove_modes([self.hurry_up])
        self.game.base_play.regular_play.chain_mode_completed()
        self.game.update_lamps()

    def update_lamps(self):
        self.game.enable_gi(True)
        for mode in self.all_chain_modes:
            style = 'off' if mode in self.modes_remaining else 'on'
            self.game.drive_lamp(mode.lamp_name, style)
        if len(self.modes_remaining) > 0:
            blinking_mode = self.mode if self.mode else self.modes_remaining[self.modes_remaining_ptr]
            self.game.drive_lamp(blinking_mode.lamp_name, 'slow')


class ChainHurryUp(TimedMode):
    """Hurry up to subway after a chain mode is successfully completed"""

    def __init__(self, game, priority):
        super(ChainHurryUp, self).__init__(game, priority, mode_time=0, name='Hurry Up',
                    instructions='Shoot subway', num_shots_required=1)

    def mode_started(self):
        self.mode_time = self.game.user_settings['Gameplay']['Time for Hurry Up']
        super(ChainHurryUp, self).mode_started()
        self.game.coils.tripDropTarget.pulse()
        self.trip_check()
        self.already_collected = False

    def play_music(self):
        # don't change the music for the hurry up, that mode is too short
        pass

    def update_status(self):
        pass

    def expired(self):
        self.exit_callback(False)

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        # newly detected raised letter D
        self.trip_drop_target()

    def trip_drop_target(self):
        # drop letter D and run a delayed handler to verify it stayed down
        self.game.coils.tripDropTarget.pulse()
        self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def trip_check(self):
        if self.game.switches.dropTargetD.is_inactive():
            self.trip_drop_target()

    def update_lamps(self):
        self.game.drive_lamp('pickAPrize', 'fast')

    def sw_subwayEnter1_closed(self, sw):
        self.collect_hurry_up()

    # Ball might jump over first switch.  Use 2nd switch as a catch all.
    def sw_subwayEnter2_closed(self, sw):
        if not self.already_collected:
            self.collect_hurry_up()

    def collect_hurry_up(self):
        self.game.sound.play_voice('good shot')
        self.cancel_delayed('trip_check')
        self.already_collected = True
        self.game.base_play.display('Well Done')
        self.exit_callback(True)


class ChainFeature(TimedMode):
    """Base class for the chain modes"""

    def __init__(self, game, priority, name, instructions, num_shot_options):
        super(ChainFeature, self).__init__(game, priority, 0, name, instructions)
        self.num_shot_options = num_shot_options
        class_name = self.__class__.__name__
        self.lamp_name = class_name[0].lower() + class_name[1:]  # lowercase first letter 

    def mode_started(self):
        self.mode_time = self.game.user_settings['Gameplay']['Time per chain feature']
        
        if self.num_shot_options:
            difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
            if not difficulty in ['easy', 'medium', 'hard']:
                difficulty = 'medium'
            self.num_shots_required = self.num_shot_options[difficulty]
        else:
            self.num_shots_required = 3

        super(ChainFeature, self).mode_started()

    def start_using_drops(self):
        self.game.base_play.regular_play.multiball.drops.paused = True
        self.reset_drops()

    def stop_using_drops(self):
        self.game.base_play.regular_play.multiball.drops.paused = False
        self.reset_drops()

    def reset_drops(self):
        self.game.base_play.regular_play.multiball.drops.reset_drop_target_bank()


class Pursuit(ChainFeature):
    """Pursuit chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':3, 'medium':4, 'hard':5}
        super(Pursuit, self).__init__(game, priority, 'Pursuit', 'Shoot L/R ramp shots', num_shot_options)

    def mode_started(self):
        super(Pursuit, self).mode_started()
        time = self.game.sound.play_voice('pursuit intro')
        self.delay(name='response', event_type=None, delay=time+0.5, handler=self.response)

    def play_music(self):
        # always pick the quieter music to make it easier to hear the intro voice of this mode
        self.game.sound.stop_music()
        self.game.sound.play_music('pursuit', loops=-1)

    def response(self):
        self.game.sound.play_voice('pursuit')

    def update_lamps(self):
        self.game.coils.flasherPursuitL.schedule(schedule=0x00030003, cycle_seconds=0, now=True)
        self.game.coils.flasherPursuitR.schedule(schedule=0x03000300, cycle_seconds=0, now=True)

    # Award shot if ball diverted for multiball.
    # Ensure it was a fast shot rather than one that just trickles in.
    def sw_leftRampToLock_active(self, sw):
        if self.game.switches.leftRampEnter.time_since_change() < 0.5:
            self.switch_hit()

    def sw_leftRampExit_active(self, sw):
        self.switch_hit()

    def sw_rightRampExit_active(self, sw):
        self.switch_hit()

    def switch_hit(self):
        self.num_shots += 1
        self.game.score(10000)
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.sound.play_voice('pursuit complete')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('good shot')

    def expired(self):
        self.game.sound.play_voice('pursuit failed')
        super(Pursuit, self).expired()


class Blackout(ChainFeature):
    """Blackout chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':2, 'medium':2, 'hard':3}
        super(Blackout, self).__init__(game, priority, 'Blackout', 'Shoot center ramp', num_shot_options)

    def mode_started(self):
        super(Blackout, self).mode_started()
        self.game.base_play.play_animation('blackout', frame_time=7)

    def update_lamps(self):
        self.game.enable_gi(False) # disable all gi except gi05 (Underworld)
        self.game.lamps.gi05.enable()
        self.game.lamps.blackoutJackpot.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
        if self.num_shots == self.num_shots_required - 1:
            self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

    def sw_centerRampExit_active(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required - 1:
            self.game.score(10000)
            self.game.update_lamps()
        elif self.num_shots == self.num_shots_required:
            self.game.score(30000)
            self.exit_callback(True)


class Sniper(ChainFeature):
    """Sniper chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':2, 'medium':2, 'hard':3}
        super(Sniper, self).__init__(game, priority, 'Sniper', 'Shoot Sniper Tower', num_shot_options)

    def mode_started(self):
        super(Sniper, self).mode_started()
        time = randint(2, 7)
        self.delay(name='gunshot', event_type=None, delay=time, handler=self.gunshot)

    def update_lamps(self):
        self.game.lamps.awardSniper.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

    def gunshot(self):
        self.game.sound.play_voice('sniper - shot')
        time = randint(2, 7)
        self.delay(name='gunshot', event_type=None, delay=time, handler=self.gunshot)

    def sw_popperR_active_for_300ms(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.game.base_play.play_animation('dredd_shoot_at_sniper', frame_time=5)
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.sound.play_voice('sniper - hit')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('sniper - miss')


class BattleTank(ChainFeature):
    """Battle tank chain mode"""

    def __init__(self, game, priority):
        super(BattleTank, self).__init__(game, priority, 'Battle Tank', 'Shoot all 3 battle tank shots', None)
        self.tank_lamp_names = ['tankLeft', 'tankCenter', 'tankRight']

    def mode_started(self):
        super(BattleTank, self).mode_started()
        self.shots = [1, 1, 1]
        self.game.sound.play_voice('tank intro')

    def update_lamps(self):
        for shot in range(0, 3):
            style = 'slow' if self.shots[shot] else 'off'
            self.game.drive_lamp(self.tank_lamp_names[shot], style)

    def sw_topRightOpto_active(self, sw):
        if self.game.switches.leftRollover.time_since_change() < 1:
            self.switch_hit(0)

    def sw_centerRampExit_active(self, sw):
        self.switch_hit(1)

    def sw_threeBankTargets_active(self, sw):
        self.switch_hit(2)

    def switch_hit(self, shot):
        if self.shots[shot]:
            self.shots[shot] = False
            self.game.update_lamps()
            if self.num_shots > 0:
                self.game.sound.stop('tank hit ' + str(self.num_shots))
            self.num_shots += 1
            self.game.sound.play_voice('tank hit ' + str(self.num_shots))
            self.game.score(10000)
            self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.score(50000)
            self.exit_callback(True)


class Impersonator(ChainFeature):
    """Bad impersonator chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':3, 'medium':5, 'hard':7}
        super(Impersonator, self).__init__(game, priority, 'Impersonator', 'Shoot lit drop targets', num_shot_options)

    def mode_started(self):
        super(Impersonator, self).mode_started()
        self.sound_active = False
        self.start_using_drops()
        time = self.game.sound.play('bad impersonator')
        #TODO
        time = 2
        self.delay(name='song_restart', event_type=None, delay=time+0.5, handler=self.song_restart)
        self.delay(name='boo_restart', event_type=None, delay=time+4, handler=self.boo_restart)
        self.delay(name='shutup_restart', event_type=None, delay=time+3, handler=self.shutup_restart)

    def mode_stopped(self):
        super(Impersonator, self).mode_stopped()
        self.stop_using_drops()
        for key in ['bad impersonator song', 'bad impersonator boo', 'bad impersonator shutup']:
            self.game.sound.stop(key)

    def play_music(self):
        # this mode talks all the time, we don't want any music
        pass

    def play_sound(self, key):
        # this mode talks all the time, keep quiet if stacked with multiball
        if not self.game.getPlayerState('multiball_active'):
            self.game.sound.play(key)

    def end_sound(self):
        self.sound_active = False

    def song_restart(self):
        self.play_sound('bad impersonator song')
        self.delay(name='song_restart', event_type=None, delay=6, handler=self.song_restart)

    def boo_restart(self):
        time = randint(2, 7)
        self.play_sound('bad impersonator boo')
        self.delay(name='boo_restart', event_type=None, delay=time, handler=self.boo_restart)

    def shutup_restart(self):
        time = randint(2, 7)
        self.play_sound('bad impersonator shutup')
        self.delay(name='shutup_restart', event_type=None, delay=time, handler=self.shutup_restart)

    def update_lamps(self):
        self.game.lamps.awardBadImpersonator.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
        self.game.disable_drop_lamps()
        # Timer is continuously updating self.timer
        time = self.timer % 6
        if time == 0:
            self.game.lamps.dropTargetJ.enable()
            self.game.lamps.dropTargetU.enable()
        elif time == 1 or time == 5:
            self.game.lamps.dropTargetU.enable()
            self.game.lamps.dropTargetD.enable()
        elif time == 2 or time == 4:
            self.game.lamps.dropTargetD.enable()
            self.game.lamps.dropTargetG.enable()
        elif time == 3:
            self.game.lamps.dropTargetG.enable()
            self.game.lamps.dropTargetE.enable()

    def sw_dropTargetJ_active(self, sw):
        self.switch_hit([0])

    def sw_dropTargetU_active(self, sw):
        self.switch_hit([0, 1, 5])

    def sw_dropTargetD_active(self, sw):
        self.switch_hit([1, 2, 4, 5])

    def sw_dropTargetG_active(self, sw):
        self.switch_hit([2, 3, 4])

    def sw_dropTargetE_active(self, sw):
        self.switch_hit([3])

    def switch_hit(self, matches):
        if self.timer % 6 in matches:
            self.num_shots += 1
            self.game.score(10000)
        self.game.sound.stop('bad impersonator song')
        if not self.sound_active:
            self.sound_active = True
            self.play_sound('bad impersonator ouch')
            self.delay(name='end_sound', event_type=None, delay=1, handler=self.end_sound)
        self.game.coils.resetDropTarget.pulse()
        self.check_for_completion()

    def timer_update(self, time):
        super(Impersonator, self).timer_update(time)
        self.game.update_lamps()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.score(50000)
            # keep playing for extra shots until the timer expires


class Meltdown(ChainFeature):
    """Meltdown chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':3, 'medium':4, 'hard':5}
        super(Meltdown, self).__init__(game, priority, 'Meltdown', 'Hit captive ball switches', num_shot_options)

    def mode_started(self):
        super(Meltdown, self).mode_started()
        self.game.sound.play_voice('meltdown intro')

    def update_lamps(self):
        self.game.lamps.stopMeltdown.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

    def sw_captiveBall1_active(self, sw):
        self.switch_hit()

    def sw_captiveBall2_active(self, sw):
        self.switch_hit()

    def sw_captiveBall3_active(self, sw):
        self.switch_hit()

    def switch_hit(self):
        if self.num_shots > 0:
            self.game.sound.stop('meltdown ' + str(self.num_shots))
        self.num_shots += 1
        if self.num_shots <= 4:
            self.game.sound.play_voice('meltdown ' + str(self.num_shots))
        self.game.score(10000)
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.sound.play_voice('meltdown all')
            self.game.score(50000)
            self.exit_callback(True)


class Safecracker(ChainFeature):
    """Safecracker chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':2, 'medium':3, 'hard':4}
        super(Safecracker, self).__init__(game, priority, 'Safe Cracker', 'Shoot subway', num_shot_options)

    def bad_guys(self):
        self.delay(name='bad guys', event_type=None, delay=randint(5, 10), handler=self.bad_guys)
        self.game.sound.play_voice('safecracker bad guys')

    def mode_started(self):
        super(Safecracker, self).mode_started()
        self.start_using_drops()
        self.trip_check()
        self.delay(name='bad guys', event_type=None, delay=randint(10, 20), handler=self.bad_guys)

    def mode_stopped(self):
        super(Safecracker, self).mode_stopped()
        self.stop_using_drops()

    def update_lamps(self):
        self.game.lamps.awardSafecracker.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

    def sw_subwayEnter2_active(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.check_for_completion()

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        # newly detected raised letter D
        self.trip_drop_target()

    def trip_drop_target(self):
        # drop letter D and run a delayed handler to verify it stayed down
        self.game.coils.tripDropTarget.pulse()
        self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def trip_check(self):
        if self.game.switches.dropTargetD.is_inactive():
            self.trip_drop_target()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.sound.play_voice('safecracker complete')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('safecracker shot')


class Manhunt(ChainFeature):
    """Manhunt chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':2, 'medium':3, 'hard':4}
        super(Manhunt, self).__init__(game, priority, 'Manhunt', 'Shoot left ramp', num_shot_options)

    def mode_started(self):
        super(Manhunt, self).mode_started()
        self.game.sound.play_voice('manhunt - intro')

    def update_lamps(self):
        self.game.coils.flasherPursuitL.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

    # Award shot if ball diverted for multiball.  Ensure it was a fast
    # shot rather than one that just trickles in.
    def sw_leftRampToLock_active(self, sw):
        if self.game.switches.leftRampEnter.time_since_change() < 0.5:
            self.switch_hit()

    def sw_leftRampExit_active(self, sw):
        self.switch_hit()

    def switch_hit(self):
        self.num_shots += 1
        self.game.score(10000)
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.sound.play_voice('manhunt - done')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('manhunt - shot')


class Stakeout(ChainFeature):
    """Stakeout chain mode"""

    def __init__(self, game, priority):
        num_shot_options = {'easy':3, 'medium':4, 'hard':5}
        super(Stakeout, self).__init__(game, priority, 'Stakeout', 'Shoot right ramp', num_shot_options)

    def mode_started(self):
        super(Stakeout, self).mode_started()
        self.delay(name='boring', event_type=None, delay=15, handler=self.boring_expired)

    def update_lamps(self):
        self.game.coils.flasherPursuitR.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

    def boring_expired(self):
        # keep quiet if stacked with multiball
        if not self.game.getPlayerState('multiball_active'):
            self.game.sound.play_voice('stakeout boring')
        self.delay(name='boring', event_type=None, delay=5, handler=self.boring_expired)

    def sw_rightRampExit_active(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.cancel_delayed('boring')
        self.game.sound.stop('stakeout boring')
        if self.num_shots == 1:
            self.game.sound.play_voice('stakeout over there')
        elif self.num_shots == 2:
            self.game.sound.play_voice('stakeout surrounded')
        elif self.num_shots == 3:
            self.game.sound.play_voice('stakeout move in')
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.game.score(50000)
            self.exit_callback(True)
