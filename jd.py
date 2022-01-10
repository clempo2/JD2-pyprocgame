import locale
import os
import pinproc
import pygame.locals
from procgame.config import value_for_key_path
from procgame.dmd import FrameLayer, MarkupFrameGenerator, ScriptedLayer
from procgame.game import BasicGame, Mode, Player
from procgame.highscore import CategoryLogic, EntrySequenceManager, HighScoreCategory
from procgame.lamps import LampController
from procgame.modes import BallSave, BallSearch, Trough
from procgame.service import ServiceMode
from procgame.sound import SoundController
from asset_loader import AssetLoader
from my_modes.switchmonitor import SwitchMonitor
from my_modes.attract import Attract
from my_modes.base import BasePlay
from my_modes.deadworld import Deadworld, DeadworldTest

import logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

locale.setlocale(locale.LC_ALL, '') # Used to put commas in the score.

curr_file_path = os.path.dirname(os.path.abspath(__file__))
settings_path = curr_file_path + '/config/settings.yaml'
game_data_path = curr_file_path + '/config/game_data.yaml'
game_data_template_path = curr_file_path + '/config/game_data_template.yaml'
settings_template_path = curr_file_path + '/config/settings_template.yaml'

# Workaround to deal with latency of flipper rule programming.
# Need to make sure flippers deativate when the flipper buttons are
# released.  The flipper rules will automatically activate the flippers
# if the buttons are held while the enable ruler is programmed, but
# if the buttons are released immediately after that, the deactivation
# would be missed without this workaround.
class FlipperWorkaroundMode(Mode):
    """Workaround to deal with latency of flipper rule programming"""
    def __init__(self, game):
        super(FlipperWorkaroundMode, self).__init__(game, 2)
        self.flipper_enable_workaround_active = False

    def enable_flippers(self, enable=True):
        if enable:
            self.flipper_enable_workaround_active = True
            self.delay(name='flipper_workaround', event_type=None, delay=0.1, handler=self.end_flipper_workaround)

    def end_flipper_workaround(self):
        self.flipper_enable_workaround_active = False

    #def sw_flipperLwL_active(self, sw):
    #    if self.flipper_enable_workaround_active:
    #        self.game.coils['flipperLwLMain'].pulse(34)
    #        self.game.coils['flipperLwLHold'].pulse(0)

    def sw_flipperLwL_inactive(self, sw):
        if self.flipper_enable_workaround_active:
            self.game.coils['flipperLwLMain'].disable()
            self.game.coils['flipperLwLHold'].disable()

    #def sw_flipperLwR_active(self, sw):
    #    if self.flipper_enable_workaround_active:
    #        self.game.coils['flipperLwRMain'].pulse(34)
    #        self.game.coils['flipperLwRHold'].pulse(0)

    def sw_flipperLwR_inactive(self, sw):
        if self.flipper_enable_workaround_active:
            self.game.coils['flipperLwRMain'].disable()
            self.game.coils['flipperLwRHold'].disable()

    #def sw_flipperUpL_active(self, sw):
    #    if self.flipper_enable_workaround_active:
    #        self.game.coils['flipperUpLMain'].pulse(34)
    #        self.game.coils['flipperUpLHold'].pulse(0)

    def sw_flipperUpL_inactive(self, sw):
        if self.flipper_enable_workaround_active:
            self.game.coils['flipperUpLMain'].disable()
            self.game.coils['flipperUpLHold'].disable()

    #def sw_flipperUpR_active(self, sw):
    #    if self.flipper_enable_workaround_active:
    #        self.game.coils['flipperUpRMain'].pulse(34)
    #        self.game.coils['flipperUpRHold'].pulse(0)

    def sw_flipperUpR_inactive(self, sw):
        if self.flipper_enable_workaround_active:
            self.game.coils['flipperUpRMain'].disable()
            self.game.coils['flipperUpRHold'].disable()

class JDServiceMode(ServiceMode):

    def mode_stopped(self):
        super(JDServiceMode, self).mode_stopped()
        self.game.service_mode_ended()


class JDPlayer(Player):
    """Keeps the progress of one player to allow the player
       to resume where he left off in a multi-player game"""

    def __init__(self, name):
        super(JDPlayer, self).__init__(name)
        self.state_tracking = {}

    def setState(self, key, val):
        self.state_tracking[key] = val

    def getState(self, key, default=None):
        return self.state_tracking.get(key, default)


class JDGame(BasicGame):
    """Judge Dredd pinball game"""

    def __init__(self):
        super(JDGame, self).__init__(pinproc.MachineTypeWPC)
        self.sound = SoundController(self)
        self.lampctrl = LampController(self)
        self.logging_enabled = False

        self.load_config('config/JD.yaml')

        # Assets
        asset_loader = AssetLoader(self)
        asset_loader.load_assets(curr_file_path)
        self.animations = asset_loader.animations
        self.fonts = asset_loader.fonts

        self.reset()

    # override load_config to allow pygame key names and pygame numeric keys in the key_map
    def load_config(self, path):
        # Ignore pylint warning on next line, we by-pass immediate superclass intentionally
        super(BasicGame, self).load_config(path)

        # Setup the key mappings from the config.yaml.
        # We used to do this in __init__, but at that time the
        # configuration isn't loaded so we can't peek into self.switches.
        key_map_config = value_for_key_path(keypath='keyboard_switch_map', default={})
        if self.desktop:
            for k, v in key_map_config.items():
                switch_name = str(v)
                if self.switches.has_key(switch_name):
                    switch_number = self.switches[switch_name].number
                else:
                    switch_number = pinproc.decode(self.machine_type, switch_name)
                if type(k) == str:
                    if k.startswith('K_'): # key is a pygame key name
                        key = getattr(pygame.locals, k)
                    else: # key is character
                        key = ord(k)
                elif type(k) == int:
                    if k < 10:
                        key = ord(str(k)) # digit character
                    else:
                        key = k # numbers used as bindings for specials -- for example K_LSHIFT is 304
                else:
                    raise ValueError('invalid key name in config file: ' + str(k))
                self.desktop.add_key_map(key, switch_number)

    def reset(self):
        # Reset the entire game framework
        super(JDGame, self).reset()

        self.load_settings_and_stats()

        # Service mode
        self.switch_monitor = SwitchMonitor(game=self)
        deadworld_test = DeadworldTest(self, 200, self.fonts['tiny7'])
        self.service_mode = JDServiceMode(self, 100, self.fonts['tiny7'], [deadworld_test])

        # Currently there are no special ball search handlers.  The deadworld
        # could be one, but running it while balls are locked would screw up
        # the multiball logic.  There is already logic in the multiball
        # to eject balls that enter the deadworld when lock isn't lit; so it
        # shouldn't be necessary to search the deadworld.  (unless a ball jumps
        # onto the ring rather than entering through the feeder.)
        self.ball_search = BallSearch(self, priority=100, countdown_time=10,
                     coils=self.ballsearch_coils, reset_switches=self.ballsearch_resetSwitches,
                     stop_switches=self.ballsearch_stopSwitches, special_handler_modes=[])
        self.ball_search.disable()
        
        # Trough
        trough_switchnames = ['trough1', 'trough2', 'trough3', 'trough4', 'trough5', 'trough6']
        early_save_switchnames = ['outlaneR', 'outlaneL']
        self.ball_save = BallSave(self, self.lamps.drainShield, 'shooterR')
        self.ball_save.disable()
        self.trough = Trough(self, trough_switchnames, 'trough6', 'trough', early_save_switchnames, 'shooterR', self.no_op_callback)
        self.trough.ball_save_callback = self.ball_save.launch_callback
        self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
        self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

        # Instantiate basic game features
        self.attract_mode = Attract(self)
        self.base_play = BasePlay(self)
        self.flipper_workaround_mode = FlipperWorkaroundMode(self)
        self.deadworld = Deadworld(self, 20, self.settings['Machine']['Deadworld mod installed'])

        self.shooting_again = False

        # Add the basic modes to the mode queue
        self.add_modes([self.switch_monitor, self.attract_mode, self.ball_search,
                        self.deadworld, self.ball_save, self.trough, self.flipper_workaround_mode])

        # Make sure flippers are off, especially for user initiated resets.
        self.enable_flippers(enable=False)

    def add_modes(self, mode_list):
        for mode in mode_list:
            self.modes.add(mode)

    def remove_modes(self, mode_list):
        for m in mode_list:
            self.modes.remove(m)

    def remove_all_modes(self):
        for m in self.modes[:]:
            self.modes.remove(m)

    def send_event(self, event):
        for mode in self.modes[:]:
            handler = getattr(mode, event, None)
            if handler:
                ret = handler()
                if ret:
                    # skip lower priority modes
                    return ret

    def load_settings_and_stats(self):
        self.load_settings(settings_template_path, settings_path)
        self.sound.music_volume_offset = self.user_settings['Machine']['Music volume offset']
        self.sound.set_volume(self.user_settings['Machine']['Initial volume'])

        self.load_game_data(game_data_template_path, game_data_path)

        self.balls_per_game = self.user_settings['Gameplay']['Balls per game']
        self.score_display.set_left_players_justify(self.user_settings['Display']['Left side score justify'])

        # High Score stuff
        classic_category = HighScoreCategory()
        classic_category.game_data_key = 'ClassicHighScoreData'

        crimeScenes_category = self.create_high_score_category('CrimeScenesHighScoreData', 'Crime Scene Champ', 'crime_scenes_total_levels', ' level')
        innerLoops_category = self.create_high_score_category('InnerLoopsHighScoreData', 'Inner Loop Champ', 'best_inner_loops', ' loop')
        outerLoops_category = self.create_high_score_category('OuterLoopsHighScoreData', 'Outer Loop Champ', 'best_outer_loops', ' loop')

        self.highscore_categories = [classic_category, crimeScenes_category, innerLoops_category, outerLoops_category]
        for category in self.highscore_categories:
            category.load_from_game(self)

        supergame_category = HighScoreCategory()
        supergame_category.game_data_key = 'SuperGameHighScoreData'
        supergame_category.titles = ['SuperGame Champion', 'SuperGame High Score #1', 'SuperGame High Score #2', 'SuperGame High Score #3', 'SuperGame High Score #4']
        supergame_category.load_from_game(self)
        
        self.supergame_highscore_categories = [supergame_category, crimeScenes_category, innerLoops_category, outerLoops_category]
        
        self.all_highscore_categories = [classic_category, supergame_category, crimeScenes_category, innerLoops_category, outerLoops_category]

    # this variant is called by procgame.service.SettingsEditor
    def save_settings(self):
        self.save_settings(settings_path)

    def create_high_score_category(self, key, title, state_key, suffix):
        category = HighScoreCategory()
        category.game_data_key = key
        category.titles = [title]
        category.score_for_player = lambda player: player.getState(state_key, 0)
        category.score_suffix_singular = suffix
        category.score_suffix_plural = suffix + 's'
        return category

    def start_service_mode(self):
        """ remove all existing modes that are running
            stop music, stop lamp shows, disable flippers
            then add the service mode.
        """

        self.remove_all_modes()

        self.lampctrl.stop_show()
        for lamp in self.lamps:
            lamp.disable()

        self.sound.stop_music()
        self.enable_flippers(False)
        self.modes.add(self.service_mode)

    def service_mode_ended(self):
        self.reset()
        self.update_lamps()

    def volume_down(self):
        volume = self.sound.volume_down()
        self.set_status('Volume Down : ' + str(volume))

    def volume_up(self):
        volume = self.sound.volume_up()
        self.set_status('Volume Up : ' + str(volume))

    def create_player(self, name):
        return JDPlayer(name)

    def request_additional_player(self):
        """ attempt to add an additional player, but honor the max number of players """
        if len(self.players) < 4:
            player = self.add_player()
            self.set_status(player.name + ' added!')
        else:
            self.logger.info('Cannot add more than 4 players.')

    def getPlayerState(self, key, default=None):
        player = self.current_player()
        return player.getState(key, default)

    def setPlayerState(self, key, val):
        player = self.current_player()
        player.setState(key, val)

    def start_game(self, supergame):
        super(JDGame, self).start_game()
        self.game_data['Audits']['Games Started'] += 1
        self.supergame = supergame
        self.modes.remove(self.attract_mode)
        self.update_lamps()

        # Add the first player
        self.add_player()
        # Start the ball.  This includes ejecting a ball from the trough.
        self.start_ball()

    def ball_starting(self):
        super(JDGame, self).ball_starting()
        self.modes.add(self.base_play)
        self.update_lamps()

    # Override to create a flag signaling extra ball.
    def shoot_again(self):
        super(JDGame, self).shoot_again()
        self.shooting_again = True

    def end_ball(self):
        self.shooting_again = False
        super(JDGame, self).end_ball()

        self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
        self.game_data['Audits']['Balls Played'] += 1

    def ball_ended(self):
        self.modes.remove(self.base_play)
        self.trough.drain_callback = self.no_op_callback

    def game_ended(self):
        super(JDGame, self).game_ended()
        self.deadworld.mode_stopped()

        # High Score Stuff
        seq_manager = EntrySequenceManager(game=self, priority=2)
        seq_manager.finished_handler = self.highscore_entry_finished
        categories = self.supergame_highscore_categories if self.supergame else self.highscore_categories
        seq_manager.logic = CategoryLogic(game=self, categories=categories)
        seq_manager.ready_handler = self.highscore_entry_ready_to_prompt
        self.modes.add(seq_manager)

    def tilt_warning(self, times_warned):
        self.sound.play('tilt warning')
        self.set_status('Warning')

    def slam_tilted(self):
        self.sound.fadeout_music()
        self.sound.play('slam_tilt')
        self.set_status('SLAM TILT')
        self.remove_all_modes()
        self.reset()
        self.update_lamps()

    def tilted(self):
        self.sound.fadeout_music()
        self.sound.play('tilt')
        self.set_status('TILT')

        # Kick balls out of places it could be stuck.
        if self.switches.shooterR.is_active():
            self.coils.shooterR.pulse(50)
        if self.switches.shooterL.is_active():
            self.coils.shooterL.pulse(20)

    def highscore_entry_ready_to_prompt(self, mode, prompt):
        self.sound.play_voice('high score')
        banner_mode = Mode(game=self, priority=8)
        markup = MarkupFrameGenerator()
        tiny7 = self.fonts['tiny7']
        markup.font_plain = tiny7
        markup.font_bold = tiny7
        text = '\n[GREAT JOB]\n#%s#\n' % (prompt.left.upper()) # we know that the left is the player name
        frame = markup.frame_for_markup(markup=text, y_offset=0)
        banner_mode.layer = ScriptedLayer(width=128, height=32, script=[{'seconds':4.0, 'layer':FrameLayer(frame=frame)}])
        banner_mode.layer.on_complete = lambda: self.highscore_banner_complete(banner_mode=banner_mode, highscore_entry_mode=mode)
        self.modes.add(banner_mode)

    def highscore_banner_complete(self, banner_mode, highscore_entry_mode):
        self.modes.remove(banner_mode)
        self.update_lamps()
        highscore_entry_mode.prompt()

    def highscore_entry_finished(self, mode):
        self.modes.remove(mode)
        self.attract_mode.game_over_display()
        self.modes.add(self.attract_mode)
        self.update_lamps()

        # Handle game stats.
        for i in range(0, len(self.players)):
            game_time = self.get_game_time(i)
            self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
            self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
            self.game_data['Audits']['Games Played'] += 1

        self.save_game_data(game_data_path)

    def set_status(self, text):
        self.dmd.set_message(text, 3)

    def perform_ball_search(self):
        self.set_status('Ball Search!')
        self.ball_search.perform_search(5)
        if self.deadworld.num_balls_locked > 0:
            self.deadworld.perform_ball_search()

    # Empty callback
    # Calling self.game.trough.launch_balls() with a None callback preserves the previous callback
    # to erase the callback completely, you have to pass an empty callback instead
    def no_op_callback(self):
        pass

    def enable_flippers(self, enable=True):
        super(JDGame, self).enable_flippers(enable)
        self.flipper_workaround_mode.enable_flippers(enable)

    def drive_lamp(self, lamp_name, style='on'):
        if style == 'slow':
            self.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
        elif style == 'medium':
            self.lamps[lamp_name].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
        elif style == 'fast':
            self.lamps[lamp_name].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
        elif style == 'on':
            self.lamps[lamp_name].enable()
        elif style == 'off':
            self.lamps[lamp_name].disable()

    def drive_perp_lamp(self, perp_name, style='on'):
        for color in ['W', 'R', 'Y', 'G']:
            lamp_name = perp_name + color
            self.drive_lamp(lamp_name, style)

    def disable_drop_lamps(self):
        self.lamps.dropTargetJ.disable()
        self.lamps.dropTargetU.disable()
        self.lamps.dropTargetD.disable()
        self.lamps.dropTargetG.disable()
        self.lamps.dropTargetE.disable()

    def enable_gi(self, on):
        for gi in ['gi01', 'gi02', 'gi03', 'gi04', 'gi05']:
            if on:
                self.lamps[gi].enable()
            else:
                self.lamps[gi].disable()

    def calc_time_average_string(self, prev_total, prev_x, new_value):
        prev_time_list = prev_x.split(':')
        prev_time = (int(prev_time_list[0]) * 60) + int(prev_time_list[1])
        avg_game_time = int((int(prev_total) * int(prev_time)) + int(new_value)) / (int(prev_total) + 1)
        avg_game_time_min = avg_game_time/60
        avg_game_time_sec = str(avg_game_time%60)
        if len(avg_game_time_sec) == 1:
            avg_game_time_sec = '0' + avg_game_time_sec

        return_str = str(avg_game_time_min) + ':' + avg_game_time_sec
        return return_str

    def calc_number_average(self, prev_total, prev_x, new_value):
        avg_game_time = int((prev_total * prev_x) + new_value) / (prev_total + 1)
        return int(avg_game_time)

def main():
    game = None
    try:
        game = JDGame()
        game.run_loop()
    finally:
        del game

if __name__ == '__main__':
    main()
