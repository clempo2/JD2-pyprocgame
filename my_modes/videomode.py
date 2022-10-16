from random import randint, shuffle
from procgame.dmd import ExpandTransition, Frame, FrameLayer, GroupedLayer, ScriptedLayer, TextLayer
from procgame.game import AdvancedMode, SwitchStop

class ShootingGallery(AdvancedMode):
    def __init__(self, game, priority):
        super(ShootingGallery, self).__init__(game, priority)
        self.on_complete = None

    def mode_started(self):
        self.success = False
        self.state = 'intro'
        self.scope_pos = 0
        self.num_enemies = 0
        self.num_enemies_shot = 0
        self.num_enemies_required = self.game.user_settings['Gameplay']['Video mode completion']
        self.speed_factor = 1
        self.targets = ['empty'] * 4

        video_mode_setting = self.game.user_settings['Gameplay']['Video mode']
        if video_mode_setting == 'cow':
            # family friendly option
            self.enemy = 'Mean Cow'
            self.enemies = 'Mean Cows'
            self.enemy_text = 'Shoot mean cows'
            self.friend_text = 'Do NOT shoot nice cows'
            self.bad_guy_shot = 'moo'
            cows_anim = self.game.animations['cows']
            image_frames = cows_anim.frames[0].create_frames_from_grid(2, 1)
            self.all_friends = [image_frames[0]] * 4
            self.all_enemies = [image_frames[1]] * 4
        else:
            # default option
            self.enemy = 'Enemy'
            self.enemies = 'Enemies'
            self.enemy_text = 'Shoot enemies'
            self.friend_text = 'Do NOT shoot friends'
            self.bad_guy_shot = 'bad guy shot'
            gallery_anim = self.game.animations['jdpeople']
            image_frames = gallery_anim.frames[0].create_frames_from_grid(6, 2)
            self.all_enemies = image_frames[0:6]
            self.all_friends = image_frames[6:12]

        self.available_friends = self.all_friends[:]
        self.available_enemies = self.all_enemies[:]
        shuffle(self.available_friends)
        shuffle(self.all_enemies)

        self.scope_frames = self.game.animations['scopeandshot'].frames[0:4]
        self.shot_frames = self.game.animations['scopeandshot'].frames[4:8]

        self.intro()

    def intro(self):
        self.game.enable_flippers(False)
        font_large = self.game.fonts['large']
        font_medium = self.game.fonts['medium']

        self.title_text_layer = TextLayer(128/2, 7, font_large, 'center').set_text('Video Mode')
        self.title_screen_layer = GroupedLayer(128, 32, [self.title_text_layer], opaque=True)

        self.info_text_layer_11 = TextLayer(128/2, 8, font_medium, 'center').set_text(self.enemy_text)
        self.info_text_layer_12 = TextLayer(128/2, 17, font_medium, 'center').set_text(self.friend_text)
        self.info_screen_layer_1 = GroupedLayer(128, 32, [self.info_text_layer_11, self.info_text_layer_12], opaque=True)

        self.info_text_layer_21 = TextLayer(128/2, 8, font_medium, 'center').set_text('Flipper buttons aim')
        self.info_text_layer_22 = TextLayer(128/2, 17, font_medium, 'center').set_text('Fire buttons shoot')
        self.info_screen_layer_2 = GroupedLayer(128, 32, [self.info_text_layer_21, self.info_text_layer_22], opaque=True)

        self.layer = ScriptedLayer(128, 32, [
            {'seconds':3.0, 'layer':self.title_screen_layer},
            {'seconds':3.0, 'layer':self.info_screen_layer_1},
            {'seconds':3.0, 'layer':self.info_screen_layer_2}],
            opaque=True)

        self.layer.on_complete = self.start

    def start(self):
        self.state = 'active'
        self.game.sound.play_voice('video mode')

        self.target_layers = [self.new_frame_layer(True) for unused in range(0, 4)]
        self.scope_layer = self.new_frame_layer()
        self.bullet_layers = [self.new_frame_layer() for unused in range(0, 4)]

        graphic_layers = self.target_layers + [self.scope_layer] + self.bullet_layers
        self.layer = GroupedLayer(128, 32, graphic_layers, opaque=True)

        # Add the first target after 1 second.
        self.delay(name='add_target', event_type=None, delay=1, handler=self.add_target)
        self.update_scope_pos()

    def new_frame_layer(self, transition=False):
        frame_layer = FrameLayer()
        frame_layer.composite_op = 'blacksrc'
        if transition:
            frame_layer.transition = ExpandTransition()
        return frame_layer

    def add_target(self):
        if self.num_enemies == self.num_enemies_required:
            self.delay(name='finish', event_type=None, delay=2.0, handler=self.finish)
        else:
            # speed up after the first 3 enemies shown, afterwards speed up after every 4 enemies shown
            if self.speed_factor < 6 and self.num_enemies == 4 * self.speed_factor - 1:
                self.speed_factor += 1

            # Find the first empty position starting with the random start_index.
            start_index = randint(0, 3)
            for i in range(0, 3):
                position = (i + start_index) % 4
                if self.targets[position] == 'empty':
                    target_type = randint(0, 1)
                    if target_type:
                        self.show_enemy(position)
                    else:
                        self.show_friend(position)
                    self.delay(name='remove_target', event_type=None, delay=3.0-(self.speed_factor * 0.4), handler=self.remove_target, param=position)
                    break

            # Add a new target after a short delay
            self.delay(name='add_target', event_type=None, delay=2.0-(self.speed_factor*0.3), handler=self.add_target)

    def show_friend(self, position):
        self.show_target(position, 'friend', self.available_friends)

    def show_enemy(self, position):
        self.num_enemies += 1
        self.show_target(position, 'enemy', self.available_enemies)

    def show_target(self, position, target_type, available_targets):
        self.bullet_layers[position].frame = None # remove empty shot if applicable
        # We never show the same friend or enemy on the screen more than once
        self.targets[position] = target_type
        target_frame = available_targets.pop()
        new_frame = Frame(128, 32)
        Frame.copy_rect(dst=new_frame, dst_x=position*32, dst_y=0, src=target_frame, src_x=0, src_y=0, width=32, height=32, op='blacksrc')
        self.target_layers[position].original_frame = target_frame
        self.target_layers[position].frame = new_frame
        self.target_layers[position].transition.in_out = 'in'
        self.target_layers[position].transition.start()

    def remove_target(self, position):
        # Only remove if it hasn't been shot.
        # If it has been shot, it will be removed later.
        if self.targets[position] != 'shot' and self.state == 'active':
            self.make_available(position)
            self.target_layers[position].transition.in_out = 'out'
            self.target_layers[position].transition.start()

    def make_available(self, position):
        available_targets = self.available_friends if self.targets[position] == 'friend' else self.available_enemies
        available_targets.append(self.target_layers[position].original_frame)
        shuffle(available_targets)
        self.targets[position] = 'empty'

    def sw_flipperLwL_active(self, sw):
        self.flipper_active(-1)

    def sw_flipperLwR_active(self, sw):
        self.flipper_active(1)

    def flipper_active(self, pos_delta):
        if self.state == 'intro':
            # skip the intro
            self.start()
        elif self.state == 'active':
            new_pos = self.scope_pos + pos_delta
            if 0 <= new_pos <= 3:
                self.scope_pos = new_pos
                self.update_scope_pos()

    def update_scope_pos(self):
        self.scope_layer.frame = self.scope_frames[self.scope_pos]

    def sw_fireL_active(self, sw):
        self.fire_active()
        return SwitchStop

    def sw_fireR_active(self, sw):
        self.fire_active()
        return SwitchStop

    def fire_active(self):
        if self.state == 'intro':
            # skip the intro
            self.start()
        elif self.state == 'active':
            self.shoot()

    def shoot(self):
        self.bullet_layers[self.scope_pos].frame = self.shot_frames[self.scope_pos]
        if self.targets[self.scope_pos] == 'empty':
            self.delay(name='remove_empty_shot', event_type=None, delay=0.5, handler=self.remove_empty_shot, param=self.scope_pos)
        elif self.targets[self.scope_pos] == 'friend':
            self.shoot_friend()
        elif self.targets[self.scope_pos] == 'enemy':
            self.shoot_enemy(self.scope_pos)

    def remove_empty_shot(self, position):
        # Make sure it's still empty
        if self.targets[position] == 'empty':
            self.bullet_layers[position].frame = None

    def shoot_friend(self):
        self.game.sound.play('good guy shot')
        self.state = 'complete'
        self.title_text_layer.set_text('Failed')
        self.layer = self.title_screen_layer
        self.cancel_delayed(['add_target', 'remove_target', 'remove_empty_shot', 'blink_enemy_shot', 'remove_enemy_shot', 'finish'])
        self.delay(name='wrap_up', event_type=None, delay=2.0, handler=self.wrap_up)
        self.success = False

    def shoot_enemy(self, position):
        self.num_enemies_shot += 1
        self.game.sound.play(self.bad_guy_shot)
        self.targets[position] = 'shot'
        self.delay(name='blink_enemy_shot', event_type=None, delay=1.5, handler=self.blink_enemy_shot, param=position)

    def blink_enemy_shot(self, position):
        self.target_layers[position].blink_frames = 2
        self.bullet_layers[position].blink_frames = 2
        # make sure remove_target triggers before remove_enemy_shot for this shot
        delay = 1.15 if self.speed_factor == 1 else 1
        self.delay(name='remove_enemy_shot', event_type=None, delay=delay, handler=self.remove_enemy_shot, param=position)

    def remove_enemy_shot(self, position):
        self.make_available(position)
        self.target_layers[position].frame = None
        self.bullet_layers[position].frame = None
        self.target_layers[position].blink_frames = 0
        self.bullet_layers[position].blink_frames = 0

    def finish(self):
        # the player reached the end of the round
        self.state = 'complete'
        self.cancel_delayed(['remove_target', 'remove_empty_shot', 'blink_enemy_shot', 'remove_enemy_shot'])

        self.success = self.num_enemies_shot == self.num_enemies_required
        if self.success:
            self.game.sound.play('perfect')

        text = str(self.num_enemies_shot) + ' ' + (self.enemy if self.num_enemies_shot == 1 else self.enemies)
        points = 100000 if self.success else 5000 * self.num_enemies_shot
        self.game.score(points)
        self.game.base_play.display(text, points)

        self.delay(name='wrap_up', event_type=None, delay=2.5, handler=self.wrap_up)

    def wrap_up(self):
        if self.success:
            self.game.base_play.display() # remove display early
        self.game.enable_flippers(True)
        if self.on_complete != None:
            self.on_complete(self.success)
