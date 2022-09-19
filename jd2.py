from collections import OrderedDict
import logging
from math import ceil
import os
import pygame.locals
import pinproc
import yaml
from procgame.config import value_for_key_path
from procgame.dmd import font_named, FrameLayer
from procgame.game import BasicGame, SkeletonGame
from procgame.game.skeletongame import run_proc_game
from procgame.highscore import HighScoreCategory, get_highscore_data
from procgame.modes.service import ServiceMode
from layers import DontMoveTransition, FixedSizeTextLayer, GroupedTransition, SlideTransition
from my_modes.attract import Attract
from my_modes.ballsearch import JDBallSearch
from my_modes.base import Base
from my_modes.baseplay import BasePlay
from my_modes.deadworld import Deadworld, DeadworldTest
from my_modes.initials import JDEntrySequenceManager
from my_modes.switchmonitor import JDSwitchMonitor

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

curr_file_path = os.path.dirname(os.path.abspath(__file__))


class JD2Game(SkeletonGame):
    """Judge Dredd pinball game"""

    # rename the settings sections used by the framework back to simpler section names
    settings_sections = {
        'Machine': 'Machine',
        'Coils': 'Coil Strength',
        'Sound': 'Sound',
        'Gameplay': 'Gameplay',
        'Replay': 'Replay'
    }

    def __init__(self):
        super(JD2Game, self).__init__('config/JD.yaml', curr_file_path)

        self.reset_pending = False
        self.lamp_schedules = {'slow':0x00ff00ff, 'medium':0x0f0f0f0f, 'fast':0x55555555, 'on':0xffffffff, 'off':0x00000000}
        self.flashers = [x for x in self.coils if x.name.startswith('flasher')]

        # shorten Blackout animation by removing last few frames
        self.animations['blackout'].frames = self.animations['blackout'].frames[:-2]

        # a text layer for status messages, same size and location as the status line at the bottom of the score display
        self.dmd.message_layer = self.create_message_layer()

        # Create basic modes
        self.base = Base(self, 1)
        self.attract_mode = Attract(self, 2)
        self.base_play = BasePlay(self, 3)
        self.deadworld = Deadworld(self, 20)
        deadworld_test = DeadworldTest(self, 200, self.fonts['settings-font-small'])
        self.service_mode = ServiceMode(self, 99, self.fonts['settings-font-small'], extra_tests=[deadworld_test])

        self.reset()

    # TODO
    # override load_config to allow pygame key names and pygame numeric keys in the key_map
    def load_config(self, path):
        # Ignore pylint warning on next line, we by-pass immediate superclass intentionally
        super(BasicGame, self).load_config(path)

        # Setup the key mappings from config.yaml.
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
                        #TODO, that does not work with SDL2
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
        super(JD2Game, self).reset()

        # read settings
        num_blocks_setting = int(self.user_settings['Gameplay']['Blocks for Ultimate Challenge'])
        self.blocks_required = min(16, 4 * ceil(num_blocks_setting / 4)) # a multiple of 4 less than or equal to 16
        self.deadworld_mod_installed = self.user_settings['Machine']['Deadworld Mod Installed']

        self.base_play.reset()
        self.start_attract_mode()

    def tick(self):
        super(JD2Game, self).tick()
        # it is safer to call reset here than within a mode called by the run loop 
        if self.reset_pending:
            self.reset_pending = False
            self.sound.fadeout_music()
            self.sound.stop_all()
            self.reset()

    def load_settings_and_stats(self):
        super(JD2Game, self).load_settings_and_stats()
        self.create_high_score_categories()
        for category in self.all_highscore_categories:
            category.load_from_game(self)

    def create_switch_monitor(self):
        return JDSwitchMonitor(self)

    def create_ball_search(self):
        # Currently there are no special ball search handlers.  The deadworld
        # could be one, but running it while balls are locked would screw up
        # the multiball logic.  There is already logic in the multiball
        # to eject balls that enter the deadworld when lock isn't lit; so it
        # shouldn't be necessary to search the deadworld.  (unless a ball jumps
        # onto the ring rather than entering through the feeder.)

        return JDBallSearch(self, priority=100, \
                         countdown_time=self.ballsearch_time, coils=self.ballsearch_coils, \
                         reset_switches=self.ballsearch_resetSwitches, \
                         stop_switches=self.ballsearch_stopSwitches, \
                         special_handler_modes=[])

    # Empty callback
    def no_op_callback(self):
        pass

    #
    # Layers
    #
    
    def create_message_layer(self):
        """return a text layer at the bottom of the screen where the last line of the score display normally goes"""
        layer = FixedSizeTextLayer(128/2, 32-6, font_named('Font07x5.dmd'), 'center', width=128, height=6, fill_color=(0,0,0,255))

        # slide in for 0.5s, stay still for 2s, slide out for 0.5s
        slide_in_transition = SlideTransition(direction='west')
        dont_move_transition = DontMoveTransition()
        dont_move_transition.progress_per_frame = 1.0 / 120.0
        slide_out_transition = SlideTransition(direction='west')
        slide_out_transition.in_out = 'out'

        layer.grouped_transition = GroupedTransition([slide_in_transition, dont_move_transition, slide_out_transition])
        layer.grouped_transition.completed_handler = self.message_transition_completed
        return layer

    def set_status(self, text=None, scroll=True):
        # when text is None, that effectively turns off the layer and transitions are not called
        if scroll:
            # text slides in, stays for a while and then slides out
            self.dmd.message_layer.set_text(text)
            self.dmd.message_layer.transition = self.dmd.message_layer.grouped_transition
            self.dmd.message_layer.transition.start()
        else:
            # text does not move
            self.dmd.message_layer.set_text(text, seconds=3)
            self.dmd.message_layer.transition = None

    def message_transition_completed(self):
        self.dmd.message_layer.set_text(None)

    #
    # Game
    #
    def game_started(self):
        self.supergame = self.switchmonitor.superGame_button_pressed
        super(JD2Game, self).game_started()

    def ball_save_start(self, time, now, allow_multiple_saves):
        # We assume the number of balls to save is the number of balls requested by the game,
        # so launch the balls and/or eject from the planet if applicable before calling this method.
        #
        # The framework consider the 2sec grace period is included in the ball save time
        # as evidenced by the Drain Shield lamp turning off 2sec before the timer expires.
        # This is apparent when looking at the countdown timer of a timed mode and looks like a bug.
        # By adding 2sec, we move the grace period after the ball save time,
        # and the Drain Shield light will now turn off at the time given.
        # That's the real definition of a grace period in my book.

        if time > 0:
            self.ball_save.start(self.num_balls_requested(), 2 + time, now, allow_multiple_saves)

    def num_balls_requested(self):
        # Return what the game considers is the number of balls in play.
        # This includes the balls that are already in play plus those pending to be launched
        # less the ones to be launched that replace balls already on the playfield (now locked or in outlane)
        # It does not count locked balls but it does count balls pending to be ejected from the planet.
        # That's because the planet immediately adds the balls to be ejected to the count of balls in play
        # without waiting for the crane to release them.
        return self.trough.num_balls_in_play + self.trough.num_balls_to_launch - self.trough.num_balls_to_stealth_launch

    def launch_balls(self, balls_to_launch):
        # launch balls from the trough if it has sufficient balls, else eject additional balls from Deadworld
        # NOTE: self.trough.num_balls() is not reliable when balls are moving in the trough, don't use it here.
        new_num_requested = self.num_balls_requested() + balls_to_launch
        num_unlocked = self.num_balls_total - self.deadworld.num_balls_locked
        if new_num_requested > num_unlocked:
            num_to_eject = new_num_requested - num_unlocked
            self.deadworld.eject_balls(num_to_eject)
            balls_to_launch -= num_to_eject
        if balls_to_launch:
            # warning: must pass a real callback since passing None preserves the previous callback
            self.trough.launch_balls(balls_to_launch, self.no_op_callback)

    def disable_ball_search(self):
        #TODO
        # workaround for a bug in pyprocgame's BallSearch.disable
        self.ball_search.disable()
        self.ball_search.cancel_delayed(['ball_search_countdown', 'ball_search_coil1'])

    def slam_tilt_complete(self):
        self.b_slam_tilted = False
        self.game_tilted = False
        self.reset()

    #
    # Modes
    #

    def add_modes(self, mode_list):
        for mode in mode_list:
            self.modes.add(mode)

    def remove_modes(self, mode_list):
        for mode in mode_list:
            self.modes.remove(mode)
            # cancel all delayed handlers
            mode._Mode__delayed = []

    def send_event(self, event):
        for mode in self.modes[:]:
            handler = getattr(mode, event, None)
            if handler:
                ret = handler()
                if ret:
                    # skip lower priority modes
                    return ret

    #
    # High Scores
    #

    def create_high_score_categories(self):
        blocks_category = self.create_high_score_category('BlocksHighScores', 'Block Champ', 'num_blocks', ' block')
        inner_loops_category = self.create_high_score_category('InnerLoopsHighScores', 'Inner Loop Champ', 'best_inner_loops', ' loop')
        outer_loops_category = self.create_high_score_category('OuterLoopsHighScores', 'Outer Loop Champ', 'best_outer_loops', ' loop')

        supergame_category = HighScoreCategory()
        supergame_category.game_data_key = 'SuperGameHighScores'
        supergame_category.titles = ['SuperGame Champion', 'SuperGame High Score #1', 'SuperGame High Score #2', 'SuperGame High Score #3', 'SuperGame High Score #4']

        classic_category = self.highscore_categories[0]
        self.highscore_categories += [classic_category, blocks_category, inner_loops_category, outer_loops_category]
        self.supergame_highscore_categories = [supergame_category, blocks_category, inner_loops_category, outer_loops_category]
        self.all_highscore_categories = [classic_category, supergame_category, blocks_category, inner_loops_category, outer_loops_category]

    def create_high_score_category(self, key, title, state_key, suffix):
        category = HighScoreCategory()
        category.game_data_key = key
        category.titles = [title]
        category.score_for_player = lambda player: player.getState(state_key, 0)
        category.score_suffix_singular = suffix
        category.score_suffix_plural = suffix + 's'
        return category

    def create_entry_sequence_manager(self):
        categories = self.supergame_highscore_categories if self.supergame else self.highscore_categories
        return JDEntrySequenceManager(game=self, priority=2, categories=categories)

    def format_points(self, points):
        # disregard the locale, always insert commas between groups of 3 digits
        return '00' if points == 0 else '{:,}'.format(points)

    def get_highscore_data(self):
        # return data for both regulation play and supergame
        return get_highscore_data(self.all_highscore_categories)

    def generate_score_layer(self):
        frame = self.score_display.layer.next_frame()
        return FrameLayer(frame=frame.copy(), opaque=True)

    #
    # lamps
    #

    def drive_lamp(self, lamp_name, style='on'):
        lamp_schedule = self.lamp_schedules[style]
        self.lamps[lamp_name].schedule(schedule=lamp_schedule, cycle_seconds=0, now=True)

    def drive_perp_lamp(self, perp_name, style='on'):
        for color in ['W', 'R', 'Y', 'G']:
            lamp_name = perp_name + color
            self.drive_lamp(lamp_name, style)

    def enable_gi(self, on):
        for gi in ['gi01', 'gi02', 'gi03', 'gi04', 'gi05']:
            self.drive_lamp(gi, 'on' if on else 'off')

    def disable_drop_lamps(self):
        for lamp in ['dropTargetJ', 'dropTargetU', 'dropTargetD', 'dropTargetG', 'dropTargetE']:
            self.lamps[lamp].disable()

    def disable_all_lights(self):
        self.disableAllLamps()

        # Disable all flashers
        for flasher in self.flashers:
            flasher.disable()

if __name__ == '__main__':
    # preserve order when reading YAML files
    yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: OrderedDict(loader.construct_pairs(node)))
    yaml.add_representer(OrderedDict,
        lambda dumper, data: dumper.represent_dict(data.iteritems())) 

    # change T2Game to be the class defined in this file!
    run_proc_game(JD2Game)