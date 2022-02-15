from procgame.dmd import Animation, AnimatedLayer, font_named

class AssetLoader(object):
    """An asset manager inspired by SkeletonGame.AssetManager"""

    def __init__(self, game):
        self.game = game
        self.animations = {}
        self.fonts = {}

    def load_assets(self, curr_file_path):

        animations_files = [
            {'key': 'cityscape', 'file': 'cityscape.dmd', 'repeat':True, 'frame_time':2},
            {'key': 'Splash', 'file': 'Splash.dmd', 'holdLastFrame':True, 'frame_time':1},
            {'key': 'darkjudges_no_bg', 'file': 'darkjudges_no_bg.dmd', 'repeat':True, 'frame_time':4},
            {'key': 'longwalk', 'file': 'longwalk.dmd', 'frame_time':7},
            {'key': 'blackout', 'file': 'blackout.dmd', 'frame_time':3},
            #{'key': 'scope', 'file': 'scope.dmd', 'repeat':True, 'frame_time':8},
            {'key': 'dredd_shoot_at_sniper', 'file': 'dredd_shoot_at_sniper.dmd', 'frame_time':5},
            {'key': 'blockwars', 'file': 'blockwars.dmd', 'repeat':True, 'frame_time':3},
            {'key': 'jdpeople', 'file': 'jdpeople.dmd', 'frame_time':1},
            {'key': 'cows', 'file': 'cows.dmd', 'frame_time':1},
            {'key': 'scopeandshot', 'file': 'scopeandshot.dmd', 'frame_time':1},
            {'key': 'gun_powerup', 'file': 'gun_powerup.dmd', 'holdLastFrame':True, 'composite_op':'blacksrc', 'frame_time':7},
            {'key': 'bike_across_screen', 'file': 'bike_across_screen.dmd', 'frame_time':3},
            {'key': 'bikeacrosscity', 'file': 'bikeacrosscity.dmd', 'frame_time':5},
            {'key': 'EBAnim', 'file': 'EBAnim.dmd', 'frame_time':1}
        ]

        lampshow_files = [
            {'key': 'advance_level', 'file': 'crimescene_advance_level.lampshow'},
            {'key': 'attract0', 'file': 'attract_show_horiz.lampshow'},
            {'key': 'attract1', 'file': 'attract_show_vert.lampshow'},
            {'key': 'jackpot', 'file': 'jackpot.lampshow'},
            {'key': 'shot_hit', 'file': 'flashers_only.lampshow'},
        ]

        music_files = [
            {'key': 'background', 'file': 'brainsDarkMelody(161).aif'},
            {'key': 'ball_launch', 'file': 'introloop(161).aif'},
            {'key': 'mode', 'file': 'Heroes and Angels -- Loopable.aif'},
            {'key': 'mode', 'file': '40 Second guitar solo.aif'},
            {'key': 'mode', 'file': '55 second loopable -- Sonya.aif'},
            {'key': 'mode', 'file': '105 second loopable -- Sisyphus.aif'},
            {'key': 'multiball', 'file': 'Heroes and Angels -- Loopable.aif'},
            {'key': 'multiball', 'file': '40 Second guitar solo.aif'},
            {'key': 'multiball', 'file': '55 second loopable -- Sonya.aif'},
            {'key': 'multiball', 'file': '105 second loopable -- Sisyphus.aif'},
        ]

        effects_files = [
            {'key': 'block_war_target', 'file': 'DropTarget.wav'},
            {'key': 'outlane', 'file': 'Outlane.wav'},
            {'key': 'inlane', 'file': 'Inlane.wav'},
            {'key': 'meltdown', 'file': 'CaptiveBall.wav'},
            {'key': 'ball_launch', 'file': 'BallLaunchMotorcycle.wav'},
            {'key': 'drop_target', 'file': 'DropTarget.wav'},
            {'key': 'extra_ball_target', 'file': 'ExtraBallTargetLower.wav'},
            {'key': 'shooterL_launch', 'file': 'LeftKickBack.wav'},
            {'key': 'outer_loop', 'file': 'BallLaunchMotorcycle.wav'},
            {'key': 'inner_loop', 'file': 'BallLaunchMotorcycle.wav'},
            {'key': 'mystery', 'file': 'Question Mark.wav'},
            {'key': 'right_ramp', 'file': 'rightrampflyby.ogg'},
            {'key': 'left_ramp', 'file': 'LoopFlyBy.wav'},
            {'key': 'slingshot', 'file': 'Slingshot.wav'},
            {'key': 'bonus', 'file': 'DropTarget.wav'}
        ]

        voice_files = [
            {'key': 'attract', 'file': 'attract/jd - dont do drugs.wav'},
            {'key': 'attract', 'file': 'attract/jd - gaze into the fist of dredd.wav'},
            {'key': 'attract', 'file': 'attract/jd - i am the law.wav'},
            {'key': 'attract', 'file': 'attract/judge death - i have come to bring law to the city my law.wav'},
            {'key': 'attract', 'file': 'attract/judge death - i have come to bring you the law of death.wav'},
            {'key': 'attract', 'file': 'attract/judge death - i have come to stop this world again.wav'},
            {'key': 'attract', 'file': 'attract/judge death - my name is death i have come to judge you.wav'},
            {'key': 'attract', 'file': 'attract/judge death - the crime is life.wav'},
            {'key': 'attract', 'file': 'attract/judge death - the sentence is death.wav'},
            {'key': 'attract', 'file': 'attract/judge fire - for you the party is over.wav'},
            {'key': 'attract', 'file': 'attract/judge fire - let the flames of justice cleanse you.wav'},
            {'key': 'drain', 'file': 'drain/jd - prepare to be judged.wav'},
            {'key': 'boring', 'file': 'boring/jd - this is boring.wav'},
            {'key': 'boring', 'file': 'boring/wake me when something happens.wav'},
            {'key': 'collected', 'file': 'hurryup/wow thats awesome.wav'},
            {'key': 'collected', 'file': 'hurryup/great shot.wav'},
            {'key': 'collected', 'file': 'hurryup/incredible shot.wav'},
            {'key': 'collected', 'file': 'hurryup/jd - excellent.wav'},
            {'key': 'pursuit intro', 'file': 'pursuit/bank robbery suspects fleeing.wav'},
            {'key': 'good shot', 'file': 'pursuit/great shot.wav'},
            {'key': 'good shot', 'file': 'pursuit/incredible shot.wav'},
            {'key': 'good shot', 'file': 'pursuit/jd - excellent.wav'},
            {'key': 'in pursuit', 'file': 'pursuit/jd - in pursuit 1.wav'},
            {'key': 'in pursuit', 'file': 'pursuit/jd - in pursuit 2.wav'},
            {'key': 'complete', 'file': 'pursuit/suspects apprehended.wav'},
            {'key': 'failed', 'file': 'pursuit/suspects got away.wav'},
            {'key': 'sniper - miss', 'file': 'sniper/jd - missed him.wav'},
            {'key': 'sniper - miss', 'file': 'sniper/jd - drokk.wav'},
            {'key': 'sniper - miss', 'file': 'sniper/jd - grud.wav'},
            {'key': 'sniper - hit', 'file': 'sniper/jd - sniper neutralized.wav'},
            {'key': 'sniper - hit', 'file': 'sniper/jd - take that punk.wav'},
            {'key': 'sniper - shot', 'file': 'sniper/gunshot.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 1.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 2.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 3.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 4.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 5.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 6.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 7.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 8.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 9.wav'},
            {'key': 'tank intro', 'file': 'battle_tank/unknown tank block 10.wav'},
            {'key': 'tank hit 1', 'file': 'battle_tank/its damaged but still going.wav'},
            {'key': 'tank hit 2', 'file': 'battle_tank/tank hit 1 more shot.wav'},
            {'key': 'tank hit 3', 'file': 'battle_tank/tank down.wav'},
            {'key': 'meltdown 1', 'file': 'meltdown/reactor 1 stabilized.wav'},
            {'key': 'meltdown 2', 'file': 'meltdown/reactor 2 stabilized.wav'},
            {'key': 'meltdown 3', 'file': 'meltdown/reactor 3 stabilized.wav'},
            {'key': 'meltdown 4', 'file': 'meltdown/reactor 4 stabilized.wav'},
            {'key': 'meltdown all', 'file': 'meltdown/all reactors stabilized.wav'},
            {'key': 'meltdown intro', 'file': 'meltdown/power towers going critical.wav'},
            {'key': 'bi - ouch', 'file': 'bad_impersonator/ouch 1.wav'},
            {'key': 'bi - ouch', 'file': 'bad_impersonator/ouch 2.wav'},
            {'key': 'bi - ouch', 'file': 'bad_impersonator/ouch 3.wav'},
            {'key': 'bi - ouch', 'file': 'bad_impersonator/ouch 4.wav'},
            {'key': 'bi - ouch', 'file': 'bad_impersonator/ouch 5.wav'},
            {'key': 'bi - song', 'file': 'bad_impersonator/song 1.wav'},
            {'key': 'bi - song', 'file': 'bad_impersonator/song 2.wav'},
            {'key': 'bi - song', 'file': 'bad_impersonator/song 3.wav'},
            {'key': 'bi - song', 'file': 'bad_impersonator/song 4.wav'},
            {'key': 'bi - song', 'file': 'bad_impersonator/song 5.wav'},
            {'key': 'bi - boo', 'file': 'bad_impersonator/boo 1.wav'},
            {'key': 'bi - boo', 'file': 'bad_impersonator/boo 2.wav'},
            {'key': 'bi - boo', 'file': 'bad_impersonator/boo 3.wav'},
            {'key': 'bi - boo', 'file': 'bad_impersonator/boo 4.wav'},
            {'key': 'bi - boo', 'file': 'bad_impersonator/boo 5.wav'},
            {'key': 'bi - shutup', 'file': 'bad_impersonator/Shut Up 1.aif'},
            {'key': 'bi - shutup', 'file': 'bad_impersonator/Shut Up 2.aif'},
            {'key': 'bi - shutup', 'file': 'bad_impersonator/Shut Up 3.aif'},
            {'key': 'bi - shutup', 'file': 'bad_impersonator/Shut Up 4.aif'},
            {'key': 'bad impersonator', 'file': 'bad_impersonator/bad impersonation in progress.wav'},
            {'key': 'bad guys', 'file': 'safecracker/hurry up.wav'},
            {'key': 'bad guys', 'file': 'safecracker/running out of time.wav'},
            {'key': 'complete', 'file': 'safecracker/jd - youre done.wav'},
            {'key': 'shot', 'file': 'safecracker/surrounded.wav'},
            {'key': 'shot', 'file': 'safecracker/great shot.wav'},
            {'key': 'shot', 'file': 'safecracker/jd - excellent.wav'},
            {'key': 'shot', 'file': 'safecracker/jd - do it again.wav'},
            {'key': 'mm - intro', 'file': 'manhunt/bank robbers trying to escape judgement.wav'},
            {'key': 'mm - shot', 'file': 'manhunt/aahh.wav'},
            {'key': 'mm - shot', 'file': 'manhunt/jd - i got one.wav'},
            {'key': 'mm - shot', 'file': 'manhunt/jd - that will stop him.wav'},
            {'key': 'mm - done', 'file': 'manhunt/jd - fugutives captured.wav'},
            {'key': 'so - over there', 'file': 'stakeout/jd - over there 1.wav'},
            {'key': 'so - over there', 'file': 'stakeout/jd - over there 2.wav'},
            {'key': 'so - surrounded', 'file': 'stakeout/jd - we have you surrounded.wav'},
            {'key': 'so - move in', 'file': 'stakeout/jd - move in now.wav'},
            {'key': 'so - move in', 'file': 'stakeout/jd - thats it take em down.wav'},
            {'key': 'so - boring', 'file': 'stakeout/jd - are we sure we have the right place.wav'},
            {'key': 'so - boring', 'file': 'stakeout/jd - this is boring.wav'},
            {'key': 'so - boring', 'file': 'stakeout/most boring stakeout ever.wav'},
            {'key': 'so - boring', 'file': 'stakeout/wake me when something happens.wav'},
            {'key': 'Block 1 Neutralized', 'file': 'crimescenes/block 1 neutralized.wav'},
            {'key': 'Block 1 Pacified', 'file': 'crimescenes/block 1 pacified.wav'},
            {'key': 'Block 1 Secured', 'file': 'crimescenes/block 1 secured.wav'},
            {'key': 'Block 2 Neutralized', 'file': 'crimescenes/block 2 neutralized.wav'},
            {'key': 'Block 2 Pacified', 'file': 'crimescenes/block 2 pacified.wav'},
            {'key': 'Block 2 Secured', 'file': 'crimescenes/block 2 secured.wav'},
            {'key': 'Block 3 Neutralized', 'file': 'crimescenes/block 3 neutralized.wav'},
            {'key': 'Block 3 Pacified', 'file': 'crimescenes/block 3 pacified.wav'},
            {'key': 'Block 3 Secured', 'file': 'crimescenes/block 3 secured.wav'},
            {'key': 'Block 4 Neutralized', 'file': 'crimescenes/block 4 neutralized.wav'},
            {'key': 'Block 4 Pacified', 'file': 'crimescenes/block 4 pacified.wav'},
            {'key': 'Block 4 Secured', 'file': 'crimescenes/block 4 secured.wav'},
            {'key': 'Block 5 Neutralized', 'file': 'crimescenes/block 5 neutralized.wav'},
            {'key': 'Block 5 Pacified', 'file': 'crimescenes/block 5 pacified.wav'},
            {'key': 'Block 5 Secured', 'file': 'crimescenes/block 5 secured.wav'},
            {'key': 'Block 6 Neutralized', 'file': 'crimescenes/block 6 neutralized.wav'},
            {'key': 'Block 6 Pacified', 'file': 'crimescenes/block 6 pacified.wav'},
            {'key': 'Block 6 Secured', 'file': 'crimescenes/block 6 secured.wav'},
            {'key': 'Block 7 Neutralized', 'file': 'crimescenes/block 7 neutralized.wav'},
            {'key': 'Block 7 Pacified', 'file': 'crimescenes/block 7 pacified.wav'},
            {'key': 'Block 7 Secured', 'file': 'crimescenes/block 7 secured.wav'},
            {'key': 'Block 8 Neutralized', 'file': 'crimescenes/block 8 neutralized.wav'},
            {'key': 'Block 8 Pacified', 'file': 'crimescenes/block 8 pacified.wav'},
            {'key': 'Block 8 Secured', 'file': 'crimescenes/block 8 secured.wav'},
            {'key': 'Block 9 Neutralized', 'file': 'crimescenes/block 9 neutralized.wav'},
            {'key': 'Block 9 Pacified', 'file': 'crimescenes/block 9 pacified.wav'},
            {'key': 'Block 9 Secured', 'file': 'crimescenes/block 9 secured.wav'},
            {'key': 'Block 10 Neutralized', 'file': 'crimescenes/block 10 neutralized.wav'},
            {'key': 'Block 10 Pacified', 'file': 'crimescenes/block 10 pacified.wav'},
            {'key': 'Block 10 Secured', 'file': 'crimescenes/block 10 secured.wav'},
            {'key': 'Block 11 Neutralized', 'file': 'crimescenes/block 11 neutralized.wav'},
            {'key': 'Block 11 Pacified', 'file': 'crimescenes/block 11 pacified.wav'},
            {'key': 'Block 11 Secured', 'file': 'crimescenes/block 11 secured.wav'},
            {'key': 'Block 12 Neutralized', 'file': 'crimescenes/block 12 neutralized.wav'},
            {'key': 'Block 12 Pacified', 'file': 'crimescenes/block 12 pacified.wav'},
            {'key': 'Block 12 Secured', 'file': 'crimescenes/block 12 secured.wav'},
            {'key': 'Block 13 Neutralized', 'file': 'crimescenes/block 13 neutralized.wav'},
            {'key': 'Block 13 Pacified', 'file': 'crimescenes/block 13 pacified.wav'},
            {'key': 'Block 13 Secured', 'file': 'crimescenes/block 13 secured.wav'},
            {'key': 'Block 14 Neutralized', 'file': 'crimescenes/block 14 neutralized.wav'},
            {'key': 'Block 14 Pacified', 'file': 'crimescenes/block 14 pacified.wav'},
            {'key': 'Block 14 Secured', 'file': 'crimescenes/block 14 secured.wav'},
            {'key': 'Block 15 Neutralized', 'file': 'crimescenes/block 15 neutralized.wav'},
            {'key': 'Block 15 Pacified', 'file': 'crimescenes/block 15 pacified.wav'},
            {'key': 'Block 15 Secured', 'file': 'crimescenes/block 15 secured.wav'},
            {'key': 'Block 16 Neutralized', 'file': 'crimescenes/block 16 neutralized.wav'},
            {'key': 'Block 16 Pacified', 'file': 'crimescenes/block 16 pacified.wav'},
            {'key': 'Block 16 Secured', 'file': 'crimescenes/block 16 secured.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 1.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 2.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 3.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 4.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 5.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 6.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 7.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 8.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 9.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 10.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 11.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 12.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 13.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 14.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 15.wav'},
            {'key': 'crime', 'file': 'crimescenes/crime 16.wav'},
            {'key': 'jackpot is lit', 'file': 'crimescenes/jackpot is lit.wav'},
            {'key': 'jackpot', 'file': 'crimescenes/jackpot - excited.wav'},
            {'key': 'jackpot', 'file': 'crimescenes/jaackpott.wav'},
            {'key': 'good shot', 'file': 'crimescenes/great shot.wav'},
            {'key': 'good shot', 'file': 'crimescenes/incredible shot.wav'},
            {'key': 'good shot', 'file': 'crimescenes/wow thats awesome.wav'},
            {'key': 'good shot', 'file': 'crimescenes/jd - excellent.wav'},
            {'key': 'block war start', 'file': 'crimescenes/riot in sector 13.wav'},
            {'key': 'block war start', 'file': 'crimescenes/rioting reported.wav'},
            {'key': 'block war start', 'file': 'crimescenes/war 1.wav'},
            {'key': 'block war start', 'file': 'crimescenes/war 2.wav'},
            {'key': 'block war start', 'file': 'crimescenes/war 3.wav'},
            {'key': 'block war start', 'file': 'crimescenes/war 4.wav'},
            {'key': 'jackpot is lit', 'file': 'multiball/jackpot is lit.wav'},
            {'key': 'jackpot', 'file': 'multiball/jackpot - excited.wav'},
            {'key': 'jackpot', 'file': 'multiball/jaackpott.wav'},
            {'key': 'shoot the left ramp', 'file': 'multiball/shoot the left ramp.wav'},
            {'key': 'shoot the left ramp', 'file': 'multiball/jd - shoot the left ramp.wav'},
            {'key': 'again', 'file': 'multiball/again.wav'},
            {'key': 'locks lit', 'file': 'multiball/jd - lets lock em up.wav'},
            {'key': 'ball 1 locked', 'file': 'multiball/jd - ball 1 captured.wav'},
            {'key': 'ball 2 locked', 'file': 'multiball/jd - ball 2 locked.wav'},
            {'key': 'multiball', 'file': 'multiball/calling all units the gang has escaped.wav'},
            {'key': 'multiball', 'file': 'multiball/escape from detention block aa23.wav'},
            {'key': 'moo', 'file': 'jd - moo.wav'},
            {'key': 'bad guy shot', 'file': 'shooting_gallery/man shot 1.wav'},
            {'key': 'bad guy shot', 'file': 'shooting_gallery/man shot 2.wav'},
            {'key': 'bad guy shot', 'file': 'shooting_gallery/man shot 3.wav'},
            {'key': 'bad guy shot', 'file': 'shooting_gallery/man shot 4.wav'},
            {'key': 'bad guy shot', 'file': 'shooting_gallery/man shot 5.wav'},
            {'key': 'good guy shot', 'file': 'shooting_gallery/mother 1.wav'},
            {'key': 'good guy shot', 'file': 'shooting_gallery/mother 2.wav'},
            {'key': 'good shot', 'file': 'skillshot/great shot.wav'},
            {'key': 'good shot', 'file': 'skillshot/incredible shot.wav'},
            {'key': 'good shot', 'file': 'skillshot/wow thats awesome.wav'},
            {'key': 'good shot', 'file': 'skillshot/jd - do it again.wav'},
            {'key': 'good shot', 'file': 'skillshot/jd - excellent.wav'},
            {'key': 'tilt warning', 'file': 'warning.wav'},
            {'key': 'tilt warning', 'file': 'jd - im warning you.wav'},
            {'key': 'tilt', 'file': 'jd - put down your weapons.wav'},
            {'key': 'fire - taunt', 'file': 'ultimate_challenge/judge fire - for you the party is over.wav'},
            {'key': 'fire - taunt', 'file': 'ultimate_challenge/judge fire - let the flames of justice cleanse you.wav'},
            {'key': 'fear - taunt', 'file': 'ultimate_challenge/judge fear - all must die.wav'},
            {'key': 'fear - taunt', 'file': 'ultimate_challenge/judge fear - gaze into the face of fear.wav'},
            {'key': 'fear - taunt', 'file': 'ultimate_challenge/judge fear - justice must be done.wav'},
            {'key': 'fear - taunt', 'file': 'ultimate_challenge/judge fear - there is no escape from justice.wav'},
            {'key': 'mortis - taunt', 'file': 'ultimate_challenge/judge mortis - decay in peace.wav'},
            {'key': 'mortis - taunt', 'file': 'ultimate_challenge/judge mortis - rejoice.wav'},
            {'key': 'mortis - taunt', 'file': 'ultimate_challenge/judge mortis - this city is guilty.wav'},
            {'key': 'mortis - taunt', 'file': 'ultimate_challenge/judge mortis - you cannot hurt us now.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - i have come to bring law to the city my law.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - i have come to bring you law the law of death.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - i have come to stop this world again.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - my name is death i have come to judge you.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - the crime is life.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - the sentence is death.wav'},
            {'key': 'death - taunt', 'file': 'ultimate_challenge/judge death - you cannot kill what does not live.wav'},
            {'key': 'ball saved', 'file': 'pity ball.wav'},
            {'key': 'ball saved', 'file': 'cant you do better than that.wav'},
            {'key': 'ball saved', 'file': 'who told you to stop.wav'},
            {'key': 'ball saved', 'file': 'you may judge again.wav'},
            {'key': 'ball saved', 'file': 'you may judge again 2.wav'},
            {'key': 'ball saved', 'file': 'jd - never do that again.wav'},
            {'key': 'curse', 'file': 'jd - curse 1.wav'},
            {'key': 'curse', 'file': 'jd - curse 2.wav'},
            {'key': 'curse', 'file': 'jd - curse 3.wav'},
            {'key': 'curse', 'file': 'jd - curse 4.wav'},
            {'key': 'curse', 'file': 'jd - curse 5.wav'},
            {'key': 'curse', 'file': 'jd - curse 6.wav'},
            {'key': 'curse', 'file': 'jd - curse 7.wav'},
            {'key': 'curse', 'file': 'jd - curse 8.wav'},
            {'key': 'curse', 'file': 'jd - curse 9.wav'},
            {'key': 'curse', 'file': 'jd - curse 10.wav'},
            {'key': 'curse', 'file': 'jd - curse 11.wav'},
            {'key': 'welcome', 'file': 'welcome.wav'},
            {'key': 'welcome', 'file': 'jd - reporting for duty.wav'},
            {'key': 'welcome', 'file': 'judge death - i have come to bring law to the city my law.wav'},
            {'key': 'welcome', 'file': 'judge death - i have come to stop this world again.wav'},
            {'key': 'shoot again 1', 'file': 'shoot again player 1.wav'},
            {'key': 'shoot again 2', 'file': 'shoot again player 2.wav'},
            {'key': 'shoot again 3', 'file': 'shoot again player 3.wav'},
            {'key': 'shoot again 4', 'file': 'shoot again player 4.wav'},
            {'key': 'high score', 'file': 'congratulations.wav'}
        ]

        fonts_files = [
            {'key': 'tiny7', 'file': '04B-03-7px.dmd'},
            {'key': 'jazz18', 'file': 'Jazz18-18px.dmd'},
            {'key': 'num_14x10', 'file': 'Font14x10.dmd'},
            {'key': '07x5', 'file': 'Font07x5.dmd'}
        ]

        assets_path = curr_file_path + '/assets'

        animations_prefix = assets_path + '/dmd/'
        for asset in animations_files:
            anim = Animation().load(animations_prefix + asset['file'])
            repeat = asset.get('repeat', False)
            hold_last_frame = asset.get('holdLastFrame', False)
            frame_time = asset.get('frame_time', 1)
            layer = AnimatedLayer(frames=anim.frames, repeat=repeat, hold=hold_last_frame, frame_time=frame_time)
            composite_op = asset.get('composite_op')
            if composite_op:
                layer.composite_op = composite_op
            self.animations[asset['key']] = layer

        lampshow_prefix = assets_path + '/lamps/'
        for asset in lampshow_files:
            self.game.lampctrl.register_show(asset['key'], lampshow_prefix + asset['file'])

        music_prefix = assets_path + '/sound/'
        for asset in music_files:
            self.game.sound.register_music(asset['key'], music_prefix + asset['file'])

        effects_prefix = assets_path + '/sound/FX/'
        for asset in effects_files:
            self.game.sound.register_sound(asset['key'], effects_prefix + asset['file'])

        voice_prefix = assets_path + '/sound/Voice/'
        for asset in voice_files:
            self.game.sound.register_sound(asset['key'], voice_prefix + asset['file'])

        for asset in fonts_files:
            self.fonts[asset['key']] = font_named(asset['file'])
