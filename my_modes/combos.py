from procgame.game import Mode

class Combos(Mode):
    """Award combos for repeated loop shots"""

    def mode_started(self):
        self.outer_loop_active = False
        self.inner_loop_active = False
        self.inner_loop_combos = 0
        self.outer_loop_combos = 0

    def sw_topRightOpto_active(self, sw):
        # See if ball came around inner left loop
        if self.game.switches.topCenterRollover.time_since_change() < 1.5:
            self.inner_loop_active = True
            self.game.sound.play('inner_loop')
            self.inner_loop_combos += 1
            if self.inner_loop_combos > self.game.getPlayerState('best_inner_loops', 0):
                self.game.setPlayerState('best_inner_loops', self.inner_loop_combos)
            points = 10000 * self.inner_loop_combos
            self.game.score(points)
            self.game.base_play.display('inner loop: ' + str(self.inner_loop_combos), points)
            self.game.base_play.play_animation('bike_across_screen', frame_time=3)
            self.game.update_lamps()
            self.cancel_delayed('inner_loop')
            self.delay(name='inner_loop', event_type=None, delay=3.0, handler=self.inner_loop_combo_expired)

    def sw_leftRollover_active(self, sw):
        # See if ball came around right loop
        if self.game.switches.topRightOpto.time_since_change() < 1:
            self.outer_loop_active = True
            self.game.sound.play('outer_loop')
            self.outer_loop_combos += 1
            if self.outer_loop_combos > self.game.getPlayerState('best_outer_loops', 0):
                self.game.getPlayerState('best_outer_loops', self.outer_loop_combos)
            points = 5000 * self.outer_loop_combos
            self.game.score(points)
            self.game.base_play.display('outer loop: ' + str(self.outer_loop_combos), points)
            self.game.base_play.play_animation('bike_across_screen', frame_time=3)
            self.game.update_lamps()
            self.cancel_delayed('outer_loop')
            self.delay(name='outer_loop', event_type=None, delay=3.0, handler=self.outer_loop_combo_expired)

    def inner_loop_combo_expired(self):
        self.inner_loop_combos = 0
        self.inner_loop_active = False
        self.game.update_lamps()

    def outer_loop_combo_expired(self):
        self.outer_loop_combos = 0
        self.outer_loop_active = False
        self.game.update_lamps()

    def update_lamps(self):
        if self.inner_loop_active:
            self.game.drive_perp_lamp('perp2', 'medium')

        if self.outer_loop_active:
            self.game.drive_perp_lamp('perp4', 'medium')
