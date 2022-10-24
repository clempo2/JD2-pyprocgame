from procgame.game import AdvancedMode

class Combos(AdvancedMode):
    """Award combos for repeated loop shots, the skill shot is an outer loop combo"""

    def __init__(self, game, priority):
        super(Combos, self).__init__(game, priority, AdvancedMode.Ball)

    def evt_player_added(self, player):
        player.setState('best_outer_loops', 0)
        player.setState('best_inner_loops', 0)

    def mode_started(self):
        self.skill_shot_active = False
        self.outer_loop_active = False
        self.inner_loop_active = False
        self.outer_loop_combos = 0
        self.inner_loop_combos = 0

    def skill_shot_begin(self):
        self.skill_shot_active = True
        self.cancel_delayed('outer_loop')
        self.delay(name='outer_loop', event_type=None, delay=7.0, handler=self.outer_loop_combo_expired)
        self.game.update_lamps()

    def sw_leftRollover_active(self, sw):
        # See if ball came around right loop
        if self.game.switches.topRightOpto.time_since_change() < 1:
            self.outer_loop_active = True
            self.outer_loop_combos += 1
            if self.outer_loop_combos > self.game.getPlayerState('best_outer_loops'):
                self.game.setPlayerState('best_outer_loops', self.outer_loop_combos)

            if self.skill_shot_active:
                sound = 'good shot'
                skill_points = 10000
                text = 'Skill Shot: '
            else:
                sound = 'outer_loop'
                skill_points = 0
                text = 'outer loop: '
                self.game.base_play.play_animation('bike_across_screen')

            self.game.sound.stop(sound)
            self.game.sound.play(sound)
            points = skill_points + 5000 * self.outer_loop_combos
            self.game.score(points)
            self.game.base_play.display(text + str(self.outer_loop_combos), points)
            self.game.update_lamps()
            self.cancel_delayed('outer_loop')
            self.delay(name='outer_loop', event_type=None, delay=3.0, handler=self.outer_loop_combo_expired)

    def sw_topRightOpto_active(self, sw):
        # See if ball came around inner left loop
        if self.game.switches.topCenterRollover.time_since_change() < 1.5:
            self.inner_loop_active = True
            self.game.sound.play('inner_loop')
            self.inner_loop_combos += 1
            if self.inner_loop_combos > self.game.getPlayerState('best_inner_loops'):
                self.game.setPlayerState('best_inner_loops', self.inner_loop_combos)
            points = 5000 * self.inner_loop_combos
            self.game.score(points)
            self.game.base_play.display('inner loop: ' + str(self.inner_loop_combos), points)
            self.game.base_play.play_animation('bike_across_screen')
            self.game.update_lamps()
            self.cancel_delayed('inner_loop')
            self.delay(name='inner_loop', event_type=None, delay=3.0, handler=self.inner_loop_combo_expired)

    def skill_shot_expired(self):
        # cancel the skill shot before the timer expires, for example when a ball is saved
        if self.skill_shot_active:
            self.cancel_delayed('outer_loop')
            self.outer_loop_combo_expired()

    def outer_loop_combo_expired(self):
        self.skill_shot_active = False
        self.outer_loop_active = False
        self.outer_loop_combos = 0
        self.game.update_lamps()

    def inner_loop_combo_expired(self):
        self.inner_loop_active = False
        self.inner_loop_combos = 0
        self.game.update_lamps()

    def update_lamps(self):
        if self.skill_shot_active:
            self.game.drive_perp_lamp('perp4', 'slow')
        elif self.outer_loop_active:
            self.game.drive_perp_lamp('perp4', 'medium')

        if self.inner_loop_active:
            self.game.drive_perp_lamp('perp2', 'medium')
