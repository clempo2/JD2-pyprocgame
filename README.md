## JD2-SkeletonGame

[JD2-SkeletonGame](https://github.com/clempo2/JD2-pyprocgame/tree/skel) is new software for the [Judge Dredd](https://www.ipdb.org/machine.cgi?id=1322) pinball machine written against [SkeletonGame](http://skeletongame.com/) running on a [P-ROC](https://www.multimorphic.com/store/circuit-boards/p-roc/) controller. It is a port of [JD2-pyprocgame](https://github.com/clempo2/JD2-pyprocgame) from [pyprocgame](http://pyprocgame.pindev.org/) to [SkeletonGameDMD](https://github.com/clempo2/SkeletonGameDMD), an unofficial fork of [SkeletonGame](https://github.com/mjocean/PyProcGameHD-SkeletonGame/tree/dev) that supports traditional monochrome DMDs. The goals are to reproduce the game faithfully running under SkeletonGameDMD, demonstrate the DMD support, and reduce the code size further.

## Status

The port is nearly complete. The game is now playable with some minor issues.

## Installation

- See the P-ROC Connection Diagram document in the doc directory for visual instructions how to install the P-ROC board in the Judge Dredd machine.  
- Run the all-in-one [SkeletonGame installer](http://skeletongame.com/step-1-installation-and-testing-the-install-windows/). This installs all the dependencies. JD2-SkeletonGame is not compatible with the official SkeletonGame release, so C:\P-ROC\PyProcGameHD-SkeletonGame-dev will not be used.  
- Copy the [SkeletonGameDMD dmd branch](https://github.com/clempo2/SkeletonGameDMD/tree/dmd) to C:\P-ROC\SkeletonGameDMD  
- Copy the [JD2-SkeletonGame skel branch](https://github.com/clempo2/JD2-pyprocgame/tree/skel) to C:\P-ROC\JD2-SkeletonGame  
- Install the [JD2-pyprocgame media kit](https://github.com/clempo2/JD2-pyprocgame-media). Follow and adapt the instructions in the media kit repository to extract the assets over the JD2-SkeletonGame skel branch. For example, after the installation you should have the directory C:\P-ROC\JD2-SkeletonGame\assets\sound  
- Edit config.yaml to comment out this line when using a real P-ROC
    ```
    #pinproc_class: procgame.fakepinproc.FakePinPROC # comment out this line when using a real P-ROC.
    ```
- Run these commands:
    ```
    cd C:\P-ROC\JD2-SkeletonGame  
    jd2.bat  
    ```
- If you have the Deadworld mod installed and would like to physically lock 2 balls, use the service buttons to go in the settings,  and change "Deadworld mod installed" to true. You only need to do this once.

JD2-SkeletonGame should also run on Linux but this has not been tested.

## Documentation

The rule sheet is located in .\doc\JD2-pyprocgame-rules.txt

## Authors

JD2-SkeletonGame is a collaboration of many people.

Game Play: Gerry Stellenberg  
Software: Adam Preble, Michael Ocean, Josh Kugler, Clement Pellerin  
Sound and Music: Rob Keller, Jonathan Coultan  
Dots: Travis Highrise  
Special Thanks to: Steven Duchac, Rob Anthony

## License

JD2-SkeletonGame is distributed under the MIT license.

JD2-SkeletonGame is  
Copyright (c) 2021-2022 Clement Pellerin

Original JD-pyprocgame is  
Copyright (c) 2009-2011 Adam Preble and Gerry Stellenberg

The JD-pyprocgame media kit is distributed under a restricted custom license.  
Copyright (c) 2011 Gerry Stellenberg  
JD-pyprocgame media kit used and repackaged by permission of the author.

PyProcGameHD-SkeletonGame is  
Copyright (c) 2014-2015 Michael Ocean and Josh Kugler
