from random import shuffle
from procgame.dmd import FrameLayer, MarkupFrameGenerator, PanningLayer, PushTransition, ScriptedLayer, TextLayer
from procgame.game import Mode
from procgame.highscore import generate_highscore_frames

class FastPanningLayer(PanningLayer):
    """Pans faster than the regular PanningLayer"""
    def __init__(self, width, height, frame, origin, translate, bounce=True):
        super(FastPanningLayer, self).__init__(width, height, frame, origin, translate, bounce)

    def next_frame(self):
        self.tick += 2
        return super(FastPanningLayer, self).next_frame()


class Attract(Mode):
    """Attract mode and start buttons"""

    def __init__(self, game):
        super(Attract, self).__init__(game, 1)
        self.lampshow_keys = ['attract0', 'attract1']

        self.cityscape_layer = self.game.animations['cityscape']
        self.jd_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=True).set_text('Judge Dredd')
        self.jd_layer.transition = PushTransition(direction='south')
        self.proc_splash_layer = self.game.animations['Splash']
        self.proc_splash_layer.transition = PushTransition(direction='south')
        self.pyprocgame_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=True).set_text('pyprocgame')
        self.pyprocgame_layer.transition = PushTransition(direction='west')
        self.press_start_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=True).set_text('Press Start', seconds=None, blink_frames=1)
        self.scores_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=True).set_text('High Scores')
        self.scores_layer.transition = PushTransition(direction='north')
        self.game_over_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=True).set_text('Game Over')

        gen = MarkupFrameGenerator()
        credits_frame = gen.frame_for_markup("""


#CREDITS#

[Rules:]
[Gerry Stellenberg]

[Tools and Framework:]
[Adam Preble]

[Software:]
[Clement Pellerin]

[Sound and Music:]
[Rob Keller]
[Jonathan Coultan]

[Dots:]
[Travis Highrise]

[P.ROC:]
[www.multimorphic.com]

[pyprocgame:]
[pyprocgame.pindev.org]

[Special thanks to:]
[Rob Anthony]
""")

        self.credits_layer = FastPanningLayer(width=128, height=32, frame=credits_frame, origin=(0, 0), translate=(0, 1), bounce=False)
        self.guntech_layer = self.game.animations['guntech']
        self.judges_layer = self.game.animations['darkjudges_no_bg']
        self.longwalk_layer = self.game.animations['longwalk']

    def mode_started(self):
        if self.game.deadworld.num_balls_locked > 0:
            self.game.deadworld.eject_balls(self.game.deadworld.num_balls_locked)

        # Blink the start buttons in alternation to notify player about starting a game.
        self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
        self.game.lamps.superGame.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)

        # Turn on minimal GI lamps
        self.game.enable_gi(False)
        self.game.lamps.gi01.enable()

        # Release the ball from places it could be stuck.
        for name in ['popperL', 'popperR', 'shooterL', 'shooterR']:
            if self.game.switches[name].is_active():
                self.game.coils[name].pulse()

        self.change_lampshow()
        self.display()

    def mode_stopped(self):
        self.game.lamps.startButton.enable()
        self.game.lamps.superGame.enable()
        self.cancel_delayed(name='lampshow')
        self.game.lampctrl.stop_show()

    def display(self):
        self.game.score_display.update_layer()
        script = [
            {'seconds':3.0, 'layer':self.jd_layer},
            {'seconds':4.0, 'layer':self.cityscape_layer},
            {'seconds':3.0, 'layer':self.proc_splash_layer},
            {'seconds':3.0, 'layer':self.pyprocgame_layer},
            {'seconds':3.0, 'layer':self.press_start_layer},
            {'seconds':3.0, 'layer':self.game.score_display.layer},
            {'seconds':7.2, 'layer':self.credits_layer},
            {'seconds':3.0, 'layer':self.judges_layer},
            {'seconds':3.0, 'layer':self.scores_layer}
        ]

        self.append_high_score_layers(script)
        self.layer = ScriptedLayer(width=128, height=32, script=script)

    def game_over_display(self):
        self.game.score_display.update_layer()
        script = [
            {'seconds':6.0, 'layer':self.longwalk_layer},
            {'seconds':3.0, 'layer':self.game_over_layer},
            {'seconds':3.0, 'layer':self.game.score_display.layer},
            {'seconds':3.0, 'layer':self.scores_layer}
        ]

        self.append_high_score_layers(script)
        self.layer = ScriptedLayer(width=128, height=32, script=script)
        self.layer.on_complete = self.display

    def append_high_score_layers(self, script):
        for frame in generate_highscore_frames(self.game.highscore_categories):
            new_layer = FrameLayer(frame=frame)
            new_layer.transition = PushTransition(direction='north')
            script.append({'seconds':2.0, 'layer':new_layer})

    def change_lampshow(self):
        shuffle(self.lampshow_keys)
        self.game.lampctrl.play_show(self.lampshow_keys[0], repeat=True)
        self.delay(name='lampshow', event_type=None, delay=10, handler=self.change_lampshow)

    def sw_fireL_active(self, sw):
        self.game.sound.play_voice('attract')

    def sw_fireR_active(self, sw):
        self.game.sound.play_voice('attract')

    def sw_flipperLwL_active(self, sw):
        self.layer.force_next(False)

    def sw_flipperLwR_active(self, sw):
        self.layer.force_next(True)

    # Eject any balls that get stuck before returning to the trough.
    def sw_popperL_active_for_500ms(self, sw): # opto!
        self.game.coils.popperL.pulse(40)

    def sw_popperR_active_for_500ms(self, sw): # opto!
        self.game.coils.popperR.pulse(40)

    def sw_shooterL_active_for_500ms(self, sw):
        self.game.coils.shooterL.pulse(40)

    def sw_shooterR_active_for_500ms(self, sw):
        self.game.coils.shooterR.pulse(40)
