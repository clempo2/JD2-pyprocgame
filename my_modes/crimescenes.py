from random import shuffle
from procgame.dmd import GroupedLayer, TextLayer
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


class CityBlocks(Mode):
    """Controls the progress through the city block modes"""

    def __init__(self, game, priority):
        super(CityBlocks, self).__init__(game, priority)
        self.city_block = CityBlock(self, priority + 1)
        self.block_war = BlockWar(self, priority + 5)
        self.block_war_bonus = BlockWarBonus(self, priority + 5)

    def mode_started(self):
        self.start_city_block()

    def mode_stopped(self):
        self.game.remove_modes([self.city_block, self.block_war, self.block_war_bonus])

    def reset(self):
        self.city_block.reset()

    def start_city_block(self):
        if self.game.getPlayerState('current_block', 0) < self.game.blocks_required:
            self.game.modes.add(self.city_block)

    def city_blocks_completed(self):
        self.game.modes.remove(self.city_block)
        self.game.update_lamps()
        self.game.setPlayerState('blocks_complete', True)
        self.game.base_play.regular_play.city_blocks_completed()

    def start_block_war(self):
        self.game.modes.remove(self.city_block)
        self.block_war.reset()
        self.start_multiball_callback()
        self.game.modes.add(self.block_war)
        self.game.update_lamps()

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
        self.city_block.next_block()
        # next_block updated the lamps
        self.start_city_block()
        self.end_multiball_callback()

    def evt_ball_drained(self):
        # End multiball if there is now only one ball in play
        if self.game.getPlayerState('multiball_active', 0) & 0x6:
            self.end_multiball()

    def update_lamps(self):
        # Count the number of block wars applicable to starting the next Ultimate Challenge
        # Block wars applicable to an already played Ultimate Challenge don't count for the lamps
        if self.game.getPlayerState('blocks_complete', False):
            num_block_wars = 4 # this avoids the confusion when modulo blocks_required returns 0
        else:
            num_blocks = self.game.getPlayerState('num_blocks', 0)
            played_block_wars = int((num_blocks % self.game.blocks_required) / 4)
            free_block_wars = int((16 - self.game.blocks_required) / 4)
            num_block_wars = free_block_wars + played_block_wars
        for num in range(1, 5):
            lamp_name = 'crimeLevel' + str(num)
            style = 'on' if num <= num_block_wars else 'off'
            self.game.drive_lamp(lamp_name, style)


class CityBlock(CrimeSceneShots):
    """Mode using the crime scene shot to secure a city block"""

    def __init__(self, parent, priority):
        super(CityBlock, self).__init__(parent.game, priority)
        self.parent = parent

        # we always award the most difficult target that remains in the current block
        self.target_award_order = [1, 3 ,0, 2, 4]
        self.extra_ball_block = 4 # securing 4 blocks awards an extra ball

        difficulty = self.game.user_settings['Gameplay']['Block difficulty']
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
        # force the mode to initialize at block 0 the next time it starts
        # num_blocks continue to accrue
        self.game.setPlayerState('current_block', -1)
        self.game.setPlayerState('blocks_complete', False)

    def mode_started(self):
        self.targets = self.game.getPlayerState('block_targets', None)

        self.num_advance_hits = 0
        if self.game.getPlayerState('current_block', -1) == -1:
            self.next_block()

    def mode_stopped(self):
        self.layer = None
        self.game.setPlayerState('block_targets', self.targets)
        # num_blocks and current_block are always up to date in the player state for other modes to see

    #
    # Award One Crime Scene Shot
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
                self.block_complete()
            else:
                self.game.sound.play_voice('crime')
            self.game.update_lamps()

    def block_complete(self):
        self.game.score(10000)
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.game.addPlayerState('num_blocks', 1) 
        num_blocks = self.game.getPlayerState('num_blocks', 0) 

        if num_blocks == self.extra_ball_block:
            self.game.base_play.light_extra_ball()

        if num_blocks % 4 == 0:
            self.parent.start_block_war()
        else:
            # internally blocks start at 0, on the display blocks start at 1
            current_block = self.game.getPlayerState('current_block', -1)
            self.display_block_complete(current_block + 1, 10000)
            self.game.sound.play_voice('block complete ' + str(current_block + 1))
            self.next_block()

    def next_block(self):
        current_block = self.game.getPlayerState('current_block', -1)
        if current_block < self.game.blocks_required:
            current_block += 1
            self.game.setPlayerState('current_block', current_block)
            if current_block == self.game.blocks_required:
                self.parent.city_blocks_completed()
            else:
                # the block consists of num_to_pick many targets chosen among the targets listed in pick_from
                # every selected target needs to be hit once
                pick_from = self.level_pick_from[current_block]
                shuffle(pick_from)

                num_to_pick = self.level_num_shots[current_block]
                if num_to_pick > len(pick_from):
                    raise ValueError('Number of targets necessary for block ' + current_block + ' exceeds the list of targets in the template')

                # Now fill targets according to shuffled template
                self.targets = [0] * 5
                for i in range(0, num_to_pick):
                    self.targets[pick_from[i]] = 1
        self.game.update_lamps()

    def display_block_complete(self, block, points):
        small_font = self.game.fonts['07x5']
        block_layer = TextLayer(128/2, 9, small_font, 'center').set_text('Block ' + str(block) + ' secured', 2)
        award_layer = TextLayer(128/2, 19, small_font, 'center').set_text(self.game.format_score(points) + ' points', 2)
        self.layer = GroupedLayer(128, 32, [block_layer, award_layer])

    #
    # Lamps
    #

    def update_lamps(self):
        styles = ['on', 'slow', 'fast', 'off']
        style = styles[self.num_advance_hits]
        self.game.drive_lamp('advanceCrimeLevel', style)

        current_block = self.game.getPlayerState('current_block', -1)
        lamp_color = current_block % 4
        for shot in range(0, 5):
            for color in range(0, 4):
                lamp_name = 'perp' + str(shot + 1) + self.lamp_colors[color]
                style = 'medium' if self.targets[shot] and lamp_color == color else 'off'
                self.game.drive_lamp(lamp_name, style)


class BlockWar(CrimeSceneShots):
    """Multiball activated by securing city blocks"""

    def __init__(self, parent, priority):
        super(BlockWar, self).__init__(parent.game, priority)
        self.parent = parent
        self.countdown_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')
        self.score_reason_layer = TextLayer(128/2, 7, self.game.fonts['07x5'], 'center')
        self.score_value_layer = TextLayer(128/2, 17, self.game.fonts['07x5'], 'center')
        self.anim_layer = self.game.animations['blockwars']
        self.layer = GroupedLayer(128, 32, [self.anim_layer, self.countdown_layer, self.banner_layer, self.score_reason_layer, self.score_value_layer])

    def mode_started(self):
        self.game.addPlayerState('multiball_active', 0x2)
        self.banner_layer.set_text('Block War', 3)
        self.game.sound.play_voice('block war start')
        self.game.trough.launch_balls(1, self.start_callback)

    def mode_stopped(self):
        self.game.addPlayerState('multiball_active', -0x2)
        self.cancel_delayed('rotate_bonus_target')

    # trough callback
    def start_callback(self):
        ball_save_time = self.game.user_settings['Gameplay']['Block Wars ballsave time']
        # 1 ball added already from launcher.  So ask ball_save to save
        # new total of balls in play.
        local_num_balls_to_save = self.game.trough.num_balls_in_play
        self.game.ball_save_start(num_balls_to_save=local_num_balls_to_save, time=ball_save_time, now=False, allow_multiple_saves=True)

    def reset(self):
        # go back to the first round
        self.num_shots_required_per_target = 1
        self.shots_required = [1, 1, 1, 1, 1]

    def next_round(self, inc_num_shots):
        if inc_num_shots:
            if self.num_shots_required_per_target < 4:
                self.num_shots_required_per_target += 1
        self.num_shots_required = [self.num_shots_required_per_target] * 5

    def switch_hit(self, shot):
        if self.shots_required[shot] > 0:
            self.shots_required[shot] -= 1
            multiplier = self.game.getPlayerState('num_hurry_ups', 0) + 1
            score = 5000 * multiplier
            self.score_value_layer.set_text(str(score), 2)
            self.game.score(score)
            self.game.sound.play('block_war_target')
            if self.shots_required[shot] == 0:
                self.score_reason_layer.set_text('Block ' + str(shot + 1) + ' secured!', 2)

            if not any(self.shots_required):
                # all shots hit already
                self.round_complete()
        else:
            self.game.sound.play_voice('good shot')
            self.game.update_lamps()

    def round_complete(self):
        self.game.score(10000)
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.parent.start_block_war_bonus()

    def update_lamps(self):
        self.game.drive_lamp('advanceCrimeLevel', 'off')
        for shot in range(0, 5):
            for color in range(0, 4):
                lamp_name = 'perp' + str(shot + 1) + self.lamp_colors[color]
                style = 'medium' if color < self.shots_required[shot] else 'off'
                self.game.drive_lamp(lamp_name, style)


class BlockWarBonus(CrimeSceneShots):
    """Bonus round after a successful block war round, shoot the rotating target"""

    def __init__(self, parent, priority):
        super(BlockWarBonus, self).__init__(parent.game, priority)
        self.parent = parent
        self.banner_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center')

    def mode_started(self):
        self.game.addPlayerState('multiball_active', 0x4)
        self.bonus_shot = 0
        self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=1)
        self.game.sound.play_voice('jackpot is lit')

    def mode_stopped(self):
        self.game.addPlayerState('multiball_active', -0x4)
        self.cancel_delayed('rotate_bonus_target')

    # rotate all the way to the end and back only once
    def rotate_bonus_target(self, bonus_step):
        if self.bonus_shot == 4:
            bonus_step = -1
        self.bonus_shot += bonus_step
        if self.bonus_shot == -1:
            self.parent.end_block_war_bonus(False)
        else:
            self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=bonus_step)
        self.game.update_lamps()

    def switch_hit(self, shot):
        if shot == self.bonus_shot:
            self.cancel_delayed('rotate_bonus_target')
            self.bonus_round_collected()

    def bonus_round_collected(self):
        self.game.score(200000)
        self.banner_layer.set_text('Jackpot', 2)
        self.game.sound.play_voice('jackpot')
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.parent.end_block_war_bonus(True)

    def update_lamps(self):
        self.game.drive_lamp('advanceCrimeLevel', 'off')
        for shot in range(0, 5):
            style = 'medium' if self.bonus_shot == shot else 'off'
            self.game.drive_perp_lamp('perp' + str(shot + 1), style)
