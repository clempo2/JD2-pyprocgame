from random import shuffle
from procgame.game import Mode
from crimescenes import CrimeSceneShots
from timer import TimedMode

class CityBlocks(Mode):
    """Controls the progress through the city block modes"""

    def __init__(self, game, priority):
        super(CityBlocks, self).__init__(game, priority)
        self.city_block = CityBlock(self, priority + 1)
        self.block_war = BlockWar(self, priority + 5)
        self.ball_save_time = self.game.user_settings['Gameplay']['Block War ballsave time']

    def mode_started(self):
        self.start_city_block()

    def mode_stopped(self):
        self.game.remove_modes([self.city_block, self.block_war])

    def reset(self):
        self.city_block.reset()

    def start_city_block(self):
        if self.game.getPlayerState('current_block', 0) < self.game.blocks_required:
            self.game.modes.add(self.city_block)

    def city_blocks_completed(self):
        self.game.remove_modes([self.city_block])
        self.game.setPlayerState('blocks_complete', True)
        self.game.base_play.regular_play.city_blocks_completed()
        # lamps were updated by city_blocks_completed()

    def start_block_war(self):
        self.game.remove_modes([self.city_block])
        self.start_multiball_callback()
        # launch another ball for a 2 ball multiball, or up to 4 balls when stacked with Deadworld multiball
        self.game.launch_balls(1)
        self.game.ball_save_start(time=self.ball_save_time, now=True, allow_multiple_saves=True)
        self.game.modes.add(self.block_war)
        self.game.update_lamps()

    def end_block_war(self):
        self.game.remove_modes([self.block_war])
        self.end_multiball_callback()
        self.city_block.next_block()
        self.start_city_block()

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
        self.target_award_order = [1, 3, 0, 2, 4]
        self.extra_ball_block = 6 # securing 6 blocks lights extra ball

        difficulty = self.game.user_settings['Gameplay']['Block difficulty']
        if difficulty == 'easy':
            self.level_pick_from = [
                [2,4], [2,4], [2,4], [2,4],
                [0,2,4], [0,2,4], [0,2,4], [0,2,4],
                [0,2,4], [0,2,4], [0,2,3,4], [0,2,3,4],
                [0,2,3,4], [0,2,3,4], [0,1,2,3,4], [0,1,2,3,4]
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

        self.block_outcome = ['Neutralized', 'Pacified', 'Secured']

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
            self.num_advance_hits = 0
            self.award_one_hit()
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
                self.block_complete(shot)
            else:
                self.game.sound.play_voice('crime')
            self.game.update_lamps()

    def block_complete(self, shot=None):
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
            shuffle(self.block_outcome)
            block_n_outcome = 'Block ' + str(current_block + 1) + ' ' + self.block_outcome[0]
            # don't hide the mode instructions if a mode is about to start
            if shot != 2 or self.game.base_play.regular_play.state != 'chain_ready':
                self.game.set_status(block_n_outcome)
            self.game.sound.play_voice(block_n_outcome)
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
                self.game.setPlayerState('block_targets', self.targets)
        self.game.update_lamps()

    #
    # Lamps
    #

    def update_lamps(self):
        styles = ['on', 'slow', 'fast']
        style = styles[self.num_advance_hits]
        self.game.drive_lamp('advanceCrimeLevel', style)

        current_block = self.game.getPlayerState('current_block', -1)
        lamp_color = current_block % 4
        for shot in range(0, 5):
            for color in range(0, 4):
                lamp_name = 'perp' + str(shot + 1) + self.lamp_colors[color]
                style = 'medium' if self.targets[shot] and lamp_color == color else 'off'
                self.game.drive_lamp(lamp_name, style)


class BlockWar(TimedMode, CrimeSceneShots):
    """Multiball activated by securing city blocks
       For round N: shoot every shot N times,
       After each round, shoot the rotating target for a block war bonus jackpot
    """

    def __init__(self, parent, priority):
        super(BlockWar, self).__init__(parent.game, priority, 0, 'Block War', 'Shoot all lit shots', 5, parent.game.animations['blockwars'])
        self.parent = parent
        # hide the mode name in the top left corner
        self.name_layer.set_text(None)

    def mode_started(self):
        super(BlockWar, self).mode_started()
        self.game.addPlayerState('multiball_active', 0x2)
        self.game.sound.play_voice('block war')
        self.num_shots_required_per_target = 1
        self.next_round(inc_num_shots=False)

    def mode_stopped(self):
        super(BlockWar, self).mode_stopped()
        self.game.addPlayerState('multiball_active', -0x2)

    def next_round(self, inc_num_shots):
        self.state = 'shots'
        self.num_shots = 0
        if inc_num_shots:
            if self.num_shots_required_per_target < 4:
                self.num_shots_required_per_target += 1
        self.num_shots_required = self.num_shots_required_per_target * 5
        self.shots_required = [self.num_shots_required_per_target] * 5
        self.update_status()
        self.game.update_lamps()

    def round_complete(self):
        # all shots are completed, start the bonus round
        self.game.score(10000)
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.state = 'bonus'
        self.bonus_shot = 0
        self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=1)
        self.game.sound.play_voice('jackpot is lit')
        self.update_status()
        self.game.update_lamps()

    def bonus_round_collected(self):
        self.game.score(100000)
        self.game.base_play.display('Jackpot')
        self.game.sound.play_voice('jackpot')
        self.game.lampctrl.play_show('advance_level', False, self.game.update_lamps)
        self.next_round(inc_num_shots=True)

    # rotate all the way to the end and back only once
    def rotate_bonus_target(self, bonus_step):
        if self.bonus_shot == 4:
            bonus_step = -1
        self.bonus_shot += bonus_step
        if self.bonus_shot == -1:
            self.next_round(inc_num_shots=False)
        else:
            self.delay(name='rotate_bonus_target', event_type=None, delay=3, handler=self.rotate_bonus_target, param=bonus_step)
        self.game.update_lamps()

    def switch_hit(self, shot):
        if self.state == 'shots':
            if self.shots_required[shot] > 0:
                self.shots_required[shot] -= 1
                self.incr_num_shots()
                self.game.update_lamps()

                multiplier = self.game.getPlayerState('num_hurry_ups', 0) + 1
                points = 5000 * multiplier
                self.game.score(points)

                if self.shots_required[shot]:
                    self.game.sound.play_voice('good shot')
                else:
                    self.game.sound.play('Block ' + str(shot + 1) + ' Secured')

                if self.num_shots == self.num_shots_required:
                    self.round_complete()
            else:
                self.game.sound.play('block_war_target')
        elif self.state == 'bonus':
            if shot == self.bonus_shot:
                self.cancel_delayed('rotate_bonus_target')
                self.bonus_round_collected()

    def update_lamps(self):
        self.game.drive_lamp('advanceCrimeLevel', 'off')
        if self.state == 'shots':
            for shot in range(0, 5):
                for color in range(0, 4):
                    lamp_name = 'perp' + str(shot + 1) + self.lamp_colors[color]
                    style = 'medium' if color < self.shots_required[shot] else 'off'
                    self.game.drive_lamp(lamp_name, style)
        elif self.state == 'bonus':
            for shot in range(0, 5):
                style = 'medium' if self.bonus_shot == shot else 'off'
                self.game.drive_perp_lamp('perp' + str(shot + 1), style)
            
    def update_status(self):
        if self.state == 'bonus':
            self.status_layer.set_text('Shoot rotating shot')
        else:
            super(BlockWar, self).update_status()

    def evt_ball_drained(self):
        # End multiball if there is now only one ball in play
        if self.game.getPlayerState('multiball_active', 0) & 0x2:
            if self.game.num_balls_requested() == 1:
                self.parent.end_block_war()

