from random import shuffle
from procgame.dmd import TextLayer
from procgame.game import Mode
from crimescenes import CrimeSceneShots
from timer import TimedMode

class UltimateChallenge(Mode):
    """Wizard mode or start of supergame"""

    def __init__(self, game, priority):
        super(UltimateChallenge, self).__init__(game, priority)

        self.fear = Fear(game, self.priority + 1)
        self.mortis = Mortis(game, self.priority + 1)
        self.death = Death(game, self.priority + 1)
        self.fire = Fire(game, self.priority + 1)
        self.celebration = Celebration(game, self.priority + 1)

        self.mode_list = [self.fear, self.mortis, self.death, self.fire, self.celebration]
        for mode in self.mode_list:
            mode.exit_callback = self.level_ended

    def mode_started(self):
        self.active_mode = self.game.getPlayerState('challenge_mode', 0)
        self.game.coils.resetDropTarget.pulse(30)
        self.intentional_drain = False
        self.start_level()

    def mode_stopped(self):
        # when celebration was awarded, the next challenge starts from the beginning
        self.game.setPlayerState('challenge_mode', self.active_mode if self.active_mode < 4 else 0)
        self.game.remove_modes([self.mode_list[self.active_mode]])

    def start_level(self):
        self.game.enable_flippers(True)
        if self.game.trough.num_balls_in_play == 0:
            # serve one ball in the shooter lane and wait for player to plunge
            self.game.base_play.auto_plunge = False
            self.game.launch_balls(1)
        self.game.modes.add(self.mode_list[self.active_mode])
        self.game.update_lamps()
        self.game.sound.play_music('mode', loops=-1)
        self.mode_list[self.active_mode].ready()

    def level_ended(self, success=True):
        self.game.ball_save.disable()
        if success:
            # drain intentionally before starting next mode
            self.game.sound.fadeout_music()
            self.intentional_drain = True
            self.game.base_play.boring.pause()
        else:
            # level failed because the timer expired
            self.end_challenge()

    def evt_ball_drained(self):
        if self.intentional_drain:
            if self.game.trough.num_balls_in_play == 0:
                self.intentional_drain = False
                self.next_level()
                # abort the event to ignore this drain
                return True

    def next_level(self):
        # all balls have intentionally drained, move to the next mode
        self.game.remove_modes([self.mode_list[self.active_mode]])
        self.active_mode += 1 # next mode
        self.start_level()

    def end_challenge(self):
        # go back to regular play
        self.game.remove_modes([self])
        self.game.update_lamps()
        self.exit_callback()

    def update_lamps(self):
        self.game.lamps.ultChallenge.enable()
        self.game.disable_drop_lamps()

    def sw_popperR_active_for_300ms(self, sw):
        self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)


class ChallengeBase(TimedMode):
    """Base class for all wizard modes"""

    def __init__(self, game, priority, initial_time, instructions, num_shots_required, num_balls, ball_save_time):
        name = self.__class__.__name__
        super(ChallengeBase, self).__init__(game, priority, 0, name, instructions, num_shots_required)
        self.initial_time = initial_time
        self.num_balls = num_balls
        self.ball_save_time = ball_save_time

    def mode_started(self):
        super(ChallengeBase, self).mode_started()
        self.started = False
        if self.num_balls > 1:
            self.game.addPlayerState('multiball_active', 0x8)

    def mode_stopped(self):
        super(ChallengeBase, self).mode_stopped()
        if self.num_balls > 1:
            self.game.addPlayerState('multiball_active', -0x8)

    def ready(self):
        if self.game.switches.popperR.is_active():
            # we were started from regular mode
            # put the ball back in play and start the timer if applicable
            self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)
            self.start()
        else:
            # wait for the player to plunge the ball
            self.game.sound.play_music('ball_launch', loops=-1)

    def start(self):
        # the first ball is now in play (popped from popperR or plunged by player)
        if self.ball_save_time > 0:
            self.game.ball_save_start(num_balls_to_save=self.num_balls, time=self.ball_save_time, now=True, allow_multiple_saves=True)

        if self.initial_time > 0:
            self.start_timer(self.initial_time)

        # launch remaining balls for the mode (if applicable)
        self.game.base_play.auto_plunge = True
        balls_to_launch = self.num_balls - self.game.trough.num_balls_in_play
        if balls_to_launch > 0:
            self.game.launch_balls(balls_to_launch)

        self.started = True

    def sw_shooterR_inactive_for_900ms(self, sw):
        if not self.started:
            self.start()

    def sw_leftRampToLock_active(self, sw):
        self.game.deadworld.eject_balls(1)

    def sw_dropTargetJ_active_for_250ms(self, sw):
        self.drop_target_active()

    def sw_dropTargetU_active_for_250ms(self, sw):
        self.drop_target_active()

    def sw_dropTargetD_active_for_250ms(self, sw):
        self.drop_target_active()

    def sw_dropTargetG_active_for_250ms(self, sw):
        self.drop_target_active()

    def sw_dropTargetE_active_for_250ms(self, sw):
        self.drop_target_active()

    def reset_drops(self):
        self.game.coils.resetDropTarget.pulse(30)


class DarkJudge(ChallengeBase):
    """Base class for dark judge wizard modes"""

    def __init__(self, game, priority, initial_time, instructions, num_shots_required, num_balls, ball_save_time):
        super(DarkJudge, self).__init__(game, priority, initial_time, instructions, num_shots_required, num_balls, ball_save_time)
        self.taunt_sound = self.name.lower() + ' - taunt'

    def expired(self):
        self.finish(success=False)

    def taunt(self):
        self.game.sound.play_voice(self.taunt_sound)
        self.delay(name='taunt', event_type=None, delay=20, handler=self.taunt)

    def drop_target_active(self):
        self.reset_drops()

    def check_for_completion(self):
        self.update_status()
        if self.num_shots == self.num_shots_required:
            self.finish(True)

    def finish(self, success):
        self.cancel_delayed('taunt')
        self.stop_timer()
        self.game.enable_flippers(False)
        self.game.update_lamps()
        text = self.name + ' Defeated' if success else 'You lose'
        self.layer = TextLayer(128/2, 13, self.game.fonts['tiny7'], 'center', True).set_text(text)
        if success:
            self.game.score(100000)
        self.exit_callback(success)


class Fear(DarkJudge):
    """ Fear wizard mode
        Judge Fear is reigning terror on the city.
        Shoot alternating ramps then subway
        1 ball with temporary ball save.
        Timer is short and resets with every successful shot
    """

    def __init__(self, game, priority):
        self.time_for_shot = game.user_settings['Gameplay']['Time for Fear shot']
        ball_save_time = game.user_settings['Gameplay']['Fear ballsave time']
        super(Fear, self).__init__(game, priority, initial_time=self.time_for_shot, instructions='Shoot lit ramps then subway',
                    num_shots_required=5, num_balls=1, ball_save_time=ball_save_time)

    def mode_started(self):
        super(Fear, self).mode_started()
        self.mystery_lit = True
        self.state = 'ramps'
        self.active_ramp = 'left'

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
            self.reset_timer(2 * self.time_for_shot)
            self.game.update_lamps()

    def sw_leftRampExit_active(self, sw):
        if self.state == 'ramps' and self.active_ramp == 'left':
            self.ramp_shot_hit()

    def sw_rightRampExit_active(self, sw):
        if self.state == 'ramps' and self.active_ramp == 'right':
            self.ramp_shot_hit()

    def ramp_shot_hit(self):
        if self.num_shots < self.num_shots_required - 1:
            self.game.score(10000)
            self.num_shots += 1
            self.update_status()
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            if self.num_shots == self.num_shots_required - 1:
                self.state = 'subway'
            else:
                # switch ramp
                self.active_ramp = 'right' if self.active_ramp == 'left' else 'left'
        self.reset_timer(self.time_for_shot)
        self.game.update_lamps()

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
            super(Fear, self).reset_drops()

    def sw_subwayEnter1_closed(self, sw):
        self.subway_hit()

    # Ball might jump over first switch.  Use 2nd switch as a catch all.
    def sw_subwayEnter2_closed(self, sw):
        if self.num_shots < self.num_shots_required:
            self.subway_hit()

    def subway_hit(self):
        if self.state == 'subway':
            self.num_shots += 1
            self.update_status()
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.finish(success=True)

    def finish(self, success):
        self.state = 'finished'
        super(Fear, self).finish(success)


class Mortis(DarkJudge):
    """ Mortis wizard mode
        Judge Mortis is spreading disease throughout the city.
        Shoot the lit shots.
        2 ball multiball with temporary ball save.
        No timer, mode ends when last ball is lost
    """

    def __init__(self, game, priority):
        ball_save_time = game.user_settings['Gameplay']['Mortis ballsave time']
        super(Mortis, self).__init__(game, priority, initial_time=0, instructions='Shoot lit shots',
                         num_shots_required=5, num_balls=2, ball_save_time=ball_save_time)
        self.lamp_names = ['mystery', 'perp1G', 'perp3G', 'perp5G', 'stopMeltdown']

    def mode_started(self):
        super(Mortis, self).mode_started()
        self.targets = [1, 1, 1, 1, 1]

    def timer_update(self, time):
        pass

    def update_lamps(self):
        schedule = 0x80808080 if any(self.targets) else 0
        self.game.coils.flasherMortis.schedule(schedule=schedule, cycle_seconds=0, now=True)

        for shot in range(0, 5):
            lamp_name = self.lamp_names[shot]
            style = 'medium' if self.targets[shot] else 'off'
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

    def sw_captiveBall2_active(self, sw): # make it easier with captiveBall2 instead of captiveBall3
        self.switch_hit(4)

    def switch_hit(self, index):
        if self.targets[index]:
            self.targets[index] = 0
            self.num_shots += 1
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.check_for_completion()


class Death(DarkJudge, CrimeSceneShots):
    """ Death wizard mode
        Judge Death is on a murder spree.
        Shoot crime scene shots quickly before they relight.
        1 ball with temporary ball save.
        Timer is long and always counts down.
    """

    def __init__(self, game, priority):
        initial_time = game.user_settings['Gameplay']['Time for Death']
        ball_save_time = game.user_settings['Gameplay']['Death ballsave time']
        self.time_for_shot = game.user_settings['Gameplay']['Time for Death shot']
        super(Death, self).__init__(game, priority, initial_time=initial_time, instructions='Shoot lit shots quickly',
                    num_shots_required=5, num_balls=1, ball_save_time=ball_save_time)
        self.shot_order = [4, 2, 0, 3, 1] # from easiest to hardest

    def mode_started(self):
        super(Death, self).mode_started()
        self.shot_timer = self.time_for_shot
        self.active_shots = [1, 1, 1, 1, 1]
        self.reset_drops()

    def update_lamps(self):
        schedule = 0x80808080 if any(self.active_shots) else 0
        self.game.coils.flasherDeath.schedule(schedule=schedule, cycle_seconds=0, now=True)

        for shot in range(0, 5):
            style = 'off' if self.active_shots[shot] == 0 else 'medium'
            self.game.drive_lamp('perp' + str(shot + 1) + 'W', style)

    def switch_hit(self, index):
        if self.active_shots[index]:
            self.active_shots[index] = 0
            self.num_shots += 1
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.shot_timer = self.time_for_shot
            self.check_for_completion()

    def add_shot(self):
        for shot in self.shot_order:
            if not self.active_shots[shot]:
                self.active_shots[shot] = 1
                self.num_shots -= 1
                break
        self.game.update_lamps()

    def decrement_timer(self):
        super(Death, self).decrement_timer()
        if self.shot_timer > 0:
            self.shot_timer -= 1
        else:
            self.shot_timer = self.time_for_shot
            self.add_shot()

    def finish(self, success):
        self.active_shots = [0, 0, 0, 0, 0]
        super(Death, self).finish(success)


class Fire(DarkJudge, CrimeSceneShots):
    """ Fire wizard mode
        Judge Fire is lighting fires all over Mega City One.
        Shoot each crime scene shot twice.
        4 ball multiball.  No ball save. Possibility to add two more balls.
        No timer, mode ends when last ball is lost
    """

    def __init__(self, game, priority):
        super(Fire, self).__init__(game, priority, initial_time=0, instructions='Shoot lit shots twice',
                    num_shots_required=10, num_balls=4, ball_save_time=0)
        self.lamp_styles = ['off', 'medium', 'fast']

    def mode_started(self):
        super(Fire, self).mode_started()
        self.mystery_lit = True
        self.shots_required = [2, 2, 2, 2, 2]

    def timer_update(self, time):
        pass

    def update_lamps(self):
        self.game.enable_gi(False)

        schedule = 0x80808080 if self.num_shots < self.num_shots_required else 0
        self.game.coils.flasherFire.schedule(schedule=schedule, cycle_seconds=0, now=True)

        for shot in range(0, 5):
            lamp_name = 'perp' + str(shot + 1) + 'R'
            style = self.lamp_styles[self.shots_required[shot]]
            self.game.drive_lamp(lamp_name, style)

    def sw_mystery_active(self, sw):
        self.game.sound.play('mystery')
        if self.mystery_lit:
            self.mystery_lit = False
            self.game.set_status('Add 2 balls')
            self.game.launch_balls(2)
            self.game.update_lamps()

    def switch_hit(self, index):
        if self.shots_required[index] > 0:
            self.shots_required[index] -= 1
            self.num_shots += 1
            self.game.lampctrl.play_show('shot_hit', False, self.game.update_lamps)
            self.game.score(10000)
            self.check_for_completion()

    def finish(self, success):
        self.mystery_lit = False
        super(Fire, self).finish(success)


class Celebration(ChallengeBase, CrimeSceneShots):
    """ Final multiball wizard mode after all dark judges have been defeated
        All shots score.
        6 ball multiball with temporary ball save.
        No timer, mode ends when a single ball remains.
    """

    def __init__(self, game, priority):
        ball_save_time = game.user_settings['Gameplay']['Celebration ballsave time']
        super(Celebration, self).__init__(game, priority, initial_time=0, instructions='All shots score',
                     num_shots_required=0, num_balls=6, ball_save_time=ball_save_time)

    def mode_started(self):
        super(Celebration, self).mode_started()
        # This player reached the end of supergame, his next ball is regular play
        # do this early now in case the game tilts
        self.game.setPlayerState('supergame', False)

    def update_lamps(self):
        # rotate 0xFFFF0000 pattern to all 32 bit positions
        lamp_schedules = [(0xFFFF0000 >> d)|(0xFFFF0000 << (32 - d)) & 0xFFFFFFFF for d in range (0, 32)]
        shuffle(lamp_schedules)

        i = 0
        for lamp in self.game.lamps:
            if lamp.name not in ['gi01', 'gi02', 'gi03', 'gi04', 'gi05', 'startButton', 'buyIn', 'drainShield', 'superGame', 'judgeAgain']:
                lamp.schedule(schedule=lamp_schedules[i%32], cycle_seconds=0, now=False)
                i += 1

    # By default, Ultimate Challenge modes ignore evt_ball_drained,
    # so BasePlay.drain_callback() will end the mode when the number of balls reaches 0
    # That's how multiball Challenge modes continue to run on a single ball.
    # (RegularPlay.evt_ball_drained() ends multiball modes on the last ball
    # but remember RegularPlay does not run when UltimateChallenge is running.)
    # Celebration is the only multiball Challenge mode that ends on the last ball in play
    # therefore it has to trap evt_ball_drained and implement that behavior itself.

    def evt_ball_drained(self):
        # The trough does not expect a multiball to start from 0 balls and gets confused,
        # It calls the end multiball callback when launching the first ball
        # thinking we got down to 1 ball when in fact we are going up to 6 balls.
        # The ball saver might also bring back the second ball from the dead,
        # so wait until the first ball is in play and we requested all the balls we wanted
        # and we are indeed on the last ball.
        if (self.started and self.game.trough.num_balls_in_play == 1 and
             self.game.trough.num_balls_to_launch == 0):
            # down to just one ball, revert to regular play
            self.exit_callback(False)
        # else celebration continues until we are really down to the last ball

    def evt_shooterL_active_500ms(self):
        self.switch_hit(6)

    def sw_mystery_active(self, sw):
        self.switch_hit(7)

    def sw_leftScorePost_active(self, sw):
        self.switch_hit(8)

    def drop_target_active(self):
        self.switch_hit(9)
        if (self.game.switches.dropTargetJ.is_active() and
                self.game.switches.dropTargetU.is_active() and
                self.game.switches.dropTargetD.is_active() and
                self.game.switches.dropTargetG.is_active() and
                self.game.switches.dropTargetE.is_active()):
            self.reset_drops()

    def sw_subwayEnter2_closed(self, sw):
        self.switch_hit(10)

    def sw_rightTopPost_active(self, sw):
        self.switch_hit(11)

    def sw_threeBankTargets_active(self, sw):
        self.switch_hit(12)

    def sw_captiveBall1_active(self, sw):
        self.switch_hit(13)

    def sw_captiveBall2_active(self, sw):
        self.switch_hit(14)

    def sw_captiveBall3_active(self, sw):
        self.switch_hit(15)

    def switch_hit(self, unused): # unused variable is the shot number
        self.game.score(10000)
        self.num_shots += 1
        self.update_status()

    def update_status(self):
        self.status_layer.set_text('Shots made: ' + str(self.num_shots))
