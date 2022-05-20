from procgame.game import Mode
from chain import Chain
from blocks import CityBlocks
from multiball import Multiball
from missile import MissileAwardMode

class RegularPlay(Mode):
    """Controls all play except ultimate challenge"""

    def __init__(self, game, priority):
        super(RegularPlay, self).__init__(game, priority)
        self.ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
        self.repeating_ball_save = self.game.user_settings['Gameplay']['New ball repeating ballsave']
        self.mystery_ball_save_time = self.game.user_settings['Gameplay']['Mystery ballsave time']
        self.mystery_feature_add_time = self.game.user_settings['Gameplay']['Mystery feature add time']

        self.chain = Chain(self.game, priority)

        self.city_blocks = CityBlocks(game, priority + 1)
        self.city_blocks.start_multiball_callback = self.multiball_starting
        self.city_blocks.end_multiball_callback = self.multiball_ended

        self.multiball = Multiball(self.game, priority + 1)
        self.multiball.start_callback = self.multiball_starting
        self.multiball.end_callback = self.multiball_ended

        self.missile_award_mode = MissileAwardMode(game, priority + 10)

    def reset(self):
        for mode in [self.chain, self.city_blocks, self.multiball, self.missile_award_mode]:
            mode.reset()

        # reset RegularPlay itself
        self.mystery_lit = False

    def mode_started(self):
        self.mystery_lit = self.game.getPlayerState('mystery_lit', False)
        self.state = 'init'
        self.game.add_modes([self.chain, self.city_blocks, self.multiball, self.missile_award_mode])
        self.setup_next_mode()

        # welcome player at start of ball but not when continuing after ultimate challenge
        if self.game.base_play.ball_starting:
            self.welcome()

    def mode_stopped(self):
        self.game.remove_modes([self.chain, self.city_blocks, self.multiball, self.missile_award_mode])
        self.game.setPlayerState('mystery_lit', self.mystery_lit)

    #### DEBUG: push the buy in button to go straight to ultimate challenge from regular mode
    ####        press multiple times in a row to skip Dark Judge modes
    def sw_buyIn_active(self, sw):
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

    #
    # Message
    #

    def welcome(self):
        if self.game.shooting_again:
            self.game.sound.play_voice('shoot again ' + str(self.game.current_player_index + 1))
            self.game.base_play.display('Shoot Again')
        elif self.game.ball == 1:
            self.game.sound.play_voice('welcome')

        # high score mention
        if self.game.ball == self.game.balls_per_game:
            if self.game.shooting_again:
                # display the score to beat after the Shoot Again message
                self.delay('high_score_mention', event_type=None, delay=3, handler=self.high_score_mention)
            else:
                self.high_score_mention()

    def high_score_mention(self):
        if self.game.base_play.replay.replay_achieved[0]:
            text = 'High Score'
            game_data_key = 'SuperGameHighScoreData' if self.game.supergame else 'ClassicHighScoreData'
            score = self.game.game_data[game_data_key][0]['score']
        else:
            text = 'Replay'
            score = self.game.base_play.replay.replay_scores[0]
        self.game.base_play.display(text, score)

    def evt_ball_started(self):
        # remove welcome message early if the player was very quick to plunge
        self.game.base_play.display('')
        self.cancel_delayed('high_score_mention')

        self.game.ball_save_start(time=self.ball_save_time, now=True, allow_multiple_saves=self.repeating_ball_save)
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
            self.game.base_play.play_background_music()

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
        self.reset()
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
                    self.game.set_status('+' + str(self.mystery_ball_save_time) + 'SEC BALL SAVER')
                    self.game.ball_save.add(self.mystery_ball_save_time)
                else:
                    self.game.set_status(str(self.mystery_ball_save_time) + 'SEC BALL SAVER')
                    self.game.ball_save_start(time=self.mystery_ball_save_time, now=True, allow_multiple_saves=True)

            elif self.game.getPlayerState('chain_active', 0):
                self.game.set_status('+' + str(self.mystery_feature_add_time) + 'SEC TIMER')
                self.chain.mode.add_time(10)
            else:
                self.game.set_status(str(self.mystery_ball_save_time) + 'SEC BALL SAVER')
                self.game.ball_save_start(time=self.mystery_ball_save_time, now=True, allow_multiple_saves=True)
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
