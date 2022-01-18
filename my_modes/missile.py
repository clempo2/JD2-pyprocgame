from random import randint
from procgame.dmd import GroupedLayer, TextLayer
from timer import ModeTimer
from videomode import ShootingGallery

class MissileAwardMode(ModeTimer):
    """Choose an award while the only ball sits in the left shooter lane"""

    def __init__(self, game, priority):
        super(MissileAwardMode, self).__init__(game, priority)
        self.timer_delay = 0.2

        self.video_mode_setting = self.game.user_settings['Gameplay']['Video mode'] != 'off'
        if self.video_mode_setting:
            self.video_mode = ShootingGallery(self.game, priority + 11, self.video_mode_setting)
            self.video_mode.on_complete = self.video_mode_complete

        self.initial_awards = ['Secure one Block', 'Light Extra Ball', '30000 Points', 'Bonus +1X', 'Hold Bonus X']
        self.repeatable_award = [True, False, True, True, False]
        self.current_award_ptr = 0

        font = self.game.fonts['tiny7']
        self.title_layer = TextLayer(128/2, 7, font, 'center')
        self.title_layer.set_text('Missile Award')

        self.element_layer = TextLayer(128/2, 15, font, 'center')
        self.element_layer.set_text('Left Fire btn collects:')

        self.value_layer = TextLayer(128/2, 22, font, 'center')
        self.selection_layer = GroupedLayer(128, 32, [self.title_layer, self.element_layer, self.value_layer])

    def mode_started(self):
        player = self.game.current_player()
        self.missile_award_lit = player.getState('missile_award_lit', False)
        self.available_awards = player.getState('available_awards', self.initial_awards[:])

    def mode_stopped(self):
        player = self.game.current_player()
        player.setState('missile_award_lit', self.missile_award_lit)
        player.setState('available_awards', self.available_awards)

    # must be called when the missile award mode is stopped
    def reset(self):
        self.game.setPlayerState('missile_award_lit', False)

    def light_missile_award(self):
        self.missile_award_lit = True
        self.game.update_lamps()

    def evt_shooterL_active_500ms(self):
        if self.missile_award_lit:
            self.missile_award_lit = False
            self.start_missile_award()
            # abort the event to capture the ball
            return True
        else:
            self.missile_award_lit = True
            # base handler will kick back the ball
            return False

    def sw_fireL_active(self, sw):
        if self.timer > 3:
            self.reset_timer(3, self.timer_delay)
        elif self.timer == 0:
            self.launch_ball()

    def start_missile_award(self):
        self.game.sound.stop_music()
        self.game.base_play.regular_play.chain.pause()
        # first award is video mode (if enabled in the settings)
        # but keep video mode for later if another mode is running
        # this way we don't pause the running mode for too long
        video_mode_lit = self.game.getPlayerState('video_mode_lit', self.video_mode_setting)
        if video_mode_lit and not self.game.base_play.regular_play.chain.is_active():
            self.game.setPlayerState('video_mode_lit', False)
            self.game.modes.add(self.video_mode)
        else:
            self.start_selection()

    def end_missile_award(self):
        self.game.sound.play_music('background', loops=-1)
        self.game.base_play.regular_play.chain.resume()

    def video_mode_complete(self, success):
        self.game.modes.remove(self.video_mode)
        self.launch_ball()
        if success:
            self.game.base_play.light_extra_ball()
        self.end_missile_award()

    def start_selection(self):
        blocks_complete = self.game.getPlayerState('blocks_complete', False)
        self.available_awards[0] = '50000 Points' if blocks_complete else 'Secure One Block'
        self.rotate_awards()
        self.layer = self.selection_layer
        self.start_timer(70, self.timer_delay)

    def timer_update(self, time):
        if time == 3:
            self.launch_ball()
            self.award()
        elif time > 10:
            self.rotate_awards()

    def expired(self):
        self.layer = None
        
    def rotate_awards(self):
        self.current_award_ptr = (self.current_award_ptr + randint(1, 4)) % len(self.available_awards)
        self.value_layer.set_text(self.available_awards[self.current_award_ptr])

    def award(self):
        award = self.available_awards[self.current_award_ptr]
        if award.endswith('Points'):
            award_words = award.rsplit(' ')
            self.game.score(int(award_words[0]))
            self.game.base_play.show_on_display(award)
        elif award == 'Light Extra Ball':
            self.game.base_play.light_extra_ball()
        elif award == 'Secure One Block':
            self.game.base_play.regular_play.crime_scenes.crime_scene_levels.level_complete()
        elif award == 'Bonus +1X':
            self.game.base_play.inc_bonus_x()
        elif award == 'Hold Bonus X':
            self.game.base_play.hold_bonus_x()

        if not self.repeatable_award[self.current_award_ptr]:
            self.available_awards[self.current_award_ptr] = str(10000*(self.current_award_ptr + 1)) + ' Points'
            
        self.end_missile_award()

    def update_lamps(self):
        style = 'medium' if self.missile_award_lit else 'off'
        self.game.drive_lamp('airRaid', style)

    def launch_ball(self):
        self.game.coils.shooterL.pulse(randint(15, 30))