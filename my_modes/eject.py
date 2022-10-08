from procgame.game import AdvancedMode

class CoilEjectMode(AdvancedMode):
    # Eject any balls that get stuck before returning to the trough.
    def sw_popperL_active_for_300ms(self, sw):
        self.game.coils.popperL.pulse()

    def sw_popperR_active_for_300ms(self, sw):
        self.game.coils.popperR.pulse()

    def sw_shooterL_active_for_300ms(self, sw):
        self.game.coils.shooterL.pulse()

    def sw_shooterR_active_for_300ms(self, sw):
        self.game.coils.shooterR.pulse()
