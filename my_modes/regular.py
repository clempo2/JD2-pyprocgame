from procgame.game import AdvancedMode
from chain import Chain
from blocks import CityBlocks
from multiball import Multiball
from missile import MissileAwardMode

class RegularPlay(AdvancedMode):
    """Controls all play except ultimate challenge"""

    def __init__(self, game, priority):
        super(RegularPlay, self).__init__(game, priority)

        self.chain = Chain(self.game, priority)

        self.city_blocks = CityBlocks(game, priority + 1)
        self.city_blocks.start_multiball_callback = self.multiball_starting
        self.city_blocks.end_multiball_callback = self.multiball_ended

        self.multiball = Multiball(self.game, priority + 1)
        self.multiball.start_callback = self.multiball_starting
        self.multiball.end_callback = self.multiball_ended

        self.missile_award_mode = MissileAwardMode(game, priority + 10)

    def reset(self):
        self.city_blocks.reset()

    def evt_player_added(self, player):
        player.setState('mystery_lit', False)

    def reset_progress(self):
        # Erase all progress to start over when ultimate challenge ends
        for mode in [self.chain, self.city_blocks, self.multiball]:
            mode.reset_progress()

    def mode_started(self):
        self.mystery_lit = self.game.getPlayerState('mystery_lit')
        self.state = 'init'
        self.game.modes.add([self.chain, self.city_blocks, self.multiball, self.missile_award_mode])
        self.setup_next_mode()

    def mode_stopped(self):
        self.game.modes.remove([self.chain, self.city_blocks, self.multiball, self.missile_award_mode])
        self.game.setPlayerState('mystery_lit', self.mystery_lit)

    #### Debugging tool:
    ####   push the buy in button to light ultimate challenge, shoot right popper to start it.
    ####   Each subsequent push marks a dark judge mode as completed
    ####   and therefore that dark judge mode will be skipped when ultimate challenge starts
    def sw_buyIn_active(self, sw):
        if self.is_ultimate_challenge_ready():
            if self.game.getPlayerState('challenge_mode') < 4:
                self.game.adjPlayerState('challenge_mode', 1)
        else:
            self.game.modes.remove([self.chain, self.city_blocks])
            self.game.setPlayerState('multiball_jackpot_collected', True)
            self.game.setPlayerState('current_block', self.game.blocks_required)
            self.game.setPlayerState('blocks_complete', True)
            self.game.setPlayerState('chain_complete', True)
            self.game.setPlayerState('modes_remaining', [])
            self.chain.mode = None
            self.game.modes.add([self.chain, self.city_blocks])
            self.game.update_lamps()
            self.setup_next_mode()

    def event_ball_started(self):
        ball_save_time = self.game.user_settings['Gameplay']['New ball ballsave time']
        repeating_ball_save = self.game.user_settings['Gameplay']['New ball repeating ballsave']
        self.game.ball_save_start(time=ball_save_time, now=True, allow_multiple_saves=repeating_ball_save)
        self.game.update_lamps()

    def sw_shooterR_inactive_for_300ms(self, sw):
        self.game.sound.play('ball_launch')
        self.game.base_play.play_animation('bikeacrosscity', frame_time=5)

    #
    # submodes
    #

    # called right after a mode has ended to decide the next state
    # the rule is: multiball can be stacked with a running mode, you cannot start a new mode during multiball
    def setup_next_mode(self):
        # a mode could still be running if modes were stacked, in that case do nothing and stay 'busy'
        if not (self.game.getPlayerState('multiball_active') or self.game.getPlayerState('chain_active')):
            self.game.sound.fadeout_music()
            self.game.base_play.play_background_music()

            if self.is_ultimate_challenge_ready():
                # player needs to shoot the right popper to start the finale
                self.state = 'challenge_ready'
                self.game.modes.remove([self.multiball])
                self.mystery_lit = False
            elif self.game.getPlayerState('chain_complete'):
                self.state = 'chain_complete'
            else:
                # player needs to shoot the right popper to start the next chain mode
                self.state = 'chain_ready'

        self.game.update_lamps()

    # starts a mode if a mode is available
    # the 310ms delay must be the same or longer than the popperR handler in CityBlock (handler inherited from CrimeSceneShots)
    # If that shot starts BlockWar multiball, we want the CityBlock to go first and change the state to busy
    # so we don't start something else here
    def sw_popperR_active_for_310ms(self, sw):
        if self.state == 'chain_ready':
            self.state = 'busy'
            self.chain.start_chain_mode()
        elif self.state == 'challenge_ready':
            self.state = 'busy'
            self.start_ultimate_challenge()
        else: # state 'busy' or 'chain_complete'
            self.game.base_play.flash_then_pop('flashersRtRamp', 'popperR')

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
        if not self.game.getPlayerState('multiball_active'):
            self.state = 'busy'
            self.game.sound.fadeout_music()
            self.game.sound.play_music('multiball', loops=-1)
            self.game.modes.remove([self.missile_award_mode])
            # Light mystery once for free.
            self.mystery_lit = True
            self.game.update_lamps()

    def multiball_ended(self):
        # The caller must update multiball_active in the player state BEFORE calling this callback.
        if not self.game.getPlayerState('multiball_active'):
            self.game.modes.add(self.missile_award_mode)
        self.setup_next_mode()

    #
    # Ultimate Challenge
    #

    def is_ultimate_challenge_ready(self):
        # 3 Criteria for finale
        return (self.game.getPlayerState('multiball_jackpot_collected') and
                self.game.getPlayerState('blocks_complete') and
                self.game.getPlayerState('chain_complete'))

    def start_ultimate_challenge(self):
        self.game.modes.remove([self.chain, self.city_blocks, self.multiball, self])
        self.reset_progress()
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
            mystery_ball_save_time = self.game.user_settings['Gameplay']['Mystery ballsave time']

            if self.game.getPlayerState('multiball_active'):
                if self.game.ball_save.timer > 0:
                    self.game.set_status('+' + str(mystery_ball_save_time) + 'SEC BALL SAVER')
                    self.game.ball_save.add(mystery_ball_save_time)
                else:
                    self.game.set_status(str(mystery_ball_save_time) + 'SEC BALL SAVER')
                    self.game.ball_save_start(time=mystery_ball_save_time, now=True, allow_multiple_saves=True)

            elif self.game.getPlayerState('chain_active'):
                mystery_feature_add_time = self.game.user_settings['Gameplay']['Mystery feature add time']
                self.game.set_status('+' + str(mystery_feature_add_time) + 'SEC TIMER')
                self.chain.mode.add_time(10)
            else:
                self.game.set_status(str(mystery_ball_save_time) + 'SEC BALL SAVER')
                self.game.ball_save_start(time=mystery_ball_save_time, now=True, allow_multiple_saves=True)
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
