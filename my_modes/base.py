from random import randint
from procgame.dmd import AnimatedLayer, GroupedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Replay
from boring import Boring
from bonus import Bonus
from challenge import UltimateChallenge
from combos import Combos
from regular import RegularPlay
from status import StatusReport

class BasePlay(Mode):
    """Base rules for all the time the ball is in play"""

    def __init__(self, game, priority):
        super(BasePlay, self).__init__(game, priority)

        self.max_extra_balls_per_game = self.game.user_settings['Gameplay']['Max extra balls per game']
        self.max_extra_balls_lit = self.game.user_settings['Gameplay']['Max extra balls lit']
        self.replay_award = self.game.user_settings['Replay']['Replay Award']

        self.boring = Boring(self.game, priority + 6)
        self.combos = Combos(self.game, priority + 25)
        self.status_report = StatusReport(self.game, priority + 26)
        self.regular_play = RegularPlay(self.game, priority + 5)

        self.ultimate_challenge = UltimateChallenge(game, priority + 5)
        self.ultimate_challenge.exit_callback = self.ultimate_challenge_ended

        self.replay = Replay(self.game, priority + 15)
        self.replay.replay_callback = self.replay_callback

        self.bonus = Bonus(self.game, priority + 6)
        self.bonus.exit_callback = self.bonus_ended

        self.display_mode = ModesDisplay(self.game, priority + 700)
        self.animation_mode = ModesAnimation(self.game, priority + 701)

    def mode_started(self):
        # init player state
        player = self.game.current_player()
        self.total_extra_balls = player.getState('total_extra_balls', 0)

        bonus_x = player.getState('bonus_x', 1) if player.getState('hold_bonus_x', False) else 1
        player.setState('bonus_x', bonus_x)
        player.setState('hold_bonus_x', False)

        # Do a quick lamp show
        self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
        self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

        self.game.launch_balls(1)
        self.game.ball_save.callback = self.ball_save_callback
        self.ball_starting = True
        self.welcome()

        # Force player to hit the right Fire button for the start of ball
        self.auto_plunge = False

        # Start modes
        self.game.enable_flippers(True)
        self.game.add_modes([self.combos, self.replay, self.display_mode, self.animation_mode])

        if player.getState('supergame', self.game.supergame):
            self.start_ultimate_challenge()
        else:
            self.game.modes.add(self.regular_play)

    def mode_stopped(self):
        self.game.remove_modes([self.combos, self.replay, self.display_mode, self.animation_mode, self.boring, self.regular_play, self.ultimate_challenge])
        self.game.enable_flippers(False)
        self.game.ball_save.callback = None

        self.game.setPlayerState('total_extra_balls', self.total_extra_balls)

    def update_lamps(self):
        # Disable all lamps except GI
        self.game.disable_all_lights()
        self.game.enable_gi(True)

        style = 'on' if self.game.current_player().extra_balls else 'off'
        self.game.drive_lamp('judgeAgain', style)

        style = 'slow' if self.game.getPlayerState('extra_balls_lit', 0) else 'off'
        self.game.drive_lamp('extraBall2', style)

    #
    # Welcome
    #

    def welcome(self):
        self.welcome_display_time = 0
        if self.game.shooting_again:
            self.game.sound.play_voice('shoot again ' + str(self.game.current_player_index + 1))
            self.display('Shoot Again')
            self.welcome_display_time = 3
        elif self.game.ball == 1:
            self.game.sound.play_voice('welcome')

        # high score mention
        if self.game.ball == self.game.balls_per_game:
            if self.game.shooting_again:
                # display the score to beat after the Shoot Again message
                self.delay('high_score_mention', event_type=None, delay=3, handler=self.high_score_mention)
                self.welcome_display_time = 6
            else:
                self.high_score_mention()

    def high_score_mention(self):
        if self.replay.replay_achieved[0]:
            text = 'High Score'
            game_data_key = 'SuperGameHighScoreData' if self.game.supergame else 'ClassicHighScoreData'
            score = self.game.game_data[game_data_key][0]['score']
        else:
            text = 'Replay'
            score = self.replay.replay_scores[0]
        self.display(text, score)

    def remove_welcome(self):
        self.game.base_play.display('')
        self.cancel_delayed('high_score_mention')

    #
    # Display text or animation
    #

    def display(self, text=None, points=None):
        self.display_mode.display(text, points)

    def play_animation(self, anim_name, frame_time=1):
        anim = self.game.animations[anim_name]
        self.animation_mode.play(anim, repeat=False, hold=False, frame_time=frame_time)

    #
    # Sound
    #

    def play_background_music(self):
        self.game.sound.play_music('background', loops=-1)

    #
    # Status Report
    #

    def sw_flipperLwL_active(self, sw):
        self.start_show_status_timer()

    def sw_flipperLwR_active(self, sw):
        self.start_show_status_timer()

    def sw_flipperLwL_inactive(self, sw):
        self.cancel_show_status_timer()

    def sw_flipperLwR_inactive(self, sw):
        self.cancel_show_status_timer()

    def cancel_show_status_timer(self):
        self.cancel_delayed('show_status')

    def start_show_status_timer(self):
        self.cancel_show_status_timer()
        self.delay('show_status', event_type=None, delay=6.0, handler=self.display_status_report)

    def display_status_report(self):
        if not self.status_report in self.game.modes:
            self.game.modes.add(self.status_report)

    #
    # Fire Buttons
    #

    def sw_fireR_active(self, sw):
        if self.game.switches.shooterR.is_active():
            self.game.coils.shooterR.pulse(50)
            if self.ball_starting:
                self.game.sound.stop_music()
                self.play_background_music()


    #
    # Shooter Lanes
    #

    def sw_shooterR_inactive_for_300ms(self, sw):
        self.game.sound.play('ball_launch')
        self.play_animation('bikeacrosscity', frame_time=5)

    def sw_shooterR_inactive_for_1s(self, sw):
        # Enable auto-plunge soon after the new ball is launched (by the player).
        self.auto_plunge = True

        if self.ball_starting:
            self.game.send_event('evt_ball_started')
            # send the event only once per ball
            self.ball_starting = False

    # event called when the ball is initially plunged by the player
    def evt_ball_started(self):
        # remove welcome message early if the player was very quick to plunge
        self.remove_welcome()

        # normally a skillshot would be a mode added here
        # but for us the skillshot is the same as another mode with different scoring
        self.combos.skill_shot_begin()
        self.game.modes.add(self.boring)
        # Tell game to save ball start time now, since ball is now in play.
        self.game.save_ball_start_time()

    def sw_shooterR_active(self, sw):
        if self.ball_starting:
            self.game.sound.play_music('ball_launch', loops=-1)
 
    def sw_shooterR_closed_for_700ms(self, sw):
        if self.auto_plunge:
            self.game.coils.shooterR.pulse(50)

    def sw_shooterL_active_for_500ms(self, sw):
        self.game.send_event('evt_shooterL_active_500ms')

    def evt_shooterL_active_500ms(self):
        self.game.coils.shooterL.pulse(randint(15, 30))

    def sw_shooterL_inactive_for_200ms(self, sw):
        self.game.sound.play('shooterL_launch')

    #
    # Extra ball
    #

    def light_extra_ball(self):
        extra_balls_lit = self.game.getPlayerState('extra_balls_lit', 0)
        if extra_balls_lit + self.total_extra_balls == self.max_extra_balls_per_game:
            self.game.set_status('EXTRA BALLS MAXED')
        elif extra_balls_lit == self.max_extra_balls_lit:
            self.game.set_status('EXTRA BALLS LIT MAXED')
        else:
            self.game.setPlayerState('extra_balls_lit', extra_balls_lit + 1)
            self.game.update_lamps()
            self.game.set_status('EXTRA BALL LIT')

    def sw_leftScorePost_active(self, sw):
        self.extra_ball_switch_hit()

    def sw_rightTopPost_active(self, sw):
        self.extra_ball_switch_hit()

    def extra_ball_switch_hit(self):
        self.game.sound.play('extra_ball_target')
        extra_balls_lit = self.game.getPlayerState('extra_balls_lit', 0)
        if extra_balls_lit:
            self.game.setPlayerState('extra_balls_lit', extra_balls_lit - 1)
            self.display('Extra Ball')
            self.extra_ball()

    def extra_ball(self):
        player = self.game.current_player()
        player.extra_balls += 1
        self.total_extra_balls += 1
        self.play_animation('extra ball')
        self.game.update_lamps()

    #
    # Replay
    #

    def replay_callback(self):
        self.game.coils.knocker.pulse(50)
        if self.replay_award == 'Extra Ball':
            if self.total_extra_balls < self.max_extra_balls_per_game:
                self.display('Replay')
                extra_balls_lit = self.game.getPlayerState('extra_balls_lit', 0)
                if extra_balls_lit + self.total_extra_balls == self.max_extra_balls_per_game:
                    # already maximum allocated, convert a lit extra ball to an extra ball instead
                    self.game.setPlayerState('extra_balls_lit', extra_balls_lit - 1)
                self.extra_ball()
            else:
                self.display('Replay Award', 100000)
                self.game.score(100000)
        else:
            self.display('Replay')
            # add a credit in your head

    #
    # Ultimate Challenge
    #

    def start_ultimate_challenge(self):
        self.game.remove_modes([self.regular_play])
        self.game.modes.add(self.ultimate_challenge)
        self.game.update_lamps()

    def ultimate_challenge_ended(self):
        self.game.remove_modes([self.ultimate_challenge])
        self.game.modes.add(self.regular_play)
        self.game.update_lamps()

    #
    # Drop Targets
    #

    def sw_dropTargetJ_active(self, sw):
        self.game.sound.play('drop_target')
        self.game.score(1000)

    def sw_dropTargetU_active(self, sw):
        self.game.sound.play('drop_target')
        self.game.score(1000)

    def sw_dropTargetD_active(self, sw):
        pass

    def sw_dropTargetG_active(self, sw):
        self.game.sound.play('drop_target')
        self.game.score(1000)

    def sw_dropTargetE_active(self, sw):
        self.game.sound.play('drop_target')
        self.game.score(1000)

    def sw_subwayEnter2_active(self, sw):
        self.game.score(1000)

    #
    # Ramps
    #

    def sw_leftRampEnter_active(self, sw):
        self.game.coils.flasherGlobe.schedule(0x33333, cycle_seconds=1, now=False)
        self.game.coils.flasherCursedEarth.schedule(0x33333, cycle_seconds=1, now=False)

    def sw_leftRampExit_active(self, sw):
        self.game.sound.play('left_ramp')
        self.game.score(2000)

    def sw_rightRampExit_active(self, sw):
        self.game.sound.play('right_ramp')
        self.game.coils.flashersRtRamp.schedule(0x33333, cycle_seconds=1, now=False)
        self.game.score(2000)

    #
    # Slings
    #

    def sw_slingL_active(self, sw):
        self.game.sound.play('slingshot')
        self.game.score(110)

    def sw_slingR_active(self, sw):
        self.game.sound.play('slingshot')
        self.game.score(110)

    #
    # Inlanes
    #

    def sw_inlaneL_active(self, sw):
        self.inlane_active()

    def sw_inlaneR_active(self, sw):
        self.inlane_active()

    def sw_inlaneFarR_active(self, sw):
        self.inlane_active()

    def inlane_active(self):
        self.game.sound.play('inlane')
        self.game.score(500)

    #
    # Outlanes
    #

    def sw_outlaneL_active(self, sw):
        self.outlane_hit()

    def sw_outlaneR_active(self, sw):
        self.outlane_hit()

    def outlane_hit(self):
        self.game.score(1000)
        if self.game.num_balls_requested() > 1 or self.game.trough.ball_save_active:
            self.game.sound.play('outlane')
        else:
            self.game.sound.play_voice('curse')

    #
    # Coil
    #

    def sw_popperL_active_for_200ms(self, sw):
        self.flash_then_pop('flashersLowerLeft', 'popperL', 50)

    def flash_then_pop(self, flasher, coil, pulse):
        self.game.coils[flasher].schedule(0x00555555, cycle_seconds=1, now=True)
        self.delay(name='delayed_pop', event_type=None, delay=0.8, handler=self.delayed_pop, param=[coil, pulse])

    def delayed_pop(self, coil_pulse):
        self.game.coils[coil_pulse[0]].pulse(coil_pulse[1])

    #
    # Ball Save
    #

    def ball_save_callback(self):
        self.combos.skill_shot_expired()
        if not self.game.getPlayerState('multiball_active', 0):
            self.game.sound.play_voice('ball saved')
            self.display('Ball Saved')

    #
    # Bonus
    #

    def inc_bonus_x(self):
        player = self.game.current_player()
        bonus_x = player.getState('bonus_x') + 1
        player.setState('bonus_x', bonus_x)
        self.game.set_status('BONUS AT ' + str(bonus_x) + 'X')

    def hold_bonus_x(self):
        self.game.setPlayerState('hold_bonus_x', True)
        self.game.set_status('HOLD BONUS X')

    def evt_ball_ended(self):
        self.game.remove_modes([self.boring, self.combos, self.regular_play, self.ultimate_challenge])
        self.game.add_modes([self.bonus])
        # cancel the event because the ball is not truly ended until bonus mode has ended
        return True

    def bonus_ended(self):
        self.game.remove_modes([self.bonus, self.replay])
        self.game.end_ball()


class ModesDisplay(Mode):
    """Display some text when the ball is active"""

    def __init__(self, game, priority):
        super(ModesDisplay, self).__init__(game, priority)
        self.big_text_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.small_text_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], 'center')
        self.points_layer = TextLayer(128/2, 17, self.game.fonts['num_14x10'], 'center')

    def display(self, text=None, points=None):
        layers = []
        if text:
            text_layer = self.small_text_layer if points is not None else self.big_text_layer
            text_layer.set_text(text, 3)
            layers.append(text_layer)
        if points is not None:
            self.points_layer.set_text(self.game.format_points(points), 3)
            layers.append(self.points_layer)
        self.layer = GroupedLayer(128, 32, layers)


class ModesAnimation(Mode):
    """Play an animation when the ball is active"""

    def play(self, anim, repeat=False, hold=False, frame_time=1):
        self.layer = AnimatedLayer(frames=anim.frames, repeat=repeat, hold=hold, frame_time=frame_time)
