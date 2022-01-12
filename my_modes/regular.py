import locale
from procgame.dmd import MarkupFrameGenerator, PanningLayer, ScriptedLayer, TextLayer
from procgame.modes import Scoring_Mode
from chain import Chain
from crimescenes import CrimeScenes
from intro import Introduction
from multiball import Multiball
from missile import MissileAwardMode

class RegularPlay(Scoring_Mode):
    """Controls all play except ultimate challenge"""

    def __init__(self, game, priority):
        super(RegularPlay, self).__init__(game, priority)

        # Instantiate sub-modes
        self.game_intro = Introduction(self.game, priority + 1, delay=1.0)
        instruct_frame = MarkupFrameGenerator().frame_for_markup(self.get_instructions())
        instruct_layer = PanningLayer(width=128, height=32, frame=instruct_frame, origin=(0,0), translate=(0,1), bounce=False)
        script = [{'seconds':21.0, 'layer':instruct_layer}]
        self.game_intro.layer = ScriptedLayer(width=128, height=32, script=script)

        self.shoot_again_intro = Introduction(self.game, priority + 1, delay=1.0)
        big_font = self.game.fonts['jazz18']
        shoot_again_layer = TextLayer(128/2, 9, big_font, 'center').set_text('Shoot Again', 3)
        script = [{'seconds':99999999.0, 'layer':shoot_again_layer}]
        self.shoot_again_intro.layer = ScriptedLayer(width=128, height=32, script=script)
        
        self.chain = Chain(self.game, priority)

        self.crime_scenes = CrimeScenes(game, priority + 1)
        self.crime_scenes.start_multiball_callback = self.multiball_started
        self.crime_scenes.end_multiball_callback = self.multiball_ended

        self.multiball = Multiball(self.game, priority + 1)
        self.multiball.start_callback = self.multiball_started
        self.multiball.end_callback = self.multiball_ended

        self.missile_award_mode = MissileAwardMode(game, priority + 10)

    def reset_modes(self):
        for mode in [self.chain, self.crime_scenes, self.multiball, self.missile_award_mode]:
            mode.reset()

        # reset RegularPlay itself
        self.light_mystery(False)

    def mode_started(self):
        self.mystery_lit = self.game.getPlayerState('mystery_lit', False)
        self.welcomed = False
        self.state = 'init'
        self.game.add_modes([self.chain, self.crime_scenes, self.multiball, self.missile_award_mode])
        self.setup_next_mode()

    def mode_stopped(self):
        self.game.remove_modes([self.chain, self.crime_scenes, self.multiball, self.missile_award_mode])
        self.game.setPlayerState('mystery_lit', self.mystery_lit)


    #### DEBUG: push the buy in button to go straight to ultimate challenge from regular mode
    def sw_buyIn_active(self, sw):
        self.game.remove_modes([self.chain, self.crime_scenes])
        self.multiball.jackpot_collected = True
        self.game.setPlayerState('crime_scenes_complete', True)
        self.game.setPlayerState('modes_remaining', [])
        self.game.add_modes([self.chain, self.crime_scenes])
        self.game.update_lamps()
        self.setup_next_mode()

    def sw_shooterR_active(self, sw):
        if self.game.base_play.ball_starting:
            if not self.welcomed:
                self.welcomed = True
                self.welcome()
                self.high_score_mention()

    #
    # Message
    #

    def welcome(self):
        if self.game.ball == 1:
            self.game.sound.play_voice('welcome')
            self.game.modes.add(self.game_intro)
        elif self.game.shooting_again:
            self.game.sound.play_voice('shoot again ' + str(self.game.current_player_index + 1))
            self.game.modes.add(self.shoot_again_intro)

    def get_instructions(self):
        return """

#INSTRUCTIONS#

Hit Right Fire to abort

To light Ultimate Challenge:
Attempt all chain features
Complete 16 crimescene levels
Collect a multiball jackpot

Start chain features by shooting the Build Up Chain Feature shot when lit

Chain feature instructions are displayed when starting each feature

Complete crime scene levels by shooting lit crimescene shots

Light locks by completing JUDGE target bank

During multiball, shoot left ramp to light jackpot then shoot subway to collect




"""

    def high_score_mention(self):
        if self.game.ball == self.game.balls_per_game:
            if self.game.base_play.replay.replay_achieved[0]:
                text = 'Highest Score'
                score = str(self.game.game_data['ClassicHighScoreData'][0]['inits']) + '  ' + locale.format('%d', self.game.game_data['ClassicHighScoreData'][0]['score'], True)
            else:
                text = 'Replay'
                score = locale.format('%d', self.game.base_play.replay.replay_scores[0], True)
            self.game.base_play.show_on_display(text, score)

    def sw_shooterL_active_for_500ms(self, sw):
        if self.any_multiball_active():
            self.game.coils.shooterL.pulse()

    def ball_started(self):
        if self.game.base_play.ball_starting and not self.game.base_play.tilt.tilted:
            ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
            self.game.ball_save.callback = self.ball_save_callback
            self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=True, allow_multiple_saves=False)
        self.game.remove_modes([self.game_intro, self.shoot_again_intro])
        self.game.update_lamps()

    #
    # submodes
    #

    # called right after a mode has ended to decide the next state
    # the rule is: multiball can be stacked with a running mode, you cannot start a new mode during multiball
    def setup_next_mode(self):
        # a mode could still be running if modes were stacked, in that case do nothing and stay 'busy'
        if not (self.any_multiball_active() or self.chain.is_active()):
            self.game.sound.fadeout_music()
            self.game.sound.play_music('background', loops=-1)

            if self.is_ultimate_challenge_ready():
                # player needs to shoot the right popper to start the finale
                self.state = 'challenge_ready'
                self.game.modes.remove(self.multiball)
                self.light_mystery(False)
            elif not self.chain.is_complete():
                # player needs to shoot the right popper to start the next chain mode
                self.state = 'chain_ready'
            else:
                self.state = 'chain_complete'
                
        self.game.update_lamps()

    # starts a mode if a mode is available
    # the 300ms delay must be the same or longer than the popperR handler in crime scenes
    # If that shot starts block war multiball, we want crime scenes to go first and change the state to busy
    # so we don't start something else here
    def sw_popperR_active_for_300ms(self, sw):
        if self.state == 'chain_ready':
            self.state = 'busy'
            self.chain.start_chain_mode()
        elif self.state == 'challenge_ready':
            self.state = 'busy'
            self.start_ultimate_challenge()
        else: # state 'busy' or 'chain_complete'
            self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR', 20)

        self.game.update_lamps()

    def crime_scenes_completed(self):
        self.setup_next_mode()

    def chain_mode_completed(self):
        self.setup_next_mode()

    #
    # Multiball
    #

    def any_multiball_active(self):
        return self.multiball.is_active() or self.crime_scenes.is_multiball_active()

    def multiball_started(self):
        # Make sure no other multiball was already active before preparing for multiball.
        # One multiball is the caller, so if both are active it means the other multiball was already active
        if not (self.multiball.is_active() and self.crime_scenes.is_multiball_active()):
            self.state = 'busy'
            self.game.sound.fadeout_music()
            self.game.sound.play_music('multiball', loops=-1)
            self.game.modes.remove(self.missile_award_mode)
            # Light mystery once for free.
            self.light_mystery()
            # light mystery updated the lamps

    def multiball_ended(self):
        if not self.any_multiball_active():
            self.game.modes.add(self.missile_award_mode)
        self.setup_next_mode()

    #
    # Ultimate Challenge
    #

    def is_ultimate_challenge_ready(self):
        # 3 Criteria for finale
        return (self.multiball.jackpot_collected and
                self.game.getPlayerState('crime_scenes_complete', False) and
                self.chain.is_complete())

    def start_ultimate_challenge(self):
        self.game.remove_modes([self.chain, self.crime_scenes, self.multiball, self])
        self.reset_modes()
        self.game.base_play.start_ultimate_challenge()
        # ultimate challenge updated the lamps

    #
    # Mystery
    #

    def light_mystery(self, lit=True):
        self.mystery_lit = lit
        self.game.update_lamps()

    def sw_captiveBall1_active(self, sw):
        self.game.sound.play('meltdown')

    def sw_captiveBall2_active(self, sw):
        self.game.sound.play('meltdown')

    def sw_captiveBall3_active(self, sw):
        self.game.sound.play('meltdown')
        self.game.base_play.inc_bonus_x()
        self.light_mystery()

    def sw_mystery_active(self, sw):
        self.game.sound.play('mystery')
        if self.mystery_lit:
            self.light_mystery(False)
            if self.any_multiball_active():
                if self.game.ball_save.timer > 0:
                    self.game.set_status('+10 second ball saver')
                    self.game.ball_save.add(10)
                else:
                    self.game.ball_save.callback = None
                    self.game.set_status('save ' + str(self.game.trough.num_balls_in_play) + ' balls')
                    self.game.ball_save.start(num_balls_to_save=self.game.trough.num_balls_in_play, time=10, now=True, allow_multiple_saves=True)

            elif self.chain.is_active():
                self.chain.mode.add(10)
                self.game.set_status('Adding 10 seconds')
            else:
                self.game.ball_save.callback = self.ball_save_callback
                self.game.ball_save.start(num_balls_to_save=1, time=10, now=True, allow_multiple_saves=True)
                self.game.set_status('+10 second ball saver')
                self.missile_award_mode.light_missile_award()

    #
    # Lamps
    #

    def update_lamps(self):
        self.game.enable_gi(True)

        style = 'on' if self.mystery_lit else 'off'
        self.game.drive_lamp('mystery', style)

        style = 'slow' if self.state == 'chain_ready' or self.state == 'challenge_ready' else 'off'
        self.game.drive_lamp('rightStartFeature', style)
        
        style = 'slow' if self.state == 'challenge_ready' else 'off'
        self.game.drive_lamp('ultChallenge', style)

    #
    # End of ball
    #

    def sw_outlaneL_active(self, sw):
        self.outlane_hit()

    def sw_outlaneR_active(self, sw):
        self.outlane_hit()

    def outlane_hit(self):
        self.game.score(1000)
        if self.any_multiball_active() or self.game.trough.ball_save_active:
            self.game.sound.play('outlane')
        else:
            self.game.sound.play_voice('curse')

    def ball_save_callback(self):
        if not self.any_multiball_active():
            self.game.sound.play_voice('ball saved')
            self.game.base_play.show_on_display('Ball Saved!')

    def ball_drained(self):
        # Called as a result of a ball draining into the trough.
        # End multiball if there is now only one ball in play (and MB was active).
        self.game.ball_save.callback = None
        if self.game.trough.num_balls_in_play == 1:
            if self.multiball.is_active():
                self.multiball.end_multiball()
            if self.crime_scenes.is_multiball_active():
                self.crime_scenes.end_multiball()
