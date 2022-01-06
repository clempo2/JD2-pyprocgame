from random import randint
import locale
from procgame.dmd import GroupedLayer, ScriptedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Scoring_Mode
from intro import Introduction

class ChainIntro(Introduction):
    def update_lamps(self):
        self.game.enable_gi(False)

class Chain(Mode):
    """Controls the progress through the chain modes"""

    def __init__(self, game, priority):
        super(Chain, self).__init__(game, priority)

        # for status report in SuperGame before Chain is started
        self.num_modes_attempted = 0
        self.num_modes_completed = 0

        self.intro = ChainIntro(self.game, self.priority+1)
        self.intro.exit_callback = self.activate_chain_mode

        pursuit = Pursuit(game, priority+1)
        blackout = Blackout(game, priority+1)
        sniper = Sniper(game, priority+1)
        battle_tank = BattleTank(game, priority+1)
        impersonator = Impersonator(game, priority+1)
        meltdown = Meltdown(game, priority+1)
        safecracker = Safecracker(game, priority+1)
        manhunt = ManhuntMillions(game, priority+1)
        stakeout = Stakeout(game, priority+1)

        self.all_chain_modes = [pursuit, blackout, sniper, battle_tank, impersonator, meltdown, safecracker, manhunt, stakeout]
        for mode in self.all_chain_modes:
            mode.exit_callback = self.chain_mode_over

        self.hurry_up = ChainHurryUp(game, priority+1)
        self.hurry_up.collected_callback = self.hurry_up_collected
        self.hurry_up.expired_callback = self.hurry_up_over

    def mode_started(self):
        # restore player state
        player = self.game.current_player()
        self.modes_not_attempted = player.getState('modes_not_attempted', self.all_chain_modes[:])
        self.modes_not_attempted_ptr = player.getState('modes_not_attempted_ptr', 0)
        self.modes_attempted = player.getState('modes_attempted', [])
        self.modes_completed = player.getState('modes_completed', [])
        self.num_modes_attempted = player.getState('num_modes_attempted', 0)
        self.num_modes_completed = player.getState('num_modes_completed', 0)

        self.mode = None

    def mode_stopped(self):
        # save player state
        player = self.game.current_player()
        player.setState('modes_not_attempted', self.modes_not_attempted)
        player.setState('modes_not_attempted_ptr', self.modes_not_attempted_ptr)
        player.setState('modes_attempted', self.modes_attempted)
        player.setState('modes_completed', self.modes_completed)
        player.setState('num_modes_completed', self.num_modes_completed)
        player.setState('num_modes_attempted', self.num_modes_attempted)

        if self.mode != None:
            self.game.modes.remove(self.mode)

    def reset(self):
        player = self.game.current_player()
        player.setState('modes_not_attempted', self.all_chain_modes[:])
        player.setState('modes_not_attempted_ptr', 0)
        player.setState('modes_attempted', [])
        player.setState('modes_completed', [])
        # num_modes_completed and num_modes_attempted continue to accrue

    def is_active(self):
        return self.mode != None

    def is_complete(self):
        return len(self.modes_not_attempted) == 0

    def get_status_layers(self):
        tiny_font = self.game.fonts['tiny7']
        attempted_layer = TextLayer(128/2, 9, tiny_font, 'center').set_text('Modes attempted: ' + str(self.num_modes_attempted))
        completed_layer = TextLayer(128/2, 19, tiny_font, 'center').set_text('Modes completed: ' + str(self.num_modes_completed))
        status_layer = GroupedLayer(128, 32, [attempted_layer, completed_layer])
        return [status_layer]

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
        length = len(self.modes_not_attempted)
        if length > 0:
            self.modes_not_attempted_ptr = (self.modes_not_attempted_ptr + step + length) % length
        self.game.update_lamps()

    def pause(self):
        if self.mode:
            self.mode.pause()

    def resume(self):
        if self.mode:
            self.mode.resume()

    # start a chain mode by showing the instructions
    def start_chain_mode(self):
        self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
        self.intro.setup(self.mode)
        self.game.modes.add(self.intro)
        self.game.update_lamps()

    # activate a chain mode after showing the instructions
    def activate_chain_mode(self):
        # Update the mode lists.
        self.modes_not_attempted.remove(self.mode)
        self.modes_attempted.append(self.mode)
        self.num_modes_attempted += 1
        self.rotate_modes(0)

        # Add the mode to the mode Q to activate it.
        self.game.base_play.regular_play.state = 'mode'
        self.game.modes.add(self.mode)
        self.game.update_lamps()
        self.mode.play_music()

        # Put the ball back into play
        self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)

    # called when the mode has completed or expired but before the hurry up
    def chain_mode_over(self, completed):
        self.game.modes.remove(self.mode)

        if completed:
            # mode was completed successfully, start hurry up award
            self.modes_completed.append(self.mode)
            self.num_modes_completed += 1
            self.game.setPlayerState('num_modes_completed', self.num_modes_completed)
            self.game.modes.add(self.hurry_up)
            self.game.update_lamps()
        else:
            # mode not successful, skip the hurry up
            self.hurry_up_over()

    # called when a successful mode hurry up was achieved
    def hurry_up_collected(self):
        # award a crime scene level and/or some points
        if self.game.getPlayerState('crimescenes_complete', False):
            self.game.score(10000)
        else:
            self.game.base_play.regular_play.crime_scenes.crime_scene_levels.level_complete()

        if self.game.base_play.regular_play.any_multiball_active():
            self.game.score(100000)
        self.hurry_up_over()

    # called when the mode is over including the hurry up
    def hurry_up_over(self):
        self.mode = None
        self.game.modes.remove(self.hurry_up)
        self.game.base_play.regular_play.chain_mode_completed()
        self.game.update_lamps()

    def update_lamps(self):
        self.game.enable_gi(True)

        if len(self.modes_not_attempted) > 0:
            blinking_mode = self.mode if self.mode else self.modes_not_attempted[self.modes_not_attempted_ptr]
            for mode in self.modes_not_attempted:
                style = 'slow' if mode is blinking_mode else 'off'
                self.game.drive_lamp(mode.lamp_name, style)
        for mode in self.modes_attempted:
            self.game.drive_lamp(mode.lamp_name, 'on')


class ChainHurryUp(Mode):
    """Hurry up to subway after a chain mode is successfully completed"""

    def __init__(self, game, priority):
        super(ChainHurryUp, self).__init__(game, priority)
        self.countdown_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.banner_layer])

    def mode_started(self):
        self.banner_layer.set_text('HURRY-UP!', 3)
        self.seconds_remaining = 13
        self.update_and_delay()
        self.game.coils.tripDropTarget.pulse(40)
        self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)
        self.already_collected = False

    def mode_stopped(self):
        self.cancel_delayed(['grace', 'countdown', 'trip_check'])

    def trip_check(self):
        if self.game.switches.dropTargetD.is_inactive():
            self.game.coils.tripDropTarget.pulse(40)
            self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        self.game.coils.tripDropTarget.pulse(40)
        self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def update_lamps(self):
        self.game.lamps.pickAPrize.schedule(schedule=0x33333333, cycle_seconds=0, now=True)

    def sw_subwayEnter1_closed(self, sw):
        self.collect_hurry_up()

    # Ball might jump over first switch.  Use 2nd switch as a catch all.
    def sw_subwayEnter2_closed(self, sw):
        if not self.already_collected:
            self.collect_hurry_up()

    def collect_hurry_up(self):
        self.game.sound.play_voice('collected')
        self.cancel_delayed(['grace', 'countdown', 'trip_check'])
        self.already_collected = True
        self.banner_layer.set_text('Well Done!')
        self.layer = GroupedLayer(128, 32, [self.banner_layer])
        self.collected_callback()

    def update_and_delay(self):
        self.countdown_layer.set_text('%d seconds' % (self.seconds_remaining))
        self.delay(name='countdown', event_type=None, delay=1, handler=self.one_less_second)

    def one_less_second(self):
        self.seconds_remaining -= 1
        if self.seconds_remaining > 0:
            self.update_and_delay()
        else:
            self.countdown_layer.set_text('')
            self.delay(name='grace', event_type=None, delay=1, handler=self.delayed_removal)

    def delayed_removal(self):
        self.expired_callback()


class ModeTimer(Mode):
    """timer for a timed mode"""

    def __init__(self, game, priority):
        super(ModeTimer, self).__init__(game, priority)
        self.timer = 0

    def mode_stopped(self):
        self.stop_timer()

    def start_timer(self, time):
        # Tell the mode how much time it gets, if it cares.
        self.timer_update(time)
        self.timer = time
        self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)

    def stop_timer(self):
        self.timer = 0
        self.cancel_delayed('decrement timer')

    def add_time(self, time):
        self.timer += time

    def pause(self):
        self.cancel_delayed('decrement timer')

    def resume(self):
        if self.timer > 0:
            self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)

    def decrement_timer(self):
        if self.timer > 0:
            self.timer -= 1
            self.delay(name='decrement timer', event_type=None, delay=1, handler=self.decrement_timer)
            self.timer_update(self.timer)
        else:
            self.expired()

    def expired(self):
        pass

    def timer_update(self, time):
        pass


class ChainFeature(Scoring_Mode, ModeTimer):
    """Base class for the chain modes"""

    def __init__(self, game, priority, name, lamp_name):
        super(ChainFeature, self).__init__(game, priority)
        self.name = name
        self.lamp_name = lamp_name
        self.mode_time = self.game.user_settings['Gameplay']['Time per chain feature']

        self.countdown_layer = TextLayer(127, 1, self.game.fonts['tiny7'], 'right')
        self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], 'left').set_text(name)
        self.score_layer = TextLayer(128/2, 10, self.game.fonts['num_14x10'], 'center')
        self.status_layer = TextLayer(128/2, 26, self.game.fonts['tiny7'], 'center')
        self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

    def mode_started(self):
        self.num_shots = 0
        self.start_timer(self.mode_time)
        self.play_music()
        self.update_status()

    def set_shots_required(self, options):
        """Return the number of required shots depending on the settings and the options for the mode"""
        difficulty = self.game.user_settings['Gameplay']['Chain feature difficulty']
        if not difficulty in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        self.shots_required = options[difficulty]

    def play_music(self):
        self.game.sound.stop_music()
        self.game.sound.play_music('mode', loops=-1)

    def get_instruction_layer(self):
        font = self.game.fonts['jazz18']
        font_small = self.game.fonts['tiny7']
        layer_name = TextLayer(128/2, 7, font, 'center').set_text(self.name)
        layer_instructions = TextLayer(128/2, 24, font_small, 'center').set_text(self.instructions)
        layer_grouped = GroupedLayer(128, 32, [layer_name, layer_instructions])
        script = [{'seconds':2, 'layer':layer_name}, {'seconds':2, 'layer':layer_grouped}]
        return ScriptedLayer(width=128, height=32, script=script)

    def update_status(self):
        if self.num_shots > self.shots_required:
            # only Impersonator can get extra hits
            extra_shots = self.num_shots - self.shots_required
            status = 'Shots made: ' + str(extra_shots) + ' extra'
        else:
            status = 'Shots made: ' + str(self.num_shots) + '/' + str(self.shots_required)
        self.status_layer.set_text(status)

    def mode_tick(self):
        score = self.game.current_player().score
        text = '00' if score == 0 else locale.format('%d', score, True)
        self.score_layer.set_text(text)

    def timer_update(self, time):
        self.countdown_layer.set_text(str(time))

    def is_complete(self):
        return self.num_shots >= self.shots_required

    def expired(self):
        self.exit_callback(self.is_complete())

    def start_using_drops(self):
        self.game.base_play.regular_play.multiball.drops.paused = True
        self.reset_drops()

    def stop_using_drops(self):
        self.game.base_play.regular_play.multiball.drops.paused = False
        self.reset_drops()

    def reset_drops(self):
        self.game.base_play.regular_play.multiball.drops.animated_reset(.1)
        self.game.base_play.regular_play.multiball.reset_active_drops()


class Pursuit(ChainFeature):
    """Pursuit chain mode"""

    def __init__(self, game, priority):
        super(Pursuit, self).__init__(game, priority, 'Pursuit', 'pursuit')
        self.set_shots_required({'easy':3, 'medium':4, 'hard':5})
        self.instructions = 'Shoot ' + str(self.shots_required) + ' L/R ramp shots'

    def mode_started(self):
        super(Pursuit, self).mode_started()
        time = self.game.sound.play_voice('pursuit intro')
        self.delay(name='response', event_type=None, delay=time+0.5, handler=self.response)

    def response(self):
        self.game.sound.play_voice('in pursuit')

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
        if self.num_shots == self.shots_required:
            self.game.sound.play_voice('complete')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('good shot')

    def expired(self):
        self.game.sound.play_voice('failed')
        super(Pursuit, self).expired()


class Blackout(ChainFeature):
    """Blackout chain mode"""

    def __init__(self, game, priority):
        super(Blackout, self).__init__(game, priority, 'Blackout', 'blackout')
        self.set_shots_required({'easy':2, 'medium':2, 'hard':3})
        self.instructions = 'Shoot center ramp'

    def mode_started(self):
        super(Blackout, self).mode_started()
        self.game.base_play.play_animation('blackout', frame_time=3)

    def update_lamps(self):
        self.game.enable_gi(False) # disable all gi except gi05
        self.game.lamps.gi05.enable()
        self.game.lamps.blackoutJackpot.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
        if self.num_shots == self.shots_required - 1:
            self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

    def sw_centerRampExit_active(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.shots_required - 1:
            self.game.score(50000)
            self.game.update_lamps()
        elif self.num_shots == self.shots_required:
            self.game.score(110000)
            self.exit_callback(True)


class Sniper(ChainFeature):
    """Sniper chain mode"""

    def __init__(self, game, priority):
        super(Sniper, self).__init__(game, priority, 'Sniper', 'sniper')
        self.set_shots_required({'easy':2, 'medium':2, 'hard':3})
        self.instructions = 'Shoot Sniper Tower 2 times'

        # Sniper has extra animation on left and text right justified
        self.score_layer = TextLayer(127, 10, self.game.fonts['num_14x10'], 'right')
        self.status_layer = TextLayer(127, 26, self.game.fonts['tiny7'], 'right')
        self.anim_layer = self.game.animations['scope']
        self.layer = GroupedLayer(128, 32, [self.anim_layer, self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

    def mode_started(self):
        super(Sniper, self).mode_started()
        time = randint(2, 7)
        self.delay(name='gunshot', event_type=None, delay=time, handler=self.gunshot)

    def mode_stopped(self):
        self.cancel_delayed('gunshot')

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
        if self.num_shots == self.shots_required:
            self.game.sound.play_voice('sniper - hit')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('sniper - miss')


class BattleTank(ChainFeature):
    """Battle tank chain mode"""

    def __init__(self, game, priority):
        super(BattleTank, self).__init__(game, priority, 'Battle Tank', 'battleTank')
        self.instructions = 'Shoot all 3 battle tank shots'
        self.shots_required = 3
        self.lamp_names = ['tankLeft', 'tankCenter', 'tankRight']

    def mode_started(self):
        self.shots = [1, 1, 1]
        super(BattleTank, self).mode_started()
        self.game.sound.play_voice('tank intro')

    def update_lamps(self):
        for shot in range(0, 3):
            style = 'slow' if self.shots[shot] else 'off'
            self.game.drive_lamp(self.lamp_names[shot], style)

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
        if self.num_shots == self.shots_required:
            self.game.score(50000)
            self.exit_callback(True)


class Meltdown(ChainFeature):
    """Meltdown chain mode"""

    def __init__(self, game, priority):
        super(Meltdown, self).__init__(game, priority, 'Meltdown', 'meltdown')
        self.set_shots_required({'easy':3, 'medium':4, 'hard':5})
        self.instructions = 'Hit ' + str(self.shots_required) + ' captive ball switches'

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
        if self.num_shots == self.shots_required:
            self.game.sound.play_voice('meltdown all')
            self.game.score(50000)
            self.exit_callback(True)


class Impersonator(ChainFeature):
    """Bad impersonator chain mode"""

    def __init__(self, game, priority):
        super(Impersonator, self).__init__(game, priority, 'Impersonator', 'impersonator')
        self.set_shots_required({'easy':3, 'medium':5, 'hard':7})
        self.instructions = 'Shoot ' + str(self.shots_required) + ' lit drop targets'

    def mode_started(self):
        super(Impersonator, self).mode_started()
        self.sound_active = False
        self.start_using_drops()
        time = self.game.sound.play('bad impersonator')
        self.delay(name='song_restart', event_type=None, delay=time+0.5, handler=self.song_restart)
        self.delay(name='boo_restart', event_type=None, delay=time+4, handler=self.boo_restart)
        self.delay(name='shutup_restart', event_type=None, delay=time+3, handler=self.shutup_restart)

    def mode_stopped(self):
        self.stop_using_drops()
        self.cancel_delayed(['song_restart', 'boo_restart', 'shutup_restart', 'end_sound'])
        self.game.sound.stop('bi - song')
        self.game.sound.stop('bi - boo')

    def play_music(self):
        pass

    def song_restart(self):
        self.game.sound.play('bi - song')
        self.delay(name='song_restart', event_type=None, delay=6, handler=self.song_restart)

    def boo_restart(self):
        time = randint(2, 7)
        self.game.sound.play('bi - boo')
        self.delay(name='boo_restart', event_type=None, delay=time, handler=self.boo_restart)

    def shutup_restart(self):
        time = randint(2, 7)
        self.game.sound.play('bi - shutup')
        self.delay(name='shutup_restart', event_type=None, delay=time, handler=self.shutup_restart)

    def end_sound(self):
        self.sound_active = False

    def update_lamps(self):
        self.game.lamps.awardBadImpersonator.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
        self.game.disable_drop_lamps()
        # ModeTimer is continuously updating self.timer
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
        self.game.sound.stop('bi - song')
        if not self.sound_active:
            self.sound_active = True
            self.game.sound.play('bi - ouch')
            self.delay(name='end_sound', event_type=None, delay=1, handler=self.end_sound)
        self.game.coils.resetDropTarget.pulse(40)
        self.check_for_completion()

    def timer_update(self, time):
        super(Impersonator, self).timer_update(time)
        self.game.update_lamps()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.shots_required:
            self.game.score(50000)
            # keep playing for extra shots until the timer expires


class Safecracker(ChainFeature):
    """Safecracker chain mode"""

    def __init__(self, game, priority):
        super(Safecracker, self).__init__(game, priority, 'Safe Cracker', 'safecracker')
        self.set_shots_required({'easy':2, 'medium':3, 'hard':4})
        self.instructions = 'Shoot the subway ' + str(self.shots_required) + ' times'

    def bad_guys(self):
        self.delay(name='bad guys', event_type=None, delay=randint(5, 10), handler=self.bad_guys)
        self.game.sound.play_voice('bad guys')

    def mode_started(self):
        super(Safecracker, self).mode_started()
        self.start_using_drops()
        self.delay(name='trip_check', event_type=None, delay=1, handler=self.trip_check)
        self.delay(name='bad guys', event_type=None, delay=randint(10, 20), handler=self.bad_guys)

    def mode_stopped(self):
        self.cancel_delayed(['trip_check', 'bad guys'])
        self.stop_using_drops()

    def update_lamps(self):
        self.game.lamps.awardSafecracker.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)

    def sw_subwayEnter2_active(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.check_for_completion()

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        self.game.coils.tripDropTarget.pulse(30)

    def trip_check(self):
        if self.game.switches.dropTargetD.is_inactive():
            self.game.coils.tripDropTarget.pulse(40)
            self.delay(name='trip_check', event_type=None, delay=.400, handler=self.trip_check)

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.shots_required:
            self.game.sound.play_voice('complete')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('shot')


class ManhuntMillions(ChainFeature):
    """ManhuntMillions chain mode"""

    def __init__(self, game, priority):
        super(ManhuntMillions, self).__init__(game, priority, 'Manhunt', 'manhunt')
        self.set_shots_required({'easy':2, 'medium':3, 'hard':4})
        self.instructions = 'Shoot the left ramp ' + str(self.shots_required) + ' times'

    def mode_started(self):
        super(ManhuntMillions, self).mode_started()
        self.game.sound.play_voice('mm - intro')

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
        if self.num_shots == self.shots_required:
            self.game.sound.play_voice('mm - done')
            self.game.score(50000)
            self.exit_callback(True)
        else:
            self.game.sound.play_voice('mm - shot')


class Stakeout(ChainFeature):
    """Stakeout chain mode"""

    def __init__(self, game, priority):
        super(Stakeout, self).__init__(game, priority, 'Stakeout', 'stakeout')
        self.set_shots_required({'easy':3, 'medium':4, 'hard':5})
        self.instructions = 'Shoot the right ramp ' + str(self.shots_required) + ' times'

    def mode_started(self):
        super(Stakeout, self).mode_started()
        self.delay(name='boring', event_type=None, delay=15, handler=self.boring_expired)

    def mode_stopped(self):
        self.cancel_delayed('boring')

    def update_lamps(self):
        self.game.coils.flasherPursuitR.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

    def boring_expired(self):
        self.game.sound.play_voice('so - boring')
        self.delay(name='boring', event_type=None, delay=5, handler=self.boring_expired)

    def sw_rightRampExit_active(self, sw):
        self.num_shots += 1
        self.game.score(10000)
        self.cancel_delayed('boring')
        self.game.sound.stop('so - boring')
        if self.num_shots == 1:
            self.game.sound.play_voice('so - over there')
        elif self.num_shots == 2:
            self.game.sound.play_voice('so - surrounded')
        elif self.num_shots == 3:
            self.game.sound.play_voice('so - move in')
        self.check_for_completion()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.shots_required:
            self.game.score(50000)
            self.exit_callback(True)
