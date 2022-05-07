from procgame.dmd import ScriptedLayer, TextLayer
from procgame.game import Mode
from chain import Chain
from blocks import CityBlocks
from intro import Introduction
from multiball import Multiball
from missile import MissileAwardMode

class RegularPlay(Mode):
    """Controls all play except ultimate challenge"""

    def __init__(self, game, priority):
        super(RegularPlay, self).__init__(game, priority)

        big_font = self.game.fonts['jazz18']
        shoot_again_layer = TextLayer(128/2, 7, big_font, 'center').set_text('Shoot Again', 99999999)
        script = [{'seconds':99999999.0, 'layer':shoot_again_layer}]
        self.shoot_again_intro = Introduction(self.game, priority + 1, delay=1.0)
        self.shoot_again_intro.setup(ScriptedLayer(width=128, height=32, script=script))

        self.chain = Chain(self.game, priority)

        self.city_blocks = CityBlocks(game, priority + 1)
        self.city_blocks.start_multiball_callback = self.multiball_starting
        self.city_blocks.end_multiball_callback = self.multiball_ended

        self.multiball = Multiball(self.game, priority + 1)
        self.multiball.start_callback = self.multiball_starting
        self.multiball.end_callback = self.multiball_ended

        self.missile_award_mode = MissileAwardMode(game, priority + 10)

    def reset_modes(self):
        for mode in [self.chain, self.city_blocks, self.multiball, self.missile_award_mode]:
            mode.reset()

        # reset RegularPlay itself
        self.mystery_lit = False

    def mode_started(self):
        self.mystery_lit = self.game.getPlayerState('mystery_lit', False)
        self.welcomed = False
        self.state = 'init'
        self.game.add_modes([self.chain, self.city_blocks, self.multiball, self.missile_award_mode])
        self.setup_next_mode()

    def mode_stopped(self):
        self.game.remove_modes([self.chain, self.city_blocks, self.multiball, self.missile_award_mode])
        self.game.setPlayerState('mystery_lit', self.mystery_lit)

    #### DEBUG: push the buy in button to go straight to ultimate challenge from regular mode
    ####        press multiple times in a row to skip Dark Judge modes
    def sw_buyIn_active(self, sw):
        # self.game.base_play.sw_shooterL_active_for_500ms(None)
        self.game.remove_modes([self.chain, self.city_blocks])
        if self.is_ultimate_challenge_ready() and self.game.getPlayerState('challenge_mode', 0) < 3:
            self.game.addPlayerState('challenge_mode', 1)
        self.game.setPlayerState('multiball_jackpot_collected', True)
        self.game.setPlayerState('blocks_complete', True)
        self.game.setPlayerState('chain_complete', True)
        self.game.setPlayerState('modes_remaining', [])
        self.chain.mode = None
        self.game.add_modes([self.chain, self.city_blocks])
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
        elif self.game.shooting_again:
            self.game.sound.play_voice('shoot again ' + str(self.game.current_player_index + 1))
            self.game.modes.add(self.shoot_again_intro)

    def high_score_mention(self):
        if self.game.ball == self.game.balls_per_game:
            if self.game.base_play.replay.replay_achieved[0]:
                text = 'High Score'
                game_data_key = 'SuperGameHighScoreData' if self.game.supergame else 'ClassicHighScoreData'
                high_score_data = self.game.game_data[game_data_key][0]
                score = str(high_score_data['inits']) + '  {:,}'.format(high_score_data['score'])
            else:
                text = 'Replay'
                score = self.game.format_points(self.game.base_play.replay.replay_scores[0])
            #this needs a redesign, it hides too much and/or looks ugly
            #self.game.base_play.display(text, score)

    def evt_ball_started(self):
        ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
        repeating_ballsave = self.game.user_settings['Gameplay']['New ball repeating ballsave']
        self.game.ball_save_start(time=ball_save_time, now=True, allow_multiple_saves=repeating_ballsave)
        self.game.remove_modes([self.shoot_again_intro])
        self.game.update_lamps()

    #
    # submodes
    #

    # called right after a mode has ended to decide the next state
    # the rule is: multiball can be stacked with a running mode, you cannot start a new mode during multiball
    def setup_next_mode(self):
        # a mode could still be running if modes were stacked, in that case do nothing and stay 'busy'
        if not (self.game.getPlayerState('multiball_active', 0) or self.game.getPlayerState('chain_active', 0)):
            self.game.sound.fadeout_music()
            self.game.sound.play_music('background', loops=-1)

            if self.is_ultimate_challenge_ready():
                # player needs to shoot the right popper to start the finale
                self.state = 'challenge_ready'
                self.game.remove_modes([self.multiball])
                self.mystery_lit = False
            elif self.game.getPlayerState('chain_complete', False):
                self.state = 'chain_complete'
            else:
                # player needs to shoot the right popper to start the next chain mode
                self.state = 'chain_ready'

        self.game.update_lamps()

    # starts a mode if a mode is available
    # the 300ms delay must be the same or longer than the popperR handler in CityBlock (handler inherited from CrimeSceneShots)
    # If that shot starts BlockWar multiball, we want the CityBlock to go first and change the state to busy
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

    def city_blocks_completed(self):
        self.setup_next_mode()

    def chain_mode_completed(self):
        self.setup_next_mode()

    #
    # Multiball
    #

    def multiball_starting(self):
        # Make sure no other multiball was already active before preparing for multiball.
        # The caller must update multiball_active in the player state AFTER calling this callback.
        if not self.game.getPlayerState('multiball_active', 0):
            self.state = 'busy'
            self.game.sound.fadeout_music()
            self.game.sound.play_music('multiball', loops=-1)
            self.game.remove_modes([self.missile_award_mode])
            # Light mystery once for free.
            self.mystery_lit = True
            self.game.update_lamps()

    def multiball_ended(self):
        # The caller must update multiball_active in the player state BEFORE calling this callback.
        if not self.game.getPlayerState('multiball_active', 0):
            self.game.modes.add(self.missile_award_mode)
        self.setup_next_mode()

    #
    # Ultimate Challenge
    #

    def is_ultimate_challenge_ready(self):
        # 3 Criteria for finale
        return (self.game.getPlayerState('multiball_jackpot_collected', False) and
                self.game.getPlayerState('blocks_complete', False) and
                self.game.getPlayerState('chain_complete', False))

    def start_ultimate_challenge(self):
        self.game.remove_modes([self.chain, self.city_blocks, self.multiball, self])
        self.reset_modes()
        self.game.base_play.start_ultimate_challenge()
        # ultimate challenge updated the lamps

    #
    # Captive balls
    #

    def sw_captiveBall1_active(self, sw):
        self.game.sound.play('meltdown')

    def sw_captiveBall2_active(self, sw):
        self.game.sound.play('meltdown')

    def sw_captiveBall3_active(self, sw):
        self.game.sound.play('meltdown')
        self.game.base_play.inc_bonus_x()
        self.mystery_lit = True
        self.game.update_lamps()

    #
    # Mystery
    #

    def sw_mystery_active(self, sw):
        self.game.sound.play('mystery')
        if self.mystery_lit:
            self.mystery_lit = False
            self.game.update_lamps()
            if self.game.getPlayerState('multiball_active', 0):
                if self.game.ball_save.timer > 0:
                    self.game.set_status('+10 second ball saver')
                    self.game.ball_save.add(10)
                else:
                    self.game.set_status('save ' + self.game.num_balls_requested() + ' balls')
                    self.game.ball_save_start(time=10, now=True, allow_multiple_saves=True)

            elif self.game.getPlayerState('chain_active', 0):
                self.chain.mode.add_time(10)
                self.game.set_status('Adding 10 seconds')
            else:
                self.game.ball_save_start(time=10, now=True, allow_multiple_saves=True)
                self.game.set_status('10 second ball saver')
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
