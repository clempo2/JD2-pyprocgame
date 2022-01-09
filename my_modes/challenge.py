import locale
from random import shuffle
from procgame.dmd import GroupedLayer, MarkupFrameGenerator, PanningLayer, ScriptedLayer, TextLayer
from procgame.game import SwitchStop
from procgame.modes import Scoring_Mode
from crimescenes import CrimeSceneBase
from intro import Introduction

class ChallengeIntro(Introduction):
    def update_lamps(self):
        self.game.enable_gi(False)
        self.game.disable_drop_lamps()


class UltimateChallenge(Scoring_Mode):
    """Wizard mode or start of supergame"""

    def __init__(self, game, priority):
        super(UltimateChallenge, self).__init__(game, priority)

        self.intro = ChallengeIntro(self.game, self.priority+1)
        self.intro.exit_callback = self.start_level

        self.fear = Fear(game, self.priority+1)
        self.mortis = Mortis(game, self.priority+1)
        self.death = Death(game, self.priority+1)
        self.fire = Fire(game, self.priority+1)
        self.celebration = Celebration(game, self.priority+1)

        self.mode_list = [self.fear, self.mortis, self.death, self.fire, self.celebration]
        for mode in self.mode_list[0:4]:
            mode.exit_callback = self.level_ended

    def mode_started(self):
        self.active_mode = self.game.getPlayerState('challenge_mode', 0)
        self.game.coils.resetDropTarget.pulse(40)
        self.intentional_drain = False

    def mode_stopped(self):
        # when celebration was awarded, the next challenge starts from the beginning
        self.game.setPlayerState('challenge_mode', self.active_mode if self.active_mode < 4 else 0)
        self.game.modes.remove(self.intro) # in case of tilt
        self.game.modes.remove(self.mode_list[self.active_mode])

    def update_lamps(self):
        self.game.lamps.ultChallenge.enable()

    def start_challenge(self):
        # called by base play supergame or regular play
        self.start_intro()

    def end_challenge(self):
        # go back to regular play
        self.game.modes.remove(self)
        self.game.update_lamps()
        self.exit_callback()

    def start_intro(self):
        self.game.sound.stop_music()
        self.intro.setup(self.mode_list[self.active_mode])
        self.game.modes.add(self.intro)
        self.game.update_lamps()
        self.game.enable_flippers(True)

    def start_level(self):
        # intro completed or aborted, start the actual mode
        self.game.modes.add(self.mode_list[self.active_mode])
        self.game.update_lamps()
        self.game.sound.play_music('mode', loops=-1)
        self.mode_list[self.active_mode].launch_balls()

    def level_ended(self, success=True):
        if success:
            # drain intentionally before starting next mode
            self.game.ball_save.disable()
            self.game.sound.fadeout_music()
            self.intentional_drain = True
        else:
            # level failed because the timer expired
            self.end_challenge()

    def next_level(self):
        # all balls have intentionally drained, move to the next mode
        self.game.modes.remove(self.mode_list[self.active_mode])
        self.active_mode += 1 # next mode
        self.start_intro()
        # intro updated the lamps

    def ball_drained(self):
        if self.intentional_drain:
            if self.game.trough.num_balls_in_play == 0:
                self.intentional_drain = False
                self.next_level()
                # ignore this drain, starting the next mode acts like a ball saver
                return True
            # else wait for the other balls to drain
        elif self.game.trough.num_balls_in_play == 1 and self.active_mode == 4: # celebration
            # wizard mode completed successfully, revert to regular play
            self.end_challenge()
        #else let base_play handle it, i.e. mode continues with remaining balls or ends if no balls left

    def sw_shooterL_active_for_200ms(self, sw):
        self.game.coils.shooterL.pulse()
        return SwitchStop

    def sw_popperR_active_for_300ms(self, sw):
        self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)


class ChallengeBase(Scoring_Mode):
    """Base class for all wizard modes"""

    def __init__(self, game, priority, num_balls, ball_save_time):
        super(ChallengeBase, self).__init__(game, priority)
        self.frame_gen = MarkupFrameGenerator()
        self.num_balls = num_balls
        self.ball_save_time = ball_save_time

    def mode_started(self):
        self.started = False
        # account for ball already in right popper if starting ultimate challenge from regular play
        # or account for ball in shooter lane when in supergame and this is the first mode for this ball
        active_balls = 1 if self.game.switches.popperR.is_active() or self.game.switches.shooterR.is_active() else 0
        self.num_launch_balls = self.num_balls - active_balls

    def get_instruction_layer(self):
        instructions = self.instructions()
        instruction_frame = self.frame_gen.frame_for_markup(instructions)
        panning_layer = PanningLayer(width=128, height=32, frame=instruction_frame, origin=(0, 0), translate=(0, 1), bounce=False)
        duration = len(instructions) / 16
        script = [{'seconds':duration, 'layer':panning_layer}]
        return ScriptedLayer(width=128, height=32, script=script)

    def launch_balls(self):
        if self.game.switches.popperR.is_active():
            # we were started from regular mode
            # put the ball back in play and start the timer if applicable
            self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)
            self.start()
        else:
            # serve the ball to the shooter lane, but wait for the player to plunge the ball
            self.game.base_play.auto_plunge = False
            self.game.sound.play_music('ball_launch', loops=-1)

        if self.num_launch_balls > 0:
            self.game.trough.launch_balls(self.num_launch_balls)

    def start(self):
        # the ball is now in play (popped from popperR or plunged by player)
        self.started = True
        self.game.base_play.auto_plunge = True
        if self.ball_save_time > 0:
            self.game.ball_save.start(num_balls_to_save=self.num_balls, time=self.ball_save_time, now=False, allow_multiple_saves=True)

    def sw_shooterR_inactive_for_1s(self, sw):
        if not self.started:
            self.start()

    def sw_leftRampToLock_active(self, sw):
        self.game.deadworld.eject_balls(1)


class DarkJudge(ChallengeBase):
    """Base class for dark judge wizard modes"""

    def __init__(self, game, priority, num_balls, ball_save_time, timer, taunt_sound):
        super(DarkJudge, self).__init__(game, priority, num_balls, ball_save_time)
        self.timer = timer
        self.taunt_sound = taunt_sound
        if self.timer > 0:
            self.countdown_layer = TextLayer(127, 1, self.game.fonts['tiny7'], 'right')

    def mode_stopped(self):
        self.cancel_delayed(['countdown', 'taunt'])

    def start(self):
        super(DarkJudge, self).start()
        if self.timer > 0:
            self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)
        self.delay(name='taunt', event_type=None, delay=5, handler=self.taunt)

    def decrement_timer(self):
        if self.timer == 0:
            self.finish(success=False)
        else:
            self.timer -= 1
            self.countdown_layer.set_text(str(self.timer))
            self.delay(name='countdown', event_type=None, delay=1, handler=self.decrement_timer)

    def taunt(self):
        self.game.sound.play_voice(self.taunt_sound)
        self.delay(name='taunt', event_type=None, delay=10, handler=self.taunt)

    def sw_dropTargetJ_active_for_250ms(self, sw):
        self.reset_drops()

    def sw_dropTargetU_active_for_250ms(self, sw):
        self.reset_drops()

    def sw_dropTargetD_active_for_250ms(self, sw):
        self.reset_drops()

    def sw_dropTargetG_active_for_250ms(self, sw):
        self.reset_drops()

    def sw_dropTargetE_active_for_250ms(self, sw):
        self.reset_drops()

    def reset_drops(self):
        self.game.coils.resetDropTarget.pulse(40)

    def show_score(self):
        if self.score_layer:
            score = self.game.current_player().score
            text = '00' if score == 0 else locale.format('%d', score, True)
            self.score_layer.set_text(text)

    def finish(self, success):
        self.cancel_delayed(['taunt', 'countdown'])
        self.game.enable_flippers(False)
        self.game.update_lamps()
        text = self.__class__.__name__ + ' Defeated' if success else 'You lose!'
        self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], 'center', True).set_text(text)
        self.exit_callback(success)


class Fear(DarkJudge):
    """Fear wizard mode"""

    def instructions(self):
        return """

#ULTIMATE#
#CHALLENGE#

Defeat the Dark Judges

Stage 1

Judge Fear is reigning terror on the city.

Banish him by shooting the lit ramp shots and then the subway before time runs out.

1 ball with temporary ball save.
"""

    def __init__(self, game, priority):
        super(Fear, self).__init__(game, priority, num_balls=1, ball_save_time=10, timer=20, taunt_sound='fear - taunt')
        self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], 'left').set_text('Fear')
        self.score_layer = TextLayer(128/2, 10, self.game.fonts['num_14x10'], 'center')
        self.status_layer = TextLayer(128/2, 26, self.game.fonts['tiny7'], 'center')
        self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

    def mode_started(self):
        super(Fear, self).mode_started()
        self.already_collected = False
        self.mystery_lit = True
        self.state = 'ramps'
        self.active_ramp = 'left'
        self.ramp_shots_required = 4
        self.ramp_shots_hit = 0

    def update_lamps(self):
        schedule = 0x80808080 if self.state != 'finished' else 0
        self.game.coils.flasherFear.schedule(schedule=schedule, cycle_seconds=0, now=True)

        style = 'on' if self.mystery_lit else 'off'
        self.game.drive_lamp('mystery', style)

        schedule = 0x00030003 if self.state == 'ramps' and self.active_ramp == 'left' else 0
        self.game.coils.flasherPursuitL.schedule(schedule=schedule, cycle_seconds=0, now=True)

        schedule = 0x00030003 if self.state == 'ramps' and self.active_ramp == 'right' else 0
        self.game.coils.flasherPursuitR.schedule(schedule=schedule, cycle_seconds=0, now=True)

        style = 'medium' if self.state == 'subway' and self.game.switches.dropTargetD.is_inactive() else 'off'
        self.game.drive_lamp('dropTargetD', style)

        style = 'medium' if self.state == 'subway' else 'off'
        for lamp in ['pickAPrize', 'awardSafecracker', 'awardBadImpersonator', 'multiballJackpot']:
            self.game.drive_lamp(lamp, style)

    def sw_mystery_active(self, sw):
        self.game.sound.play('mystery')
        if self.mystery_lit:
            self.mystery_lit = False
            self.timer = 20
            self.game.update_lamps()

    def sw_leftRampExit_active(self, sw):
        if self.state == 'ramps' and self.active_ramp == 'left':
            self.ramp_shot_hit()

    def sw_rightRampExit_active(self, sw):
        if self.state == 'ramps' and self.active_ramp == 'right':
            self.ramp_shot_hit()

    def ramp_shot_hit(self):
        self.ramp_shots_required -= 1
        if self.ramp_shots_required:
            self.switch_ramps()
        else:
            self.state = 'subway'
        self.timer = 20
        self.game.update_lamps()

    def switch_ramps(self):
        self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
        self.game.score(10000)
        self.active_ramp = 'right' if self.active_ramp == 'left' else 'right'

    def sw_dropTargetD_inactive_for_400ms(self, sw):
        if self.state == 'subway':
            self.game.coils.tripDropTarget.pulse(60)

    def sw_dropTargetD_active_for_250ms(self, sw):
        if self.state == 'ramps':
            self.reset_drops()
        else:
            self.game.update_lamps()

    def reset_drops(self):
        if self.state != 'subway':
            self.game.coils.resetDropTarget.pulse(40)

    def sw_subwayEnter1_closed(self, sw):
        self.subway_hit()

    # Ball might jump over first switch.  Use 2nd switch as a catch all.
    def sw_subwayEnter2_closed(self, sw):
        self.subway_hit()

    def subway_hit(self):
        if self.state == 'subway' and not self.already_collected:
            self.already_collected = True
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.finish(success=True)

    def mode_tick(self):
        self.show_score()

    def finish(self, success):
        self.state = 'finished'
        super(Fear, self).finish(success)


class Mortis(DarkJudge):
    """Mortis wizard mode"""

    def instructions(self):
        return """

#ULTIMATE#
#CHALLENGE#

Stage 2

Judge Mortis is spreading disease throughout the city.

Banish him by shooting each lit shot twice.

2 ball multiball with temporary ball save.
"""
    def __init__(self, game, priority):
        super(Mortis, self).__init__(game, priority, num_balls=2, ball_save_time=10, timer=0, taunt_sound='mortis - taunt')
        self.lamp_names = ['mystery', 'perp1G', 'perp3G', 'perp5G', 'stopMeltdown']
        self.lamp_styles = ['off', 'fast', 'medium']

    def mode_started(self):
        super(Mortis, self).mode_started()
        self.state = 'ramps'
        self.shots_required = [2, 2, 2, 2, 2]
        self.already_collected = False
        self.delay(name='taunt', event_type=None, delay=5, handler=self.taunt)

    def update_lamps(self):
        schedule = 0x80808080 if any(self.shots_required) else 0
        self.game.coils.flasherMortis.schedule(schedule=schedule, cycle_seconds=0, now=True)
        for shot in range(0, 5):
            lamp_name = self.lamp_names[shot]
            req_shots = self.shots_required[shot]
            style = self.lamp_styles[req_shots]
            self.game.drive_lamp(lamp_name, style)

    def sw_mystery_active(self, sw):
        self.switch_hit(0)

    def sw_topRightOpto_active(self, sw):
        if self.game.switches.leftRollover.time_since_change() < 1:
            # ball came around outer left loop
            self.switch_hit(1)

    def sw_popperR_active_for_300ms(self, sw):
        self.switch_hit(2)

    def sw_rightRampExit_active(self, sw):
        self.switch_hit(3)

    def sw_captiveBall3_active(self, sw):
        self.switch_hit(4)

    def switch_hit(self, index):
        if self.shots_required[index] > 0:
            self.shots_required[index] -= 1
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.check_for_completion()

    def check_for_completion(self):
        if not any(self.shots_required):
            self.finish(success=True)


class Death(DarkJudge, CrimeSceneBase):
    """Death wizard mode"""

    def instructions(self):
        return """

#ULTIMATE#
#CHALLENGE#

Stage 3

Judge Death is on a murder spree.

Banish him by shooting the lit crime scene shots before time expires.  Shots slowly re-light so finish him quickly.

1 ball with temporary ball save.
"""

    def __init__(self, game, priority):
        super(Death, self).__init__(game, priority, num_balls=1, ball_save_time=20, timer=180, taunt_sound='death - taunt')
        self.shot_order = [4, 2, 0, 3, 1] # from easiest to hardest
        self.name_layer = TextLayer(1, 1, self.game.fonts['tiny7'], 'left').set_text('Death')
        self.score_layer = TextLayer(128/2, 10, self.game.fonts['num_14x10'], 'center')
        self.status_layer = TextLayer(128/2, 26, self.game.fonts['tiny7'], 'center')
        self.layer = GroupedLayer(128, 32, [self.countdown_layer, self.name_layer, self.score_layer, self.status_layer])

    def mode_started(self):
        super(Death, self).mode_started()
        self.already_collected = False
        self.current_shot_index = 0
        self.shot_timer = 10
        self.active_shots = [1, 1, 1, 1, 1]
        self.game.coils.resetDropTarget.pulse(40)

    def update_lamps(self):
        schedule = 0x80808080 if any(self.active_shots) else 0
        self.game.coils.flasherDeath.schedule(schedule=schedule, cycle_seconds=0, now=True)

        for shot in range(0, 5):
            style = 'off' if self.active_shots[shot] == 0 else 'medium'
            self.game.drive_lamp('perp' + str(shot + 1) + 'W', style)

    def switch_hit(self, index):
        if self.active_shots[index]:
            self.active_shots[index] = 0
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.shot_timer += 10
            self.check_for_completion()
            self.game.update_lamps()

    def add_shot(self):
        for shot in self.shot_order:
            if not self.active_shots[shot]:
                self.active_shots[shot] = 1
                break
        self.game.update_lamps()

    def mode_tick(self):
        self.show_score()

    def decrement_timer(self):
        super(Death, self).decrement_timer()
        if self.shot_timer > 0:
            self.shot_timer -= 1
        else:
            self.shot_timer = 10
            self.add_shot()

    def check_for_completion(self):
        if not any(self.active_shots):
            self.finish(success=True)

    def finish(self, success):
        self.active_shots = [0, 0, 0, 0, 0]
        super(Death, self).finish(success)


class Fire(DarkJudge, CrimeSceneBase):
    """Fire wizard mode"""

    def instructions(self):
        return """

#ULTIMATE#
#CHALLENGE#

Stage 4

Judge Fire is creating chaos by lighting fires all over Mega City One.

Extinguish fires and banish Judge Fire by shooting the lit crime scene shots.

4 ball multiball.  No ball save.
"""

    def __init__(self, game, priority):
        super(Fire, self).__init__(game, priority, num_balls=4, ball_save_time=0, timer=0, taunt_sound='fire - taunt')

    def mode_started(self):
        super(Fire, self).mode_started()
        self.mystery_lit = True
        self.targets = [1, 1, 1, 1, 1]

    def update_lamps(self):
        schedule = 0x80808080 if any(self.targets) else 0
        self.game.coils.flasherFire.schedule(schedule=schedule, cycle_seconds=0, now=True)

        for shot in range(0, 5):
            lampname = 'perp' + str(shot+1) + 'R'
            style = 'medium' if self.targets[shot] else 'off'
            self.game.drive_lamp(lampname, style)

        style = 'on' if self.mystery_lit else 'off'
        self.game.drive_lamp('mystery', style)

    def sw_mystery_active(self, sw):
        self.game.sound.play('mystery')
        if self.mystery_lit:
            self.mystery_lit = False
            self.game.set_status('Add 2 balls!')
            self.game.trough.launch_balls(2)
            self.game.update_lamps()

    def switch_hit(self, num):
        if self.targets[num]:
            self.targets[num] = 0
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.check_for_completion()

    def check_for_completion(self):
        if not any(self.targets):
            self.finish(success=True)

    def finish(self, success):
        self.mystery_lit = False
        super(Fire, self).finish(success)


class Celebration(ChallengeBase):
    """Final multiball wizard mode after all dark judges have been defeated"""

    def instructions(self):
        return """

#CONGRATS#

The Dark Judges have all been banished.

Enjoy a 6-ball celebration multiball.  All shots score.

Normal play resumes when only 1 ball remains.
"""

    def __init__(self, game, priority):
        super(Celebration, self).__init__(game, priority, num_balls=6, ball_save_time=20)

    def mode_started(self):
        super(Celebration, self).mode_started()
        # This player reached the end of supergame, his next ball is regular play
        # do this early now in case the game tilts
        self.game.setPlayerState('supergame', False)

    def update_lamps(self):
        self.game.enable_gi(True)

        # rotate 0xFFFF0000 pattern to all 32 bit positions
        lamp_schedules = [(0xFFFF0000 >> d)|(0xFFFF0000 << (32 - d)) & 0xFFFFFFFF for d in range (0, 32)]
        shuffle(lamp_schedules)

        i = 0
        for lamp in self.game.lamps:
            if lamp.name not in ['gi01', 'gi02', 'gi03', 'gi04', 'gi05', 'startButton', 'buyIn', 'drainShield', 'superGame', 'judgeAgain']:
                lamp.schedule(schedule=lamp_schedules[i%32], cycle_seconds=0, now=False)
                i += 1

    def sw_mystery_active(self, sw):
        self.game.score(5000)

    def sw_topRightOpto_active(self, sw):
        if self.game.switches.leftRollover.time_since_change() < 1:
            # ball came around outer left loop
            self.game.score(5000)
        elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
            # ball came around inner left loop
            self.game.score(5000)

    def sw_popperR_active_for_300ms(self, sw):
        self.game.score(1000)

    def sw_leftRollover_active(self, sw):
        if self.game.switches.topRightOpto.time_since_change() < 1.5:
            # ball came around right loop
            self.game.score(5000)

    def sw_rightRampExit_active(self, sw):
        self.game.score(1000)
