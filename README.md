## JD2-pyprocgame

JD2-pyprocgame is new software for the [Judge Dredd](https://www.ipdb.org/machine.cgi?id=1322) pinball machine written against [pyprocgame](http://pyprocgame.pindev.org/) running on a [P-ROC](https://www.multimorphic.com/store/circuit-boards/p-roc/) controller. It is a more polished version of [JD-pyprocgame](https://github.com/preble/JD-pyprocgame) by Gerry Stellenberg et al. The goal is to achieve near commercial quality while minimizing the amount of code. The rules are nearly identical to JD-pyprocgame with minimal changes dictated by bug fixing.

## Status

JD2-pyprocgame is mature. Visit [JD2-SkeletonGame](https://github.com/clempo2/JD2-SkeletonGame) for the continuation of this project.

## Installation

- See the P-ROC Connection Diagram document in the doc directory for visual instructions how to install the P-ROC board in the Judge Dredd machine.  
- Install Python 2.7 and supporting libraries. The easiest is to run the all-in-one [SkeletonGame installer](http://skeletongame.com/step-1-installation-and-testing-the-install-windows/). Note JD2-pyprocgame is not compatible with SkeletonGame, that portion of the all-in-one installation can be ignored afterwards.  
- Copy the [pyprocgame dev branch](https://github.com/preble/pyprocgame/tree/dev) to C:\P-ROC\pyprocgame-dev
- Edit C:\P-ROC\pyprocgame-dev\procgame\dmd\animation.py, delete line 8 to fix a compilation error.
    ```
    import Image
    ```
- Copy the [JD2-pyprocgame dev2 branch](https://github.com/clempo2/JD2-pyprocgame/tree/dev2) to C:\P-ROC\JD2-pyprocgame  
- Install the [JD2-pyprocgame media kit](https://github.com/clempo2/JD2-pyprocgame-media). Follow the instructions in the media kit repository to extract the assets over the JD2-pyprocgame dev2 branch.  
- Edit config.yaml to comment out this line when using a real P-ROC
    ```
    #pinproc_class: procgame.fakepinproc.FakePinPROC # comment out this line when using a real P-ROC.
    ```
- Run these commands:
    ```
    cd C:\P-ROC\JD2-pyprocgame    
    jd2.bat
    ```
- If you have the Deadworld mod installed and would like to physically lock 2 balls, use the service buttons to go in the settings and change "Deadworld mod installed" to true. You only need to do this once.

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

The JD-pyprocgame media kit is distributed under a restricted custom license.  
Copyright (c) 2011 Gerry Stellenberg  
JD-pyprocgame media pack used by permission of the author.

Small portions copied from [PyProcGameHD-SkeletonGame](https://github.com/mjocean/PyProcGameHD-SkeletonGame) are  
Copyright (c) 2014-2015 Michael Ocean and Josh Kugler
