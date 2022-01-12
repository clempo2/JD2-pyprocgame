from random import randint
from procgame.dmd import ExpandTransition, Frame, FrameLayer, GroupedLayer, ScriptedLayer, TextLayer
from procgame.game import Mode

class ShootingGallery(Mode):
    def __init__(self, game, priority, video_mode_setting):
        super(ShootingGallery, self).__init__(game, priority)

        self.cow_mode = video_mode_setting == 'cow'
        if self.cow_mode:
            cows_anim = self.game.animations['cows']
            self.cow_image_frames = cows_anim.frames[0].create_frames_from_grid(4, 1)
        else:
            gallery_anim = self.game.animations['jdpeople']
            self.image_frames = gallery_anim.frames[0].create_frames_from_grid(6, 2)

        self.scope_and_shot_anim = self.game.animations['scopeandshot'].frames
        self.on_complete = None

    def mode_started(self):
        self.scope_pos = 0
        self.targets = ['empty'] * 4
        self.num_enemies = 0
        self.num_enemies_old = 0
        self.num_enemies_shot = 0
        self.speed_factor = 1
        
        self.state = 'active'
        self.success = False

        self.intro_active = True
        self.intro()

    def intro(self):
        self.game.enable_flippers(False)
        self.status_layer = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=False).set_text('Video Mode')
        self.intro_layer_0 = GroupedLayer(128, 32, [self.status_layer])

        if self.cow_mode:
            enemy_text = 'Shoot mean cows'
            friend_text = 'Do NOT shoot nice cows'
        else:
            enemy_text = 'Shoot enemies'
            friend_text = 'Do NOT shoot friends'

        self.intro_layer_11 = TextLayer(128/2, 7, self.game.fonts['07x5'], 'center').set_text(enemy_text)
        self.intro_layer_12 = TextLayer(128/2, 17, self.game.fonts['07x5'], 'center').set_text(friend_text)
        self.intro_layer_1 = GroupedLayer(128, 32, [self.intro_layer_11, self.intro_layer_12])

        self.intro_layer_21 = TextLayer(128/2, 7, self.game.fonts['07x5'], 'center').set_text('Flipper buttons aim')
        self.intro_layer_22 = TextLayer(128/2, 17, self.game.fonts['07x5'], 'center').set_text('Fire buttons shoot')
        self.intro_layer_2 = GroupedLayer(128, 32, [self.intro_layer_21, self.intro_layer_22])

        self.intro_layer_3 = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=False).set_text('Video Mode').set_text('Ready...')

        self.intro_layer_4 = TextLayer(128/2, 7, self.game.fonts['jazz18'], 'center', opaque=False).set_text('Video Mode').set_text('Begin!')

        self.layer = ScriptedLayer(128, 32, [
            {'seconds':3.0, 'layer':self.intro_layer_0},
            {'seconds':3.0, 'layer':self.intro_layer_1},
            {'seconds':3.0, 'layer':self.intro_layer_2},
            {'seconds':3.0, 'layer':self.intro_layer_3},
            {'seconds':1.0, 'layer':self.intro_layer_4}])

        self.layer.on_complete = self.start

    def start(self):
        self.intro_active = False
        self.status_layer.set_text('')

        self.target_layers = [self.new_frame_layer(True) for unused in range(0, 4)]
        self.scope_layer = self.new_frame_layer()
        self.bullet_layers = [self.new_frame_layer() for unused in range(0, 4)]
        self.result_layer = TextLayer(128/2, 20, self.game.fonts['07x5'], 'center', opaque=False)

        all_layers = self.target_layers + [self.scope_layer] + self.bullet_layers + [self.status_layer, self.result_layer]
        self.layer = GroupedLayer(128, 32, all_layers)

        # Add the first target after 1 second.
        self.delay(name='add', event_type=None, delay=1, handler=self.add_target)
        self.update_scope_pos()

    def new_frame_layer(self, transition=False):
        frame_layer = FrameLayer()
        frame_layer.composite_op = 'blacksrc'
        if transition:
            frame_layer.transition = ExpandTransition()
        return frame_layer

    def add_target(self):
        if self.num_enemies == 15:
            self.delay(name='finish', event_type=None, delay=2.0, handler=self.finish)
        else:
            if self.speed_factor < 5 and self.num_enemies % 4 == 3 and self.num_enemies != self.num_enemies_old:
                self.speed_factor += 1
                self.num_enemies_old = self.num_enemies
            if self.state == 'active':
                target_index = randint(0, 3)
                target_type = randint(0, 1)

                # Find the first empty position starting with the random target_index.
                for i in range(0, 3):
                    position = (i + target_index) % 4
                    if self.targets[position] == 'empty':
                        if target_type:
                            self.show_enemy(position, -1)
                        else:
                            self.show_friend(position, -1)
                        self.delay(name='remove', event_type=None, delay=3.0-(self.speed_factor * 0.4), handler=self.remove_target, param=position)
                        break

                # Add a new target every 2 seconds.
                self.delay(name='add', event_type=None, delay=2.0-(self.speed_factor*0.3), handler=self.add_target)

    def finish(self):
        self.state = 'complete'
        self.status_layer.set_text('Completed!')
        self.intro_layer_21.set_text('Completion Bonus:')
        self.intro_layer_22.set_text(str(100000))
        self.layer = self.intro_layer_2
        self.delay(name='show_num_shot', event_type=None, delay=2.0, handler=self.show_num_shot)

    def show_num_shot(self):
        self.intro_layer_21.set_text('Enemies Shot:')
        self.intro_layer_22.set_text(str(self.num_enemies_shot) + ' of ' + str(self.num_enemies))
        self.success = self.num_enemies_shot == self.num_enemies
        if self.success:
            self.delay(name='perfect', event_type=None, delay=3.0, handler=self.perfect)
        else:
            self.delay(name='wrap_up', event_type=None, delay=3.0, handler=self.wrap_up)

    def perfect(self):
        self.status_layer.set_text('Perfect!')
        self.layer = self.status_layer
        self.layer.opaque = True
        self.delay(name='wrap_up', event_type=None, delay=2.0, handler=self.wrap_up)

    def wrap_up(self):
        self.game.enable_flippers(True)
        if self.on_complete != None:
            self.on_complete(self.success)

    def remove_target(self, position):
        # Only remove if it hasn't been shot.
        # If it has been shot, it will be removed later.
        if self.targets[position] != 'shot' and self.state == 'active':
            self.targets[position] = 'empty'
            self.target_layers[position].transition.in_out = 'out'
            self.target_layers[position].transition.start()

    def show_friend(self, position, target_index=-1):
        if target_index == -1:
            target_index = 0 if self.cow_mode else randint(6, 11)
        self.show_target(position, target_index)
        self.targets[position] = 'friend'

    def show_enemy(self, position, target_index=-1):
        self.num_enemies += 1
        if target_index == -1:
            if self.cow_mode:
                target_index = 1
            else:
                target_index = randint(0,5)

        self.show_target(position, target_index)
        self.targets[position] = 'enemy'

    def show_target(self, position, target_index):
        new_frame = Frame(128,32)
        src_frames = self.cow_image_frames if self.cow_mode else self.image_frames
        Frame.copy_rect(dst=new_frame, dst_x=position*32, dst_y=0, src=src_frames[target_index], src_x=0, src_y=0, width=32, height=32, op='blacksrc')
        self.target_layers[position].frame = new_frame
        self.target_layers[position].transition.in_out = 'in'
        self.target_layers[position].transition.start()

    def sw_flipperLwL_active(self, sw):
        self.flipper_active('flipperLwR', -1)

    def sw_flipperLwR_active(self, sw):
        self.flipper_active('flipperLwL', 1)

    def flipper_active(self, other_flipper, pos_delta):
        if self.intro_active:
            if self.game.switches[other_flipper].is_active():
                self.layer.force_next(True)
        elif self.state == 'active':
            new_pos = self.scope_pos + pos_delta
            if 0 <= new_pos <= 3:
                self.scope_pos = new_pos
                self.update_scope_pos()

    def update_scope_pos(self):
        self.scope_layer.frame = self.scope_and_shot_anim[self.scope_pos]

    def sw_fireL_active(self, sw):
        self.fire_active()

    def sw_fireR_active(self, sw):
        self.fire_active()

    def fire_active(self):
        if self.intro_active:
            # skip the intro
            self.layer = None
            self.start()
        else:
            self.shoot()

    def shoot(self):
        self.bullet_layers[self.scope_pos].frame = self.scope_and_shot_anim[self.scope_pos + 4]
        if self.targets[self.scope_pos] == 'enemy':
            self.delay(name='enemy_shot', event_type=None, delay=1.5, handler=self.enemy_shot, param=self.scope_pos)
            self.targets[self.scope_pos] = 'shot'
            self.result_layer.set_text('Good Shot', 1)
            self.num_enemies_shot += 1
            self.game.sound.play('bad guy shot')
        elif self.targets[self.scope_pos] == 'empty':
            self.delay(name='empty_shot', event_type=None, delay=0.5, handler=self.empty_shot, param=self.scope_pos)
        elif self.targets[self.scope_pos] == 'friend':
            self.friend_shot()

    def enemy_shot(self, position):
        self.target_layers[position].blink_frames = 2
        self.bullet_layers[position].blink_frames = 2
        self.delay(name='enemy_remove', event_type=None, delay=1, handler=self.enemy_remove, param=position)

    def enemy_remove(self, position):
        self.targets[position] = 'empty'
        self.target_layers[position].frame = None
        self.bullet_layers[position].frame = None
        self.target_layers[position].blink_frames = 0
        self.bullet_layers[position].blink_frames = 0

    def friend_shot(self):
        self.game.sound.play('good guy shot')
        self.state = 'complete'
        self.status_layer.set_text('Failed!')
        self.cancel_delayed(['empty_shot', 'enemy_shot', 'enemy_remove', 'friend_shot', 'add', 'finish'])
        self.delay(name='wrap_up', event_type=None, delay=2.0, handler=self.wrap_up)
        self.success = False

    def empty_shot(self, position):
        # Make sure it's still empty
        if self.targets[position] == 'empty':
            self.bullet_layers[position].frame = None
