import procgame
from procgame import *
import locale
import os
import pinproc
import random
from deadworld import Deadworld, DeadworldTest
from info import Info
from bonus import Bonus
from tilt import Tilt
from jd_modes import *

import logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

curr_file_path = os.path.dirname(os.path.abspath( __file__ ))
settings_path = curr_file_path + "/config/settings.yaml"
game_data_path = curr_file_path + "/config/game_data.yaml"
game_data_template_path = curr_file_path + "/config/game_data_template.yaml"
settings_template_path = curr_file_path + "/config/settings_template.yaml"

font_tiny7 = dmd.font_named('04B-03-7px.dmd')
font_jazz18 = dmd.font_named("Jazz18-18px.dmd")
font_14x10 = dmd.font_named("Font14x10.dmd")
font_18x12 = dmd.font_named("Font18x12.dmd")
font_07x4 = dmd.font_named("Font07x4.dmd")
font_07x5 = dmd.font_named("Font07x5.dmd")
font_09Bx7 = dmd.font_named("Font09Bx7.dmd")

class AssetLoader:
	"""An asset manager inspired by SkeletonGame.AssetManager"""
	def __init__(self, game):
		self.game = game
		self.animations = {}
		
	def load_assets(self):
		
		animations_files = [
			{'key': 'cityscape', 'file': 'cityscape.dmd', 'repeatAnim':True, 'frame_time':1},
			{'key': 'Splash', 'file': 'Splash.dmd', 'holdLastFrame':True, 'frame_time':1},
			{'key': 'guntech', 'file': 'guntech.dmd', 'frame_time':4},
			{'key': 'darkjudges_no_bg', 'file': 'darkjudges_no_bg.dmd', 'repeatAnim':True, 'frame_time':4},
			{'key': 'longwalk', 'file': 'longwalk.dmd', 'frame_time':7},
			{'key': 'blackout', 'file': 'blackout.dmd', 'frame_time':3},
			{'key': 'scope', 'file': 'scope.dmd', 'repeatAnim':True, 'frame_time':8},
			{'key': 'dredd_shoot_at_sniper', 'file': 'dredd_shoot_at_sniper.dmd', 'frame_time':5},
			{'key': 'blockwars', 'file': 'blockwars.dmd', 'repeatAnim':True, 'frame_time':3},
			{'key': 'jdpeople', 'file': 'jdpeople.dmd', 'frame_time':1},
			{'key': 'cows', 'file': 'cows.dmd', 'frame_time':1},
			{'key': 'scopeandshot', 'file': 'scopeandshot.dmd', 'frame_time':1},
			{'key': 'gun_powerup', 'file': 'gun_powerup.dmd', 'composite_op':'blacksrc', 'frame_time':5},
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
			{'key': 'mode', 'file': 'Heroes and Angels -- Loopable.aif'},
			{'key': 'mode', 'file': '40 Second guitar solo.aif'},
			{'key': 'mode', 'file': '55 second loopable -- Sonya.aif'},
			{'key': 'mode', 'file': '105 second loopable -- Sisyphus.aif'},
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
			{'key': 'block complete 1', 'file': 'crimescenes/block 1 neutralized.wav'},
			{'key': 'block complete 1', 'file': 'crimescenes/block 1 pacified.wav'},
			{'key': 'block complete 1', 'file': 'crimescenes/block 1 secured.wav'},
			{'key': 'block complete 2', 'file': 'crimescenes/block 2 neutralized.wav'},
			{'key': 'block complete 2', 'file': 'crimescenes/block 2 pacified.wav'},
			{'key': 'block complete 2', 'file': 'crimescenes/block 2 secured.wav'},
			{'key': 'block complete 3', 'file': 'crimescenes/block 3 neutralized.wav'},
			{'key': 'block complete 3', 'file': 'crimescenes/block 3 pacified.wav'},
			{'key': 'block complete 3', 'file': 'crimescenes/block 3 secured.wav'},
			{'key': 'block complete 4', 'file': 'crimescenes/block 4 neutralized.wav'},
			{'key': 'block complete 4', 'file': 'crimescenes/block 4 pacified.wav'},
			{'key': 'block complete 4', 'file': 'crimescenes/block 4 secured.wav'},
			{'key': 'block complete 5', 'file': 'crimescenes/block 5 neutralized.wav'},
			{'key': 'block complete 5', 'file': 'crimescenes/block 5 pacified.wav'},
			{'key': 'block complete 5', 'file': 'crimescenes/block 5 secured.wav'},
			{'key': 'block complete 6', 'file': 'crimescenes/block 6 neutralized.wav'},
			{'key': 'block complete 6', 'file': 'crimescenes/block 6 pacified.wav'},
			{'key': 'block complete 6', 'file': 'crimescenes/block 6 secured.wav'},
			{'key': 'block complete 7', 'file': 'crimescenes/block 7 neutralized.wav'},
			{'key': 'block complete 7', 'file': 'crimescenes/block 7 pacified.wav'},
			{'key': 'block complete 7', 'file': 'crimescenes/block 7 secured.wav'},
			{'key': 'block complete 8', 'file': 'crimescenes/block 8 neutralized.wav'},
			{'key': 'block complete 8', 'file': 'crimescenes/block 8 pacified.wav'},
			{'key': 'block complete 8', 'file': 'crimescenes/block 8 secured.wav'},
			{'key': 'block complete 9', 'file': 'crimescenes/block 9 neutralized.wav'},
			{'key': 'block complete 9', 'file': 'crimescenes/block 9 pacified.wav'},
			{'key': 'block complete 9', 'file': 'crimescenes/block 9 secured.wav'},
			{'key': 'block complete 10', 'file': 'crimescenes/block 10 neutralized.wav'},
			{'key': 'block complete 10', 'file': 'crimescenes/block 10 pacified.wav'},
			{'key': 'block complete 10', 'file': 'crimescenes/block 10 secured.wav'},
			{'key': 'block complete 11', 'file': 'crimescenes/block 11 neutralized.wav'},
			{'key': 'block complete 11', 'file': 'crimescenes/block 11 pacified.wav'},
			{'key': 'block complete 11', 'file': 'crimescenes/block 11 secured.wav'},
			{'key': 'block complete 12', 'file': 'crimescenes/block 12 neutralized.wav'},
			{'key': 'block complete 12', 'file': 'crimescenes/block 12 pacified.wav'},
			{'key': 'block complete 12', 'file': 'crimescenes/block 12 secured.wav'},
			{'key': 'block complete 13', 'file': 'crimescenes/block 13 neutralized.wav'},
			{'key': 'block complete 13', 'file': 'crimescenes/block 13 pacified.wav'},
			{'key': 'block complete 13', 'file': 'crimescenes/block 13 secured.wav'},
			{'key': 'block complete 14', 'file': 'crimescenes/block 14 neutralized.wav'},
			{'key': 'block complete 14', 'file': 'crimescenes/block 14 pacified.wav'},
			{'key': 'block complete 14', 'file': 'crimescenes/block 14 secured.wav'},
			{'key': 'block complete 15', 'file': 'crimescenes/block 15 neutralized.wav'},
			{'key': 'block complete 15', 'file': 'crimescenes/block 15 pacified.wav'},
			{'key': 'block complete 15', 'file': 'crimescenes/block 15 secured.wav'},
			{'key': 'block complete 16', 'file': 'crimescenes/block 16 neutralized.wav'},
			{'key': 'block complete 16', 'file': 'crimescenes/block 16 pacified.wav'},
			{'key': 'block complete 16', 'file': 'crimescenes/block 16 secured.wav'},
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
			{'key': 'welcome', 'file': 'judge death - i have come to stop this world again.wav'},
			{'key': 'shoot again 1', 'file': 'shoot again player 1.wav'},
			{'key': 'shoot again 2', 'file': 'shoot again player 2.wav'},
			{'key': 'shoot again 3', 'file': 'shoot again player 3.wav'},
			{'key': 'shoot again 4', 'file': 'shoot again player 4.wav'},
			{'key': 'high score', 'file': 'congratulations.wav'}
		]
		
		animations_prefix = curr_file_path + '/dmd/'
		for asset in animations_files:
			anim = dmd.Animation().load(animations_prefix + asset['file'])
			repeat = asset.get('repeat', False)
			holdLastFrame = asset.get('holdLastFrame', False)
			frame_time = asset.get('frame_time', 1)
			layer = dmd.AnimatedLayer(frames=anim.frames, repeat=repeat, hold=holdLastFrame, frame_time=frame_time)
			composite_op = asset.get('composite_op')
			if composite_op:
				layer.composite_op = composite_op
			self.animations[asset['key']] = layer

		lampshow_prefix = curr_file_path + '/lamps/'
		for asset in lampshow_files:
			self.game.lampctrl.register_show(asset['key'], lampshow_prefix + asset['file'])

		music_prefix = curr_file_path + '/sound/'
		for asset in music_files:
			self.game.sound.register_music(asset['key'], music_prefix + asset['file'])
		
		effects_prefix = curr_file_path + '/sound/FX/'
		for asset in effects_files:
			self.game.sound.register_sound(asset['key'], effects_prefix + asset['file'])
		
		voice_prefix = curr_file_path + '/sound/Voice/'
		for asset in voice_files:
			self.game.sound.register_sound(asset['key'], voice_prefix + asset['file'])


class Attract(game.Mode):
	"""Attract mode and start buttons"""
	
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.display_order = [0,1,2,3,4,5,6,7,8,9]
		self.display_index = 0

	def mode_started(self):
		self.play_super_game = False
		self.emptying_deadworld = False
		if self.game.deadworld.num_balls_locked > 0:
			self.game.deadworld.eject_balls(self.game.deadworld.num_balls_locked)
			self.emptying_deadworld = True
			self.delay(name='deadworld_empty', event_type=None, delay=10, handler=self.check_deadworld_empty)

		# Blink the start button to notify player about starting a game.
		self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
		# Blink the start button to notify player about starting a game.
		self.game.lamps.superGame.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
		# Turn on minimal GI lamps
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.disable()

		# Release the ball from places it could be stuck.
		for name in ['popperL', 'popperR', 'shooterL', 'shooterR']:
			if self.game.switches[name].is_active():
				self.game.coils[name].pulse()

		self.change_lampshow()
		
		self.cityscape_layer = self.game.animations['cityscape']
		self.jd_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Judge Dredd")
		self.jd_layer.transition = dmd.PushTransition(direction='south')
		self.proc_splash_layer = self.game.animations['Splash']
		self.proc_splash_layer.transition = dmd.PushTransition(direction='south')
		self.pyprocgame_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("pyprocgame")
		self.pyprocgame_layer.transition = dmd.PushTransition(direction='west')
		self.press_start_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Press Start", seconds=None, blink_frames=1)
		self.scores_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("High Scores")
		self.scores_layer.transition = dmd.PushTransition(direction='north')

		gen = dmd.MarkupFrameGenerator()
		credits_frame = gen.frame_for_markup("""


#CREDITS#

[Rules:]
[Gerry Stellenberg]

[Tools and Framework:]
[Adam Preble]

[Sound and Music:]
[Rob Keller]
[Jonathan Coultan]

[Dots:]
[Travis Highrise]

[P.ROC:]
[www.multimorphic.com]

[pyprocgame:]
[pyprocgame.pindev.org]

[Special thanks to:]
[Rob Anthony]
""")

		self.credits_layer = dmd.PanningLayer(width=128, height=32, frame=credits_frame, origin=(0,0), translate=(0,1), bounce=False)
		self.guntech_layer = self.game.animations['guntech']
		self.judges_layer = self.game.animations['darkjudges_no_bg']
		self.longwalk_layer = self.game.animations['longwalk']

		self.pre_game_display()

	def pre_game_display(self):
		script = [
			{'seconds':3.0, 'layer':self.jd_layer},
			{'seconds':4.0, 'layer':self.cityscape_layer},
			{'seconds':3.0, 'layer':self.proc_splash_layer},
			{'seconds':3.0, 'layer':self.pyprocgame_layer},
			{'seconds':3.0, 'layer':self.press_start_layer},
			{'seconds':3.0, 'layer':self.scores_layer}
		]

		for frame in highscore.generate_highscore_frames(self.game.highscore_categories):
			new_layer = dmd.FrameLayer(frame=frame)
			new_layer.transition = dmd.PushTransition(direction='north')
			script.append({'seconds':2.0, 'layer':new_layer})

		script.extend([
			{'seconds':20.0, 'layer':self.credits_layer},
			{'seconds':3.0, 'layer':self.judges_layer},
			{'seconds':4.0, 'layer':self.cityscape_layer}])

		self.layer = dmd.ScriptedLayer(width=128, height=32, script=script)

	def post_game_display(self):
		script = [
			{'seconds':3.0, 'layer':self.jd_layer},
			{'seconds':4.0, 'layer':self.cityscape_layer},
			{'seconds':3.0, 'layer':self.proc_splash_layer},
			{'seconds':3.0, 'layer':self.pyprocgame_layer},
			{'seconds':20.0, 'layer':self.credits_layer},
			{'seconds':3.0, 'layer':self.judges_layer},
			{'seconds':4.0, 'layer':self.cityscape_layer},
			{'seconds':3.0, 'layer':None},
			{'seconds':3.0, 'layer':self.scores_layer}
		]
		
		for frame in highscore.generate_highscore_frames(self.game.highscore_categories):
			new_layer = dmd.FrameLayer(frame=frame)
			new_layer.transition = dmd.PushTransition(direction='north')
			script.append({'seconds':2.0, 'layer':new_layer})

		self.layer = dmd.ScriptedLayer(width=128, height=32, script=script)

	def game_over_display(self):
		script = [
			{'seconds':6.0, 'layer':self.longwalk_layer},
			{'seconds':3.0, 'layer':None},
			{'seconds':3.0, 'layer':self.scores_layer}
		]

		for frame in highscore.generate_highscore_frames(self.game.highscore_categories):
			new_layer = dmd.FrameLayer(frame=frame)
			new_layer.transition = dmd.PushTransition(direction='north')
			script.append({'seconds':2.0, 'layer':new_layer})

		self.layer = dmd.ScriptedLayer(width=128, height=32, script=script)
		self.layer.on_complete = self.post_game_display

	def change_lampshow(self):
		random.shuffle(self.game.lampshow_keys)
		self.game.lampctrl.play_show(self.game.lampshow_keys[0], repeat=True)
		self.delay(name='lampshow', event_type=None, delay=10, handler=self.change_lampshow)

	def sw_fireL_active(self, sw):
		self.game.sound.play_voice('attract')

	def sw_fireR_active(self, sw):
		self.game.sound.play_voice('attract')

	def sw_flipperLwL_active(self, sw):
		self.layer.force_next(False)

	def sw_flipperLwR_active(self, sw):
		self.layer.force_next(True)

	# Eject any balls that get stuck before returning to the trough.
	def sw_popperL_active_for_500ms(self, sw): # opto!
		self.game.coils.popperL.pulse(40)

	def sw_popperR_active_for_500ms(self, sw): # opto!
		self.game.coils.popperR.pulse(40)

	def sw_shooterL_active_for_500ms(self, sw):
		self.game.coils.shooterL.pulse(40)

	def sw_shooterR_active_for_500ms(self, sw):
		self.game.coils.shooterR.pulse(40)

	# Enter service mode when the enter button is pushed.
	def sw_enter_active(self, sw):
		#self.game.modes.remove(self.show)
		self.cancel_delayed(name='lampshow')
		self.cancel_delayed(name='display')
		self.game.lampctrl.stop_show()
		for lamp in self.game.lamps:
			lamp.disable()
		del self.game.service_mode
		self.game.service_mode = procgame.service.ServiceMode(self.game,100,font_tiny7,[self.game.deadworld_test])
		self.game.modes.add(self.game.service_mode)
		return procgame.game.SwitchStop

	def sw_exit_active(self, sw):
		return procgame.game.SwitchStop

	# Outside of the service mode, up/down control audio volume.
	def sw_down_active(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return procgame.game.SwitchStop

	def sw_up_active(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return procgame.game.SwitchStop

	# Start button starts a game if the trough is full.  Otherwise it
	# initiates a ball search.
	# This is probably a good place to add logic to detect completely lost balls.
	# Perhaps if the trough isn't full after a few ball search attempts, it logs a ball
	# as lost?	
	def sw_startButton_active(self, sw):
		if self.game.trough.is_full():
			self.game.lampctrl.save_state('temp')
			# Stop the attract mode lampshows
			self.cancel_delayed(name='lampshow')
			self.game.lampctrl.stop_show()
			# Remove attract mode from mode queue - Necessary?
			self.game.modes.remove(self)
			# Initialize game	
			self.game.start_game()
			# Add the first player
			self.game.add_player()
			# Start the ball.  This includes ejecting a ball from the trough.
			self.game.start_ball()
		else: 
			if not self.emptying_deadworld:
				self.game.set_status("Ball Search!")
				self.game.ball_search.perform_search(5)
				self.game.deadworld.perform_ball_search()
		return procgame.game.SwitchStop

	def sw_superGame_active(self, sw):
		if self.game.trough.is_full():
			self.play_super_game = True
			self.game.lampctrl.save_state('temp')
			# Stop the attract mode lampshows
			self.cancel_delayed(name='lampshow')
			self.game.lampctrl.stop_show()
			# Remove attract mode from mode queue - Necessary?
			self.game.modes.remove(self)
			# Initialize game	
			self.game.start_game()
			# Add the first player
			self.game.add_player()
			# Start the ball.  This includes ejecting a ball from the trough.
			self.game.start_ball()
		else: 
			if not self.emptying_deadworld:
				self.game.set_status("Ball Search!")
				self.game.ball_search.perform_search(5)
				self.game.deadworld.perform_ball_search()
		return procgame.game.SwitchStop

	def check_deadworld_empty(self):
		if self.game.deadworld.num_balls_locked > 0:
			self.delay(name='deadworld_empty', event_type=None, delay=10, handler=self.check_deadworld_empty)
		else:
			self.emptying_deadworld = False
			
# Workaround to deal with latency of flipper rule programming.
# Need to make sure flippers deativate when the flipper buttons are
# released.  The flipper rules will automatically activate the flippers
# if the buttons are held while the enable ruler is programmed, but 
# if the buttons are released immediately after that, the deactivation
# would be missed without this workaround.
class FlipperWorkaroundMode(game.Mode):
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
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperLwLMain'].pulse(34)
	#		self.game.coils['flipperLwLHold'].pulse(0)

	def sw_flipperLwL_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperLwLMain'].disable()
			self.game.coils['flipperLwLHold'].disable()

	#def sw_flipperLwR_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperLwRMain'].pulse(34)
	#		self.game.coils['flipperLwRHold'].pulse(0)

	def sw_flipperLwR_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperLwRMain'].disable()
			self.game.coils['flipperLwRHold'].disable()

	#def sw_flipperUpL_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperUpLMain'].pulse(34)
	#		self.game.coils['flipperUpLHold'].pulse(0)

	def sw_flipperUpL_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperUpLMain'].disable()
			self.game.coils['flipperUpLHold'].disable()

	#def sw_flipperUpR_active(self, sw):
	#	if self.flipper_enable_workaround_active:
	#		self.game.coils['flipperUpRMain'].pulse(34)
	#		self.game.coils['flipperUpRHold'].pulse(0)

	def sw_flipperUpR_inactive(self, sw):
		if self.flipper_enable_workaround_active:
			self.game.coils['flipperUpRMain'].disable()
			self.game.coils['flipperUpRHold'].disable()


class BaseGameMode(game.Mode):
	"""Game play when no playable mode is active"""
	
	def __init__(self, game):
		super(BaseGameMode, self).__init__(game, 2)
		self.tilt = Tilt(self.game, 1000, font_jazz18, font_tiny7, 'tilt', 'slamTilt')
		self.flipper_enable_workaround_active = False

	def mode_started(self):
		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Do a quick lamp show
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)

		# Turn on the GIs
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)
		self.game.lamps.gi04.pulse(0)

		# Enable the flippers
		self.game.enable_flippers(enable=True)

		# Create jd_modes, which handles all of the game rules
		self.jd_modes = JD_Modes(self.game, 8, font_tiny7, font_jazz18)

		# Create mode to check for replay
		self.replay = procgame.modes.Replay(self.game, 18)
		self.game.modes.add(self.replay)
		self.replay.replay_callback = self.jd_modes.replay_callback
		self.jd_modes.replay = self.replay

		# Start modes
		self.game.modes.add(self.jd_modes)
		self.tilt.tilt_callback = self.tilt_callback
		self.tilt.slam_tilt_callback = self.slam_tilt_callback
		self.tilt.num_tilt_warnings = self.game.user_settings['Gameplay']['Number of tilt warnings']
		self.game.modes.add(self.tilt)

		# Load the player data saved from the previous ball.
		# It will be empty if this is the first ball.
		self.jd_modes.restore_player_state()
		if self.game.attract_mode.play_super_game:
			self.jd_modes.multiball.jackpot_collected = True
			self.jd_modes.crimescenes.complete = True
			self.jd_modes.modes_not_attempted = []
		self.jd_modes.begin_processing()

		# Put the ball into play and start tracking it.
		# self.game.coils.trough.pulse(40)
		# Always start the ball with no launch callback.
		self.game.trough.launch_balls(1, self.empty_ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0

		# In case a higher priority mode doesn't install it's own ball_drained
		# handler.
		self.game.trough.drain_callback = self.ball_drained_callback

	def empty_ball_launch_callback(self):
		pass

	def mode_stopped(self):
		# Ensure flippers are disabled
		self.game.enable_flippers(enable=False)

		# Deactivate the ball search logic so it won't search due to no 
		# switches being hit.
		self.game.ball_search.disable()

	def ball_drained_callback(self):
		if self.game.trough.num_balls_in_play == 0:
			# Give jd_modes a chance to do any ball processing
			self.jd_modes.ball_drained()
			# End the ball
			if self.tilt_status:
				self.tilt_delay()
			else:
				self.finish_ball()
		else:
			# Tell jd_modes a ball has drained (but not the last ball).
			self.jd_modes.ball_drained()

	def tilt_delay(self):
		# Make sure tilt switch hasn't been hit for at least 2 seconds before
		# finishing ball to ensure next ball doesn't start with tilt bob still
		# swaying.
		if self.game.switches.tilt.time_since_change() < 2:
			self.delay(name='tilt_bob_settle', event_type=None, delay=2.0, handler=self.tilt_delay)
		else:
			self.finish_ball()

	def finish_ball(self):
		self.game.sound.fadeout_music()

		# Make sure the motor isn't spinning between balls.
		self.game.coils.globeMotor.disable()

		# Remove the rules logic from responding to switch events.
		self.game.modes.remove(self.jd_modes)
		self.game.modes.remove(self.tilt)

		# save the player's data
		self.jd_modes.save_player_state()

		# Create the bonus mode so bonus can be calculated.
		self.bonus = Bonus(self.game, 8, font_jazz18, font_tiny7)
		self.game.modes.add(self.bonus)

		# Only compute bonus if it wasn't tilted away.
		if not self.tilt_status:
			self.bonus.compute(self.jd_modes.get_bonus_base(), self.jd_modes.get_bonus_x(), self.end_ball)
		else:
			self.end_ball()

	# Final processing for the ending ball.  If bonus was calculated, it is finished
	# by now.
	def end_ball(self):
		self.game.modes.remove(self.replay)
		# Remove the bonus mode since it's finished.
		self.game.modes.remove(self.bonus)
		# Tell the game object it can process the end of ball
		# (to end player's turn or shoot again)
		self.game.end_ball()

		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.

	def sw_startButton_active(self, sw):
		if self.game.ball == 1:
			if len(self.game.players) < 4:
				p = self.game.add_player()
				self.game.set_status(p.name + " added!")
		elif self.game.user_settings['Gameplay']['Allow restarts']:
			self.game.set_status("Hold for 2s to reset.")

	def sw_startButton_active_for_2s(self, sw):
		if self.game.ball > 1 and self.game.user_settings['Gameplay']['Allow restarts']:
			self.game.set_status("Reset!")

			# Need to build a mechanism to reset AND restart the game.  If one ball
			# is already in play, the game can restart without plunging another ball.
			# It would skip the skill shot too (if one exists). 

			# Currently just reset the game. This forces the ball(s) to drain and
			# the game goes to attrack mode. This makes it painfully slow to restart,
			# but it's better than nothing.
			self.game.reset()
			return procgame.game.SwitchStop

	# Allow service mode to be entered during a game.
	def sw_enter_active(self, sw):
		del self.game.service_mode
		self.game.service_mode = procgame.service.ServiceMode(self.game,100,font_tiny7,[self.game.deadworld_test])
		self.game.modes.add(self.game.service_mode)
		return procgame.game.SwitchStop

	# Outside of the service mode, up/down control audio volume.
	def sw_down_active(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return procgame.game.SwitchStop

	def sw_up_active(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return procgame.game.SwitchStop

	# Reset game on slam tilt
	def slam_tilt_callback(self):
		self.game.sound.fadeout_music()
		# Need to play a sound and show a slam tilt screen.
		# For now just popup a status message.
		self.game.reset()
		return True

	def tilt_callback(self):
		# Process tilt.
		# First check to make sure tilt hasn't already been processed once.
		# No need to do this stuff again if for some reason tilt already occurred.
		if self.tilt_status == 0:

			self.game.sound.fadeout_music()
			
			# Tell the rules logic tilt occurred
			self.jd_modes.tilt = True

			# Disable flippers so the ball will drain.
			self.game.enable_flippers(enable=False)

			# Make sure ball won't be saved when it drains.
			self.game.ball_save.disable()

			# Make sure the ball search won't run while ball is draining.
			self.game.ball_search.disable()

			# Ensure all lamps are off.
			for lamp in self.game.lamps:
				lamp.disable()

			# Kick balls out of places it could be stuck.
			if self.game.switches.shooterR.is_active():
				self.game.coils.shooterR.pulse(50)
			if self.game.switches.shooterL.is_active():
				self.game.coils.shooterL.pulse(20)
			self.tilt_status = 1
			#play sound
			#play video
	
	def sw_slingL_active(self, sw):
		self.game.score(100)

	def sw_slingR_active(self, sw):
		self.game.score(100)

class JDPlayer(game.Player):
	"""Keeps the progress of one player to allow the player
	   to resume where he left off in a multi-player game"""

	crimescenes = 0

	def __init__(self, name):
		super(JDPlayer, self).__init__(name)
		self.state_tracking = {}

	def setState(self, key, val):
		self.state_tracking[key] = val

	def getState(self, key, default = None):
		return self.state_tracking.get(key,default)


class JDGame(game.BasicGame):
	"""Judge Dredd pinball game"""
	
	def __init__(self):
		super(JDGame, self).__init__(pinproc.MachineTypeWPC)
		self.sound = procgame.sound.SoundController(self)
		self.lampctrl = procgame.lamps.LampController(self)
		self.logging_enabled = False
		self.shooting_again = False
		self.setup()
	
	def create_player(self, name):
		return JDPlayer(name)
	
	def save_settings(self):
		self.save_settings(settings_path)

	def save_game_data(self):
		super(JDGame, self).save_game_data(game_data_path)
		
	def setup(self):
		self.load_config('JD.yaml')
		self.load_settings(settings_template_path, settings_path)
		self.sound.music_volume_offset = self.user_settings['Machine']['Music volume offset']
		self.sound.set_volume(self.user_settings['Machine']['Initial volume'])
		self.load_game_data(game_data_template_path, game_data_path)
		
		logging.info("Stats:")
		logging.info(self.game_data)
		logging.info("Settings:")
		logging.info(self.settings)
		logging.info("Initial switch states:")
		for sw in self.switches:
			logging.info("  %s:\t%s" % (sw.name, sw.state_str()))

		self.balls_per_game = self.user_settings['Gameplay']['Balls per game']

		self.setup_ball_search()

		self.score_display.set_left_players_justify(self.user_settings['Display']['Left side score justify'])

		# Instantiate basic game features
		self.attract_mode = Attract(self)
		self.base_game_mode = BaseGameMode(self)
		self.flipper_workaround_mode = FlipperWorkaroundMode(self)
		self.deadworld = Deadworld(self, 20, self.settings['Machine']['Deadworld mod installed'])
		self.ball_save = procgame.modes.BallSave(self, self.lamps.drainShield, 'shooterR')

		trough_switchnames = []
		for i in range(1,7):
			trough_switchnames.append('trough' + str(i))
		early_save_switchnames = ['outlaneR', 'outlaneL']
		self.trough = procgame.modes.Trough(self,trough_switchnames,'trough6','trough', early_save_switchnames, 'shooterR', self.drain_callback)

		# Link ball_save to trough
		self.trough.ball_save_callback = self.ball_save.launch_callback
		self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
		self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

		self.deadworld_test = DeadworldTest(self,200,font_tiny7)

		# Setup and instantiate service mode
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7,[self.deadworld_test])
		
		asset_loader = AssetLoader(self)
		asset_loader.load_assets()
		self.animations = asset_loader.animations 
		
		# Setup fonts
		self.fonts = {}
		self.fonts['tiny7'] = font_tiny7
		self.fonts['jazz18'] = font_jazz18
		self.fonts['num_14x10'] = font_14x10
		self.fonts['18x12'] = font_18x12
		self.fonts['num_07x4'] = font_07x4
		self.fonts['07x5'] = font_07x5
		self.fonts['num_09Bx7'] = font_09Bx7

		self.lampshow_keys = ['attract0', 'attract1']

		# High Score stuff
		self.highscore_categories = []
		
		cat = highscore.HighScoreCategory()
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=500000,inits='GSS'),\
				  highscore.HighScore(score=400000,inits='ASP'),\
				  highscore.HighScore(score=300000,inits='JRP'),\
				  highscore.HighScore(score=200000,inits='JAG'),\
				  highscore.HighScore(score=100000,inits='JTW')]
		cat.game_data_key = 'ClassicHighScoreData'
		self.highscore_categories.append(cat)
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'CrimescenesHighScoreData'
		cat.scores = [highscore.HighScore(score=2,inits='GSS')]
		cat.titles = ['Crimescene Champ']
		cat.score_for_player = lambda player: player.crimescenes
		cat.score_suffix_singular = ' level'
		cat.score_suffix_plural = ' levels'
		self.highscore_categories.append(cat)
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'InnerLoopsHighScoreData'
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=2,inits='GSS')]
		cat.titles = ['Inner Loop Champ']
		cat.score_for_player = lambda player: player.getState('best_inner_loops', 0)
		cat.score_suffix_singular = ' loop'
		cat.score_suffix_plural = ' loops'
		self.highscore_categories.append(cat)

		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'OuterLoopsHighScoreData'
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=2,inits='GSS')]
		cat.titles = ['Outer Loop Champ']
		cat.score_for_player = lambda player: player.getState('best_outer_loops', 0)
		cat.score_suffix_singular = ' loop'
		cat.score_suffix_plural = ' loops'
		self.highscore_categories.append(cat)
		
		for category in self.highscore_categories:
			category.load_from_game(self)

		# Instead of resetting everything here as well as when a user
		# initiated reset occurs, do everything in self.reset() and call it
		# now and during a user initiated reset.
		self.reset()

	def reset(self):
		# Reset the entire game framework
		super(JDGame, self).reset()

		# Add the basic modes to the mode queue
		self.modes.add(self.attract_mode)
		self.modes.add(self.ball_search)
		self.modes.add(self.deadworld)
		self.modes.add(self.ball_save)
		self.modes.add(self.trough)
		self.modes.add(self.flipper_workaround_mode)

		self.ball_search.disable()
		self.ball_save.disable()
		self.trough.drain_callback = self.drain_callback

		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)

	# Empty callback just incase a ball drains into the trough before another
	# drain_callback can be installed by a gameplay mode.
	def drain_callback(self):
		pass

	# Override to create a flag signaling extra ball.
	def shoot_again(self):
		super(JDGame, self).shoot_again()
		self.shooting_again = True

	def ball_starting(self):
		super(JDGame, self).ball_starting()
		self.modes.add(self.base_game_mode)

	def end_ball(self):
		self.shooting_again = False
		super(JDGame, self).end_ball()

		self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
		self.game_data['Audits']['Balls Played'] += 1

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
		
	def ball_ended(self):
		self.modes.remove(self.base_game_mode)
		super(JDGame, self).ball_ended()

	def start_game(self):
		super(JDGame, self).start_game()
		self.game_data['Audits']['Games Started'] += 1
		
	def game_ended(self):
		super(JDGame, self).game_ended()
		# Make sure nothing unexpected happens if a ball drains
		# after a game ends (due possibly to a ball search).
		self.trough.drain_callback = self.drain_callback
		self.modes.remove(self.base_game_mode)
		#self.modes.add(self.attract_mode)
		self.deadworld.mode_stopped()
		# Restart attract mode lampshows

		# High Score Stuff
		seq_manager = highscore.EntrySequenceManager(game=self, priority=2)
		seq_manager.finished_handler = self.highscore_entry_finished
		seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
		seq_manager.ready_handler = self.highscore_entry_ready_to_prompt
		self.modes.add(seq_manager)

	def highscore_entry_ready_to_prompt(self, mode, prompt):
		self.sound.play_voice('high score')
		banner_mode = game.Mode(game=self, priority=8)
		markup = dmd.MarkupFrameGenerator()
		markup.font_plain = dmd.font_named('04B-03-7px.dmd')
		markup.font_bold = dmd.font_named('04B-03-7px.dmd')
		text = '\n[GREAT JOB]\n#%s#\n' % (prompt.left.upper()) # we know that the left is the player name
		frame = markup.frame_for_markup(markup=text, y_offset=0)
		banner_mode.layer = dmd.ScriptedLayer(width=128, height=32, script=[{'seconds':4.0, 'layer':dmd.FrameLayer(frame=frame)}])
		banner_mode.layer.on_complete = lambda: self.highscore_banner_complete(banner_mode=banner_mode, highscore_entry_mode=mode)
		self.modes.add(banner_mode)

	def highscore_banner_complete(self, banner_mode, highscore_entry_mode):
		self.modes.remove(banner_mode)
		highscore_entry_mode.prompt()

	def highscore_entry_finished(self, mode):
		self.modes.remove(mode)

		self.modes.add(self.attract_mode)

		#self.attract_mode.change_display(99)
		# setup display sequence in Attract.
		self.attract_mode.game_over_display()

		# Handle stats for last ball here
		self.game_data['Audits']['Avg Ball Time'] = self.calc_time_average_string(self.game_data['Audits']['Balls Played'], self.game_data['Audits']['Avg Ball Time'], self.ball_time)
		self.game_data['Audits']['Balls Played'] += 1
		# Also handle game stats.
		for i in range(0,len(self.players)):
			game_time = self.get_game_time(i)
			self.game_data['Audits']['Avg Game Time'] = self.calc_time_average_string( self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Game Time'], game_time)
			self.game_data['Audits']['Games Played'] += 1

		for i in range(0,len(self.players)):
			self.game_data['Audits']['Avg Score'] = self.calc_number_average(self.game_data['Audits']['Games Played'], self.game_data['Audits']['Avg Score'], self.players[i].score)
		self.save_game_data()

	def set_status(self, text):
		self.dmd.set_message(text, 3)
	
	def extra_ball(self):
		p = self.current_player()
		p.extra_balls += 1

	def getPlayerState(self, key, default = None):
		p = self.current_player()
		return p.getState(key, default)

	def setPlayerState(self, key, val):
		p = self.current_player()
		p.setState(key, val)

	def setup_ball_search(self):

		# Currently there are no special ball search handlers.  The deadworld
		# could be one, but running it while balls are locked would screw up
		# the multiball logic.  There is already logic in the multiball logic
		# to eject balls that enter the deadworld when lock isn't lit; so it 
		# shouldn't be necessary to search the deadworld.  (unless a ball jumps
		# onto the ring rather than entering through the feeder.)
		special_handler_modes = []
		self.ball_search = procgame.modes.BallSearch(self, priority=100, \
					 countdown_time=10, coils=self.ballsearch_coils, \
					 reset_switches=self.ballsearch_resetSwitches, \
					 stop_switches=self.ballsearch_stopSwitches, \
					 special_handler_modes=special_handler_modes)

	def enable_flippers(self, enable=True):
		super(JDGame, self).enable_flippers(enable)
		self.flipper_workaround_mode.enable_flippers(enable)
		
def main():
	game = None
	try:
	 	game = JDGame()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
