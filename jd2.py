from math import ceil
import logging
import os
import pygame.locals
import pinproc
from procgame.config import value_for_key_path
from procgame.dmd import FrameLayer, MarkupFrameGenerator, ScriptedLayer, font_named
from procgame.game import BasicGame, Mode, SkeletonGame
from procgame.highscore import HighScoreCategory
from procgame.service import ServiceMode
from layers import DontMoveTransition, FixedSizeTextLayer, GroupedTransition, SlideTransition
from my_modes.attract import Attract
from my_modes.ballsearch import JDBallSearch
from my_modes.base import BasePlay
from my_modes.deadworld import Deadworld, DeadworldTest
from my_modes.drain import DrainMode
from my_modes.initials import JDEntrySequenceManager
from my_modes.switchmonitor import JDSwitchMonitor
from my_modes.tilt import SlamTilted, Tilted

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

curr_file_path = os.path.dirname(os.path.abspath(__file__))

class JDServiceMode(ServiceMode):

    def mode_stopped(self):
        super(JDServiceMode, self).mode_stopped()
        self.game.service_mode_ended()


class JD2Game(SkeletonGame):
    """Judge Dredd pinball game"""

    def __init__(self):
        super(JD2Game, self).__init__('config/JD.yaml', curr_file_path)

        # a text layer for status messages, same size and location as the status line at the bottom of the score display
        self.dmd.message_layer = self.create_message_layer()

        self.logging_enabled = False

        self.load_config('config/JD.yaml')
        self.lamp_schedules = {'slow':0x00ff00ff, 'medium':0x0f0f0f0f, 'fast':0x55555555, 'on':0xffffffff, 'off':0x00000000}
        self.create_high_score_categories()

        self.reset()

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
        # work-around for poor implementation of reset by the framework
        # this is important when the game is aborted with a long press to the startButton
        self.stop()

        # Reset the entire game framework
        super(JD2Game, self).reset()

        # reload the settings since they might have changed in service mode
        self.load_game_settings()
        self.load_game_stats()

        deadworld_test = DeadworldTest(self, 200, self.fonts['tiny'])
        self.service_mode = JDServiceMode(self, 100, self.fonts['tiny'], [deadworld_test])

        # Trough
        #TODO
        #trough_switchnames = ['trough1', 'trough2', 'trough3', 'trough4', 'trough5', 'trough6']
        #early_save_switchnames = ['outlaneL', 'outlaneR']
        #self.ball_save = BallSave(self, self.lamps.drainShield, 'shooterR')
        #self.ball_save.disable()
        #self.trough = Trough(self, trough_switchnames, 'trough6', 'trough', early_save_switchnames, 'shooterR', self.no_op_callback)
        #self.trough.ball_save_callback = self.ball_save.launch_callback
        #self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
        #elf.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

        self.shooting_again = False

        # Basic game features
        self.attract_mode = Attract(self, 1)
        self.drain_mode = DrainMode(self, 2)
        self.base_play = BasePlay(self, 3)
        self.deadworld = Deadworld(self, 20)
        self.tilted_mode = Tilted(self, 33000)

        #TODO self.add_modes([self.switch_monitor, self.ball_search, self.deadworld, self.ball_save, self.trough, self.attract_mode])
        self.modes.add(self.deadworld)

        # Make sure flippers are off, especially for user initiated resets.
        self.enable_flippers(enable=False)
        self.start_attract_mode()

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

    def stop(self):
        self.disable_game()
        self.remove_all_modes()

    # Empty callback
    def no_op_callback(self):
        pass

    #
    # Layers
    #
    
    def create_message_layer(self):
        """return a text layer at the bottom of the screen where the last line of the score display normally goes"""
        layer = FixedSizeTextLayer(128/2, 32-6, font_named('Font07x5.dmd'), 'center', opaque=False, width=128, height=6)

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

    def reset_script_layer(self, script):
        for script_item in script:
            script_item['layer'].reset()
            if script_item['layer'].transition:
                script_item['layer'].transition.start()

    #
    # Players
    #

    def request_additional_player(self):
        """ attempt to add an additional player, but honor the max number of players """
        if len(self.players) < 4:
            player = self.add_player()
            self.set_status(player.name.upper() + ' ADDED')
        else:
            self.logger.info('Cannot add more than 4 players.')

    #
    # Game
    #

    def start_game(self, supergame=False):
        self.supergame = supergame
        super(JD2Game, self).start_game()
        self.game_data['Audits']['Games Started'] += 1
        self.remove_modes([self.attract_mode])
        self.update_lamps()

        # Add the first player
        self.add_player()
        # Start the game modes, base_play will eject a ball from the trough
        self.start_ball()

    def ball_starting(self):
        super(JD2Game, self).ball_starting()
        self.add_modes([self.drain_mode, self.base_play])
        self.update_lamps()

    def ball_save_start(self, time, now, allow_multiple_saves):
        # We assume the number of balls to save is the number of balls requested by the game,
        # so launch the balls and/or eject from the planet if applicable before calling this method.
        #
        # Normally, the 2sec grace period is included in the ball save time
        # as evidenced by the Drain Shield lamp turning off 2sec before the timer expires.
        # This is apparent when looking at the countdown timer of a timed mode and looks like a bug.
        # By adding 2sec, we move the grace period after the ball save time,
        # and the Drain Shield light will now turn off at the time given.
        # That's the real definition of a grace period in my book.
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

    # Override to create a flag signaling extra ball.
    def shoot_again(self):
        self.shooting_again = True
        super(JD2Game, self).shoot_again()

    def end_ball(self):
        self.shooting_again = False
        super(JD2Game, self).end_ball()

        self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
        self.game_data['Audits']['Balls Played'] += 1

    def ball_ended(self):
        self.remove_modes([self.drain_mode, self.base_play, self.tilted_mode])

    def game_ended(self):
        super(JD2Game, self).game_ended()
        self.deadworld.stop_spinning()

        # High Score Stuff
        categories = self.supergame_highscore_categories if self.supergame else self.highscore_categories
        seq_manager = JDEntrySequenceManager(game=self, priority=2, categories=categories)
        seq_manager.finished_handler = self.highscore_entry_finished
        seq_manager.ready_handler = self.highscore_entry_ready_to_prompt
        self.modes.add(seq_manager)

    def disable_ball_search(self):
        # workaround for a bug in pyprocgame's BallSearch.disable
        self.ball_search.disable()
        self.ball_search.cancel_delayed(['ball_search_countdown', 'ball_search_coil1'])

    #
    # Modes
    #

    def add_modes(self, mode_list):
        for mode in mode_list:
            # TODO REMOVE THIS AND FIX ADDING MODES
            if mode.is_started():
                print 'Mode ' + str(mode) + ' is already active'
            else:
                self.modes.add(mode)

    def remove_modes(self, mode_list):
        for mode in mode_list:
            self.modes.remove(mode)
            # cancel all delayed handlers
            mode._Mode__delayed = []

    def remove_all_modes(self):
        self.remove_modes(self.modes[:])

    def send_event(self, event):
        for mode in self.modes[:]:
            handler = getattr(mode, event, None)
            if handler:
                ret = handler()
                if ret:
                    # skip lower priority modes
                    return ret

    #
    # Tilt
    #

    def tilt_warning(self, times_warned):
        self.sound.play('tilt warning')
        self.set_status('WARNING')

    def slam_tilted(self):
        self.stop()
        self.modes.add(SlamTilted(self, 33000))

    def tilted(self):
        self.disable_game()
        # remove all game play, drain_mode will continue to monitor ball drains
        self.remove_modes([self.base_play])
        self.modes.add(self.tilted_mode)

    def disable_game(self):
        # Make sure balls will drain and won't be saved
        self.enable_flippers(enable=False)
        if hasattr(self, 'ball_save'):
            self.ball_save.disable()
        self.disable_all_lights()
        self.stop_all_sounds()
        self.sound.stop_music()
        self.set_status(None)

    #
    # Settings
    #

    def load_game_settings(self):
        self.load_settings('game_default_settings.yaml', 'game_user_settings.yaml')

        # Work-around because the framework cannot handle settings with a floating point increment.
        # By the time we get here, GameController.load_settings() already discarded the options and the increments.
        # Let's keep the work-around simple and hardcode the value we expect in the yaml file
        self.volume_scale = 20.0
        self.volume_increments = 1

        self.sound.music_volume_offset = self.user_settings['Machine']['Music volume offset'] / self.volume_scale
        # TODO
        #self.sound.set_volume(self.user_settings['Machine']['Initial volume'] / self.volume_scale)

        # read other game settings
        self.balls_per_game = self.user_settings['Gameplay']['Balls per game']
        self.score_display.set_left_players_justify(self.user_settings['Display']['Left side score justify'])

        num_blocks_setting = int(self.user_settings['Gameplay']['Blocks for Ultimate Challenge'])
        self.blocks_required = min(16, 4 * ceil(num_blocks_setting / 4)) # a multiple of 4 less than or equal to 16

    #
    # Stats
    #

    def load_game_stats(self):
        self.load_game_data('game_default_data.yaml', 'game_user_data.yaml')
        for category in self.all_highscore_categories:
            category.load_from_game(self)

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

    #
    # High Scores
    #

    def create_high_score_categories(self):
        classic_category = HighScoreCategory()
        classic_category.game_data_key = 'ClassicHighScoreData'

        blocks_category = self.create_high_score_category('BlocksHighScoreData', 'Block Champ', 'num_blocks', ' block')
        inner_loops_category = self.create_high_score_category('InnerLoopsHighScoreData', 'Inner Loop Champ', 'best_inner_loops', ' loop')
        outer_loops_category = self.create_high_score_category('OuterLoopsHighScoreData', 'Outer Loop Champ', 'best_outer_loops', ' loop')

        supergame_category = HighScoreCategory()
        supergame_category.game_data_key = 'SuperGameHighScoreData'
        supergame_category.titles = ['SuperGame Champion', 'SuperGame High Score #1', 'SuperGame High Score #2', 'SuperGame High Score #3', 'SuperGame High Score #4']

        self.highscore_categories = [classic_category, blocks_category, inner_loops_category, outer_loops_category]
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

    def highscore_entry_ready_to_prompt(self, mode, prompt):
        self.sound.play_voice('high score')
        banner_mode = Mode(game=self, priority=8)
        markup = MarkupFrameGenerator()
        text = '\n#GREAT JOB#\n[%s]' % (prompt.left.upper()) # we know that the left is the player name
        frame = markup.frame_for_markup(markup=text, y_offset=0)
        banner_mode.layer = ScriptedLayer(width=128, height=32, script=[{'seconds':3.0, 'layer':FrameLayer(frame=frame)}])
        banner_mode.layer.on_complete = lambda: self.highscore_banner_complete(banner_mode=banner_mode, highscore_entry_mode=mode)
        self.modes.add(banner_mode)

    def highscore_banner_complete(self, banner_mode, highscore_entry_mode):
        self.remove_modes([banner_mode])
        self.update_lamps()
        highscore_entry_mode.prompt()

    def highscore_entry_finished(self, mode):
        self.remove_modes([mode])
        self.modes.add(self.attract_mode)
        self.attract_mode.game_over_display()
        self.update_lamps()

        # Handle game stats.
        for i in range(0, len(self.players)):
            game_time = self.get_game_time(i)
            self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
            self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
            self.game_data['Audits']['Games Played'] += 1

        self.save_game_data('game_data.yaml')

    def format_points(self, points):
        # disregard the locale, always insert commas between groups of 3 digits
        return '00' if points == 0 else '{:,}'.format(points)

    #
    # Service Mode
    #

    def start_service_mode(self):
        """ remove all existing modes that are running
            stop music, stop lamp shows, disable flippers
            then add the service mode.
        """

        self.stop()

        self.lampctrl.stop_show()
        for lamp in self.lamps:
            lamp.disable()

        self.enable_flippers(False)
        self.modes.add(self.service_mode)

    def service_mode_ended(self):
        self.reset()
        self.update_lamps()

    #
    # Sound
    #

    def stop_all_sounds(self):
        # workaround for pyprocgame's SoundController lack of functionality
        #for key in self.sound.sounds:
        #    self.sound.sounds[key][0].stop()
        self.sound.voice_end_time = 0

    def volume_down(self):
        # implementing volume_down()/volume_up() ourselves allows more than 10 steps
        volume = round(self.sound.volume * self.volume_scale)
        volume = max(0, volume - self.volume_increments)
        self.sound.set_volume(volume / self.volume_scale)
        self.set_status('VOLUME DOWN: ' + str(int(volume)), scroll=False)

    def volume_up(self):
        volume = round(self.sound.volume * self.volume_scale)
        volume = min(self.volume_scale, volume + self.volume_increments)
        self.sound.set_volume(volume / self.volume_scale)
        self.set_status('VOLUME UP: ' + str(int(volume)), scroll=False)

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
        for lamp in self.lamps:
            lamp.disable()

        # Disable all flashers
        for coil in self.coils:
            if coil.name.startswith('flasher'):
                coil.disable()


def main():
    game = None
    try:
        game = JD2Game()
        game.run_loop()
    finally:
        del game

if __name__ == '__main__':
    main()
