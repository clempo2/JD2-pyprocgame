from random import shuffle
from procgame.dmd import FrameLayer, GroupedLayer, MarkupFrameGenerator, PanningLayer, PushTransition, ScriptedLayer, TextLayer
from procgame.game import Mode
from procgame.highscore import generate_highscore_frames

class FastPanningLayer(PanningLayer):
    """Pans faster than the regular PanningLayer"""
    def next_frame(self):
        self.tick += 2
        return super(FastPanningLayer, self).next_frame()


class Attract(Mode):
    """Attract mode and start buttons"""

    def __init__(self, game):
        super(Attract, self).__init__(game, 1)
        self.lampshow_keys = ['attract0', 'attract1']

        font_jazz18 = self.game.fonts['jazz18']

        self.gun_layer = self.game.animations['gun_powerup']

        self.jd_layer = TextLayer(128/2, 7, font_jazz18, 'center', opaque=True).set_text('Judge Dredd')
        self.jd_layer.transition = PushTransition(direction='south')

        self.cityscape_layer = self.game.animations['cityscape']

        self.proc_splash_layer = self.game.animations['Splash']
        self.proc_splash_layer.transition = PushTransition(direction='south')

        self.press_yellow_layer = self.button_layer('Press Yellow Button', 'for Regulation Play', direction='west')
        self.press_yellow_layer2 = self.button_layer('Press Yellow Button', 'for Regulation Play', blink_frame=5)
        self.press_green_layer = self.button_layer('Press Green Button', 'for SuperGame', direction='west')
        self.press_green_layer2 = self.button_layer('Press Green Button', 'for SuperGame', blink_frame=5)

        self.high_scores_title_layer = TextLayer(128/2, 7, font_jazz18, 'center', opaque=True).set_text('High Scores')
        self.high_scores_title_layer.transition = PushTransition(direction='north')
        self.game_over_layer = TextLayer(128/2, 7, font_jazz18, 'center', opaque=True).set_text('Game Over')

        gen = MarkupFrameGenerator()
        credits_frame = gen.frame_for_markup("""


#CREDITS#

[Rules:]
[Gerry Stellenberg]

[Software:]
[Adam Preble]
[Clement Pellerin]

[Sound and Music:]
[Rob Keller]
[Jonathan Coultan]

[Dots:]
[Travis Highrise]

[Special Thanks to:]
[Steven Duchac]
[Rob Anthony]

[www.multimorphic.com]
[pyprocgame.pindev.org]
""")

        self.credits_layer = FastPanningLayer(width=128, height=32, frame=credits_frame, origin=(0, 0), translate=(0, 1), bounce=False)
        self.judges_layer = self.game.animations['darkjudges']
        self.longwalk_layer = self.game.animations['longwalk']

        instruct_frame = MarkupFrameGenerator().frame_for_markup("""


#INSTRUCTIONS#

Start chain features
by shooting
Build Up Chain Feature
when lit

Instructions are displayed
when starting each feature

Secure blocks by shooting
lit crime scene shots

Complete JUDGE targets
to light locks

During multiball,
Left ramp lights jackpot
shoot subway to collect

To light Ultimate Challenge:
Start all chain features
Secure all blocks
Collect a multiball jackpot
""")

        self.instruct_layer = PanningLayer(width=128, height=32, frame=instruct_frame, origin=(0,0), translate=(0,1), bounce=False)

    def mode_started(self):
        self.delay(name='ball_search', event_type=None, delay=1, handler=self.ball_search)

        # Blink the start buttons in alternation to notify player about starting a game.
        self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
        self.game.lamps.superGame.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)

        # Turn on minimal GI lamps
        self.game.enable_gi(False)
        self.game.lamps.gi01.enable()

        self.change_lampshow()
        self.display()

    def mode_stopped(self):
        # Stop deadworld ball search (if active) before we eject the first ball
        # otherwise deadworld might not see the trough was momentarily full
        # I wish there was a trough full event for this.
        self.game.deadworld.stop_ball_search()

        self.game.lamps.startButton.enable()
        self.game.lamps.superGame.enable()
        self.game.lampctrl.stop_show()

    def ball_search(self):
        if not self.game.trough.is_full():
            self.game.ball_search.perform_search(5)
            self.game.deadworld.perform_ball_search()
            #self.game.set_status('Ball Missing')

    def display(self):
        self.game.score_display.update_layer()

        script = [
            {'seconds':3.0, 'layer':self.gun_layer},
            {'seconds':3.0, 'layer':self.jd_layer},
            {'seconds':2.5, 'layer':self.game.score_display.layer},
            {'seconds':4.0, 'layer':self.cityscape_layer},
            {'seconds':0.75, 'layer':self.press_yellow_layer},
            {'seconds':2.0, 'layer':self.press_yellow_layer2},
            {'seconds':0.75, 'layer':self.press_green_layer},
            {'seconds':2.0, 'layer':self.press_green_layer2},
            {'seconds':2.5, 'layer':self.game.score_display.layer},
            {'seconds':3.0, 'layer':self.proc_splash_layer},
            {'seconds':7.0, 'layer':self.credits_layer},
            {'seconds':2.5, 'layer':self.game.score_display.layer},
            {'seconds':3.0, 'layer':self.judges_layer},
        ]

        self.append_high_score_layers(script)
        self.reset_script(script)
        self.layer = ScriptedLayer(width=128, height=32, script=script)
        self.layer.on_complete = lambda: self.reset_script(script)

    def game_over_display(self):
        self.game.score_display.update_layer()

        script = [
            {'seconds':3.4, 'layer':self.longwalk_layer}, # stop this anim early, Game Over font does not fit rest of the game
            {'seconds':3.0, 'layer':self.game_over_layer},
            {'seconds':4.0, 'layer':self.game.score_display.layer},
        ]

        self.append_high_score_layers(script)
        self.reset_script(script)
        self.layer = ScriptedLayer(width=128, height=32, script=script)
        self.layer.on_complete = self.display

    def instruction_display(self):
        script = [{'seconds':20.1, 'layer':self.instruct_layer}]
        self.reset_script(script)
        self.layer = ScriptedLayer(width=128, height=32, script=script)
        self.layer.on_complete = self.display

    def button_layer(self, button_text, play_text, blink_frame=None, direction=None):
        font_07x5 = self.game.fonts['07x5']
        press_layer = TextLayer(128/2, 8, font_07x5, 'center', opaque=True).set_text(button_text, seconds=None, blink_frames=blink_frame)
        play_layer = TextLayer(128/2, 17, font_07x5, 'center', opaque=False).set_text(play_text, seconds=None, blink_frames=blink_frame)
        start_layer = GroupedLayer(128, 32, [press_layer, play_layer])
        if direction:
            start_layer.transition = PushTransition(direction=direction)
        return start_layer

    def append_high_score_layers(self, script):
        script.append({'seconds':2.0, 'layer':self.high_scores_title_layer})
        for frame in generate_highscore_frames(self.game.all_highscore_categories):
            new_layer = FrameLayer(frame=frame)
            script.append({'seconds':1.25, 'layer':new_layer})

    def reset_script(self, script):
        for script_item in script:
            script_item['layer'].reset()

    def change_lampshow(self):
        shuffle(self.lampshow_keys)
        self.game.lampctrl.play_show(self.lampshow_keys[0], repeat=True)
        self.delay(name='lampshow', event_type=None, delay=10, handler=self.change_lampshow)

    def sw_fireL_active(self, sw):
        self.game.sound.play_voice('attract')
        self.layer.force_next(forward=False)

    def sw_fireR_active(self, sw):
        self.game.sound.play_voice('attract')
        self.layer.force_next(forward=True)

    def sw_flipperLwL_active(self, sw):
        self.instruction_display()

    def sw_flipperLwR_active(self, sw):
        self.instruction_display()

    # Eject any balls that get stuck before returning to the trough.
    def sw_popperL_active_for_500ms(self, sw):
        self.game.coils.popperL.pulse(40)

    def sw_popperR_active_for_500ms(self, sw):
        self.game.coils.popperR.pulse(40)

    def sw_shooterL_active_for_500ms(self, sw):
        self.game.coils.shooterL.pulse(40)

    def sw_shooterR_active_for_500ms(self, sw):
        self.game.coils.shooterR.pulse(40)
