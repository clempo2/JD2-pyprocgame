import locale
from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode

class SkillShot(Mode):
    """Skillshot when the ball starts"""

    def __init__(self, game, priority):
        super(SkillShot, self).__init__(game, priority)
        self.text_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], 'center')
        self.award_layer = TextLayer(128/2, 17, self.game.fonts['num_14x10'], 'center')
        self.layer = GroupedLayer(128, 32, [self.text_layer, self.award_layer])

    def mode_started(self):
        self.shots_hit = 0
        self.update_lamps()

    def begin(self):
        self.delay(name='skill_shot_delay', event_type=None, delay=7.0, handler=self.skill_shot_expired)
        self.update_lamps()

    def update_lamps(self):
        for lamp_name in ['perm4W', 'perp4R', 'perp4Y', 'perp4G']:
            self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

    def award(self):
        self.game.sound.stop('good shot')
        self.game.sound.play('good shot')
        self.shots_hit += 1
        score = self.shots_hit * 5000
        self.game.score(score)
        self.text_layer.set_text('Skill Shot!', 3)
        self.award_layer.set_text(locale.format('%d', score, True), 3)
        self.cancel_delayed('skill_shot_delay')
        self.delay(name='skill_shot_delay', event_type=None, delay=3.0, handler=self.skill_shot_expired)
        self.update_lamps()

    def skill_shot_expired(self):
        # timer expired or external caller cancels the skillshot (for example after a ball save)
        self.cancel_delayed('skill_shot_delay')
        for lamp_name in ['perm4W', 'perp4R', 'perp4Y', 'perp4G']:
            self.game.lamps[lamp_name].disable()
        self.game.modes.remove(self)

    def sw_leftRollover_active(self, sw):
        # See if ball came around right loop
        if self.game.switches.topRightOpto.time_since_change() < 1:
            self.award()
