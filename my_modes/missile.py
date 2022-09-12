from random import randint
from procgame.dmd import GroupedLayer, TextLayer
from timer import Timer
from videomode import ShootingGallery

class MissileAwardMode(Timer):
    """Choose an award while the only ball sits in the left shooter lane"""

    def __init__(self, game, priority):
        super(MissileAwardMode, self).__init__(game, priority)
        self.timer_delay = 0.2

        self.video_mode = ShootingGallery(self.game, priority + 11)
        self.video_mode.on_complete = self.video_mode_complete

        self.initial_awards = ['Secure One Block', 'Light Extra Ball', '30,000 Points', 'Bonus +1X', 'Hold Bonus X']
        self.repeatable_award = [True, False, True, True, False]
        self.current_award_ptr = 0

        font = self.game.fonts['tiny']
        self.title_layer = TextLayer(128/2, 7, font, 'center').set_text('Missile Award')
        self.value_layer = TextLayer(128/2, 15, font, 'center')
        self.selection_layer = GroupedLayer(128, 32, [self.title_layer, self.value_layer], opaque=True, fill_color=(0,0,0,255))

    def evt_player_added(self, player):
        player.setState('missile_award_lit', False)
        player.setState('available_awards', self.initial_awards[:])

        video_mode_setting = self.game.user_settings['Gameplay']['Video mode']
        player.setState('video_mode_lit', video_mode_setting != 'off')

    def mode_started(self):
        player = self.game.current_player()
        self.missile_award_lit = player.getState('missile_award_lit')
        self.available_awards = player.getState('available_awards')

    def mode_stopped(self):
        player = self.game.current_player()
        player.setState('missile_award_lit', self.missile_award_lit)
        player.setState('available_awards', self.available_awards)
        self.layer = None # in case the ball is lost before timer expires

    def light_missile_award(self):
        self.missile_award_lit = True
        self.game.update_lamps()

    def event_shooterL_active_500ms(self):
        starting = self.missile_award_lit
        self.missile_award_lit = not self.missile_award_lit
        self.game.update_lamps()

        if starting:
            self.start_missile_award()
            # abort the event to capture the ball
            return True
        else:
            # base handler will kick back the ball
            return False

    def sw_fireL_active(self, sw):
        if self.timer > 15:
            self.reset_timer(15, self.timer_delay)
        elif self.timer == 0 and self.game.switches.shooterL.is_active():
            # the ball would be ejected by BasePlay anyway, but this removes the small sub-second delay
            self.eject_ball()

    def start_missile_award(self):
        self.game.sound.stop_music()
        self.game.base_play.regular_play.chain.pause()
        # first award is video mode (if enabled in the settings)
        # but keep video mode for later if another mode is running
        # this way we don't pause the running mode for too long
        # and the player won't forget what he was doing
        if self.game.getPlayerState('video_mode_lit') and not self.game.getPlayerState('chain_active'):
            self.game.setPlayerState('video_mode_lit', False)
            self.game.modes.add(self.video_mode)
        else:
            self.start_selection()

    def end_missile_award(self):
        self.game.base_play.play_background_music()
        self.game.base_play.regular_play.chain.resume()

    def video_mode_complete(self, success):
        self.game.remove_modes([self.video_mode])
        self.eject_ball()
        if success:
            self.game.base_play.light_extra_ball()
        self.end_missile_award()

    def start_selection(self):
        blocks_complete = self.game.getPlayerState('blocks_complete')
        self.available_awards[0] = '50,000 Points' if blocks_complete else 'Secure One Block'
        self.rotate_awards()
        self.layer = self.selection_layer
        self.start_timer(70, self.timer_delay)

    def timer_update(self, time):
        if time > 15:
            self.rotate_awards()
        elif time == 15:
            # that gives 3 seconds to read the chosen selection
            self.give_award()
            self.eject_ball()

    def expired(self):
        self.layer = None

    def rotate_awards(self):
        self.current_award_ptr = (self.current_award_ptr + randint(1, 4)) % len(self.available_awards)
        self.value_layer.set_text(self.available_awards[self.current_award_ptr])

    def give_award(self):
        award = self.available_awards[self.current_award_ptr]

        if award.endswith('Points'):
            award_words = award.rsplit(' ')
            points = award_words[0].replace(',', '')
            self.game.score(int(points))
        elif award == 'Light Extra Ball':
            self.game.base_play.light_extra_ball()
        elif award == 'Secure One Block':
            self.game.base_play.regular_play.city_blocks.city_block.block_complete()
        elif award == 'Bonus +1X':
            self.game.base_play.inc_bonus_x()
        elif award == 'Hold Bonus X':
            self.game.base_play.hold_bonus_x()

        if not self.repeatable_award[self.current_award_ptr]:
            self.available_awards[self.current_award_ptr] = self.game.format_points(10000*(self.current_award_ptr + 1)) + ' Points'

        self.end_missile_award()

    def update_lamps(self):
        style = 'medium' if self.missile_award_lit else 'off'
        self.game.drive_lamp('airRaid', style)

    def eject_ball(self):
        pulse_min = self.game.user_settings['Coil Strength']['ShooterL Min']
        pulse_max = self.game.user_settings['Coil Strength']['ShooterL Max']
        self.game.coils.shooterL.pulse(randint(pulse_min, pulse_max))
