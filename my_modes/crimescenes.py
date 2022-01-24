from procgame.game import Mode

class CrimeSceneShots(Mode):
    """Base class for modes using the crime scene shots"""

    def __init__(self, game, priority, *args, **kwargs):
        super(CrimeSceneShots, self).__init__(game, priority)
        self.lamp_colors = ['G', 'Y', 'R', 'W']

    def sw_topRightOpto_active(self, sw):
        if self.game.switches.leftRollover.time_since_change() < 1:
            # ball came around outer left loop
            self.switch_hit(0)
        elif self.game.switches.topCenterRollover.time_since_change() < 1.5:
            # ball came around inner left loop
            self.switch_hit(1)

    def sw_popperR_active_for_300ms(self, sw):
        self.switch_hit(2)

    def sw_leftRollover_active(self, sw):
        if self.game.switches.topRightOpto.time_since_change() < 1.5:
            # ball came around right loop
            self.switch_hit(3)

    def sw_topCenterRollover_active(self, sw):
        if self.game.switches.topRightOpto.time_since_change() < 2:
            # ball came around right loop, we allow up to 2 seconds as ball trickles this way
            self.switch_hit(3)

    def sw_rightRampExit_active(self, sw):
        self.switch_hit(4)

    def switch_hit(self, shot):
        pass
