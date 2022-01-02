import locale
from math import ceil
from random import shuffle
from procgame.dmd import GroupedLayer, TextLayer
from procgame.game import Mode
from procgame.modes import Scoring_Mode

class CrimeScenes(Mode):
    """Controls the progress through the crime scene modes"""

    def __init__(self, game, priority):
        super(CrimeScenes, self).__init__(game, priority)

        num_levels = int(self.game.user_settings['Gameplay']['Crimescene levels for finale'])
        self.levels_required = min(16, 4 * ceil(num_levels / 4)) # a multiple of 4 less than or equal to 16

        self.crime_scene_levels = CrimeSceneLevels(game, priority + 1, self.levels_required)
        self.crime_scene_levels.start_block_war = self.start_block_war
        self.crime_scene_levels.crime_scenes_completed = self.crime_scene_levels_completed

        self.block_war = BlockWar(game, priority + 5)
        self.block_war.start_block_war_bonus = self.start_block_war_bonus

        self.block_war_bonus = BlockWarBonus(game, priority + 5)
        self.block_war_bonus.end_block_war_bonus = self.end_block_war_bonus

    def mode_started(self):
        self.start_crime_scene_levels()

    def mode_stopped(self):
        self.game.remove_modes([self.crime_scene_levels, self.block_war, self.block_war_bonus])

    def is_complete(self):
        return self.game.getPlayerState('crimescenes_level', 0) >= self.levels_required

    def start_crime_scene_levels(self):
        if self.game.getPlayerState('crimescenes_level', 0) < self.levels_required:
            self.game.modes.add(self.crime_scene_levels)

    def crime_scene_levels_completed(self):
        self.game.modes.remove(self.crime_scene_levels)
        self.game.update_lamps()
        self.game.base_play.regular_play.crime_scenes_completed()

    def start_block_war(self):
        self.game.modes.remove(self.crime_scene_levels)
        self.block_war.reset()
        self.game.modes.add(self.block_war)
        self.game.update_lamps()
        self.start_multiball_callback()

    def start_block_war_bonus(self):
        self.game.modes.remove(self.block_war)
        self.game.modes.add(self.block_war_bonus)
        self.game.update_lamps()

    def end_block_war_bonus(self, bonus_collected):
        self.game.modes.remove(self.block_war_bonus)
        self.block_war.next_round(bonus_collected)
        self.game.modes.add(self.block_war)
        self.game.update_lamps()

    def end_multiball(self):
        self.game.modes.remove(self.block_war)
        self.game.modes.remove(self.block_war_bonus)
        self.crime_scenes_levels.next_level()
        # next_level updated the lamps
        self.start_crime_scene_levels()
        self.end_multiball_callback()

    def is_multiball_active(self):
        return (self.block_war in self.game.modes or
                self.block_war_bonus in self.game.modes)

    def update_lamps(self):
        # Use 4 center crime scene lamps to indicate fraction of required levels completed in quarters
        level = self.game.getPlayerState('crimescenes_level', 0)
        num_quarters = int(level * 4 / self.levels_required)
        for num in range(1, 5):
            lamp_name = 'crimeLevel' + str(num)
            style = 'on' if num <= num_quarters else 'off'
            self.game.drive_lamp(lamp_name, style)

class CrimeSceneBase(Scoring_Mode):
    """Base class for modes using the crime scene shots"""

    def __init__(self, game, priority):
        super(CrimeSceneBase, self).__init__(game, priority)
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

class CrimeSceneLevels(CrimeSceneBase):
    """Crime scenes mode"""

    def __init__(self, game, priority, levels_required):
        super(CrimeSceneLevels, self).__init__(game, priority)
        self.levels_required = levels_required

        # we always award the most difficult target that remains in the current level
        self.target_award_order = [1, 3 ,0, 2, 4]
        self.extra_ball_level = 4

        difficulty = self.game.user_settings['Gameplay']['Crimescene shot difficulty']
        if difficulty == 'easy':
            self.level_pick_from = [
                [2,4], [2,4], [2,4], [2,4],
                [0,2,4], [0,2,4], [0,2,4], [0,2,4], [0,2,4], [0,2,4],
                [0,2,3,4], [0,2,3,4], [0,2,3,4], [0,2,3,4],
                [0,1,2,3,4], [0,1,2,3,4]
            ]
            self.level_num_shots = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5]
        elif difficulty == 'medium':
            self.level_pick_from = [
                [2,4], [2,4], [2,4], [2,4],
                [0,2,4], [0,2,4], [0,2,4], [0,2,4],
                [0,2,3,4], [0,2,3,4], [0,2,3,4], [0,2,3,4],
                [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4]
            ]
            self.level_num_shots = [1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5]
        else:
            self.level_pick_from = [
                [0,2,4], [0,2,4], [0,2,4], [0,2,4],
                [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4],
                [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4],
                [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4], [0,1,2,3,4]
            ]
            self.level_num_shots = [1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5]

    def reset(self):
        # force the mode to initialize at level 0 the next time it starts
        self.game.setPlayerState('crimescenes_level', -1)

    def mode_started(self):
        # restore player state
        player = self.game.current_player()
        self.targets = player.getState('crimescenes_targets', None)
        self.total_levels = player.getState('crimescenes_total_levels', 0)

        self.num_advance_hits = 0
        if player.getState('crimescenes_level', -1) == -1:
            self.next_level()

    def mode_stopped(self):
        # save player state
        player = self.game.current_player()
        player.setState('crimescenes_targets', self.targets)
        player.setState('crimescenes_total_levels', self.total_levels)
        # 'crimescenes_level' is always kept up to date in the player's state for other modes to see

    def get_status_layers(self):
        tiny_font = self.game.fonts['tiny7']
        level = self.game.getPlayerState('crimescenes_level', -1)
        title_layer = TextLayer(128/2, 7, tiny_font, 'center').set_text('Crime Scenes')
        level_layer = TextLayer(128/2, 16, tiny_font, 'center').set_text('Current Level: ' + str(level + 1) + '/' + str(self.levels_required))
        block_layer = TextLayer(128/2, 25, tiny_font, 'center').set_text('Block War in ' + str(4-(level % 4)) + ' levels')
        status_layer = GroupedLayer(128, 32, [title_layer, level_layer, block_layer])
        return [status_layer]

    #
    # Advance Crime Level
    #

    def sw_threeBankTargets_active(self, sw):
        self.num_advance_hits += 1
        if self.num_advance_hits == 3:
            self.award_one_hit()
            self.num_advance_hits = 0
        self.game.update_lamps()

    def award_one_hit(self):
        for shot in self.target_award_order:
            if self.targets[shot]:
                self.switch_hit(shot)
                break

    #
    # Crime Scene Shots
    #

    def switch_hit(self, shot):
        if self.targets[shot]:
            self.targets[shot] = 0
            self.game.score(1000)

            if not any(self.targets):
                # all targets hit already
                self.level_complete()
            else:
                self.game.sound.play_voice('crime')
            self.game.update_lamps()

    def level_complete(self):
        self.game.score(10000)
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.total_levels += 1
        level = self.game.getPlayerState('crimescenes_level', -1)
        level += 1
        self.game.setPlayerState('crimescenes_level', level)

        if level == self.extra_ball_level:
            self.game.base_play.light_extra_ball()

        if (level % 4) == 3:
            self.start_block_war()
        else:
            self.display_level_complete(level, 10000)
            self.game.sound.play_voice('block complete ' + str(level))
            self.next_level()

    def next_level(self):
        level = self.game.getPlayerState('crimescenes_level', -1)
        if level < self.levels_required:
            level += 1
            self.game.setPlayerState('crimescenes_level', level)
            if level == self.levels_required:
                self.crime_scenes_completed()
            else:
                # the level consists of num_to_pick many targets chosen among the targets listed in pick_from
                # every selected target needs to be hit once
                pick_from = self.level_pick_from[level]
                shuffle(pick_from)

                num_to_pick = self.level_num_shots[level]
                if num_to_pick > len(pick_from):
                    raise ValueError('Number of targets necessary for level ' + level + ' exceeds the list of targets in the template')

                # Now fill targets according to shuffled template
                self.targets = [0] * 5
                for i in range(0, num_to_pick):
                    self.targets[pick_from[i]] = 1
        self.game.update_lamps()

    def display_level_complete(self, level, points):
        small_font = self.game.fonts['07x5']
        title_layer = TextLayer(128/2, 7, small_font, 'center').set_text('Advance Crimescene', 1.5)
        level_layer = TextLayer(128/2, 14, small_font, 'center').set_text('Level ' + str(level) + ' complete', 1.5)
        award_layer = TextLayer(128/2, 21, small_font, 'center').set_text('Award: ' + locale.format('%d', points, True) + ' points', 1.5)
        self.layer = GroupedLayer(128, 32, [title_layer, level_layer, award_layer])

    #
    # Lamps
    #

    def update_lamps(self):
        styles = ['on', 'slow', 'fast', 'off']
        style = styles[self.num_advance_hits]
        self.game.drive_lamp('advanceCrimeLevel', style)

        level = self.game.getPlayerState('crimescenes_level', -1)
        lamp_color = level % 4
        for shot in range(0, 5):
            for color in range(0, 4):
                lamp_name = 'perp' + str(shot+1) + self.lamp_colors[color]
                style = 'medium' if self.targets[shot] and lamp_color == color else 'off'
                self.game.drive_lamp(lamp_name, style)


class BlockWar(CrimeSceneBase):
    """Multiball activated by crime scenes"""

    def __init__(self, game, priority):
        super(BlockWar, self).__init__(game, priority)
        self.countdown_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.score_reason_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], 'center')
        self.score_value_layer = TextLayer(128/2, 17, self.game.fonts['07x5'], 'center')
        self.anim_layer = self.game.animations['blockwars']
        self.layer = GroupedLayer(128, 32, [self.anim_layer, self.countdown_layer, self.banner_layer, self.score_reason_layer, self.score_value_layer])

    def mode_started(self):
        self.banner_layer.set_text('Block War!', 3)
        self.game.sound.play_voice('block war start')
        self.game.trough.launch_balls(1, self.start_callback)

    def mode_stopped(self):
        self.cancel_delayed('rotate_bonus_target')

    # trough callback
    def start_callback(self):
        ball_save_time = self.game.user_settings['Gameplay']['Block Wars ballsave time']
        # 1 ball added already from launcher.  So ask ball_save to save
        # new total of balls in play.
        local_num_balls_to_save = self.game.trough.num_balls_in_play
        self.game.ball_save.start(num_balls_to_save=local_num_balls_to_save, time=ball_save_time, now=False, allow_multiple_saves=True)

    def reset(self):
        # go back to the first round
        self.shots_required_per_target = 1
        self.shots_required = [1, 1, 1, 1, 1]

    def next_round(self, inc_num_shots):
        if inc_num_shots:
            if self.shots_required_per_target < 4:
                self.shots_required_per_target += 1
        self.shots_required = [self.shots_required_per_target] * 5

    def switch_hit(self, shot):
        if self.shots_required[shot] > 0:
            self.shots_required[shot] -= 1
            multiplier = self.game.getPlayerState('num_modes_completed', 0) + 1
            score = 5000 * multiplier
            self.score_value_layer.set_text(str(score), 2)
            self.game.score(score)
            self.game.sound.play('block_war_target')
            if self.shots_required[shot] == 0:
                self.score_reason_layer.set_text('Block ' + str(shot+1) + ' secured!', 2)

            if not any(self.shots_required):
                # all shots hit already
                self.round_complete()
        else:
            self.game.sound.play_voice('good shot')
            self.game.update_lamps()

    def round_complete(self):
        self.game.score(10000)
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.start_block_war_bonus()

    def update_lamps(self):
        self.game.drive_lamp('advanceCrimeLevel', 'off')
        for shot in range(0, 5):
            for color in range(0, 4):
                lamp_name = 'perp' + str(shot+1) + self.lamp_colors[color]
                style = 'medium' if color < self.shots_required[shot] else 'off'
                self.game.drive_lamp(lamp_name, style)


class BlockWarBonus(CrimeSceneBase):
    """Bonus round after a successful block war round, shoot the rotating target"""

    def __init__(self, game, priority):
        super(BlockWarBonus, self).__init__(game, priority)
        self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')

    def mode_started(self):
        self.bonus_shot = 0
        self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=1)
        self.game.sound.play_voice('jackpot is lit')

    def mode_stopped(self):
        self.cancel_delayed('rotate_bonus_target')

    # rotate all the way to the end and back only once
    def rotate_bonus_target(self, bonus_step):
        if self.bonus_shot == 4:
            bonus_step = -1
        self.bonus_shot += bonus_step
        if self.bonus_shot == -1:
            self.end_block_war_bonus(False)
        else:
            self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=bonus_step)
        self.game.update_lamps()

    def switch_hit(self, shot):
        if shot == self.bonus_shot:
            self.cancel_delayed('rotate_bonus_target')
            self.bonus_round_collected()

    def bonus_round_collected(self):
        self.game.score(200000)
        self.banner_layer.set_text('Jackpot!', 2)
        self.game.sound.play_voice('jackpot')
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.end_block_war_bonus(True)

    def update_lamps(self):
        self.game.drive_lamp('advanceCrimeLevel', 'off')
        for shot in range(0, 5):
            style = 'medium' if self.bonus_shot == shot else 'off'
            self.game.drive_perp_lamp('perp' + str(shot+1), style)
