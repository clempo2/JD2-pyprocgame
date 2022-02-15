## JD2-pyprocgame

JD2-pyprocgame is new software for the [Judge Dredd](https://www.ipdb.org/machine.cgi?id=1322) pinball machine written against [pyprocgame](http://pyprocgame.pindev.org/) running on a [P-ROC](https://www.multimorphic.com/store/circuit-boards/p-roc/) controller. It is a more polished version of [JD-pyprocgame](https://github.com/preble/JD-pyprocgame) by Gerry Stellenberg et al. The goal is to achieve near commercial quality while minimizing the amount of code. The rules are nearly identical to JD-pyprocgame with minimal changes dictated by bug fixing.

In honnor of JD-pyprocgame, the first version of JD2-pyprocgame will be 2.0

## Installation

The easiest is to run the all-in-one [SkeletonGame installer](http://skeletongame.com/step-1-installation-and-testing-the-install-windows/) to install Python 2.7 and supporting libraries. Note JD2-pyprocgame is not compatible with SkeletonGame, that portion of the all-in-one installation can be ignored afterwards.

Copy the pyprocgame dev branch to C:\P-ROC\pyprocgame-dev  
Copy the JD2-pyprocgame dev2 branch to C:\P-ROC\JD2-pyprocgame-dev2  
Install the JD-pyprocgame media pack in C:\P-ROC\JD2-pyprocgame-dev2\assets

Edit config.yaml to comment out this line when using a real P-ROC  
#pinproc_class: procgame.fakepinproc.FakePinPROC # comment out this line when using a real P-ROC. 

set PYTHONPATH=C:\P-ROC\JD-pyprocgame-dev2;C:\P-ROC\pyprocgame-dev;C:\P-ROC\pypinproc-dev;C:\Python27\DLLs;C:\Python27\lib;C:\Python27\lib\lib-tk;C:\Python27;C:\Python27\lib\site-packages;C:\Python27\lib\site-packages\win32;C:\Python27\lib\site-packages\win32\lib;C:\Python27\lib\site-packages\Pythonwin;C:\Python27\lib\site-packages\wx-3.0-msw  
cd C:\P-ROC\JD2-pyprocgame-dev2  
python jd2.py

JD2-pyprocgame should also run on Linux but this has not been tested.

## Documentation

The rule sheet is located in .\doc\JD2-pyprocgame-rules.txt

## Authors

JD2-pyprocgame is a collaboration of many people.

Game Play: Gerry Stellenberg  
Software: Adam Preble, Clement Pellerin  
Sound and Music: Rob Keller, Jonathan Coultan  
Dots: Travis Highrise  
Special Thanks to: Steven Duchac, Rob Anthony, Michael Ocean, Josh Kugler

## License

JD2-pyprocgame is distributed under the MIT license.

JD2-pyprocgame is  
Copyright (c) 2021-2022 Clement Pellerin

Original JD-pyprocgame is  
Copyright (c) 2009-2011 Adam Preble and Gerry Stellenberg

The JD-pyprocgame media pack is distributed under a restricted custom license.  
Copyright (c) 2009-2011 Gerry Stellenberg  
JD-pyprocgame media pack used by permission of the author.

Small portions copied from [PyProcGameHD-SkeletonGame](https://github.com/mjocean/PyProcGameHD-SkeletonGame) are  
Copyright (c) 2014-2015 Michael Ocean and Josh Kugler

