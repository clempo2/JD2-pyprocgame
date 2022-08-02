## JD2-SkeletonGame

[JD2-SkeletonGame](https://github.com/clempo2/JD2-SkeletonGame) is new software for the [Judge Dredd](https://www.ipdb.org/machine.cgi?id=1322) pinball machine written against [SkeletonGame](http://skeletongame.com/) running on a [P-ROC](https://www.multimorphic.com/store/circuit-boards/p-roc/) controller. It is a port of [JD2-pyprocgame](https://github.com/clempo2/JD2-pyprocgame) from [pyprocgame](http://pyprocgame.pindev.org/) to SkeletonGame dated August 2022 or newer. The goal is to reproduce the game faithfully running under SkeletonGame and test the newly added support for low-resolution monochrome DMDs.

## Status

The port is on-going and the code does not work yet.

## Installation

- See the P-ROC Connection Diagram document in the doc directory for visual instructions how to install the P-ROC board in the Judge Dredd machine.  
- Run the all-in-one [SkeletonGame installer](http://skeletongame.com/step-1-installation-and-testing-the-install-windows/).
- Copy the [JD2-SkeletonGame skel branch](https://github.com/clempo2/JD2-SkeletonGame/tree/skel) to C:\P-ROC\JD2-SkeletonGame  
- Install the [JD2-pyprocgame media kit](https://github.com/clempo2/JD2-pyprocgame-media). Follow and adapt the instructions in the media kit repository to extract the assets over the JD2-SkeletonGame skel branch.  
- Edit config.yaml to comment out this line when using a real P-ROC
    ```
    #pinproc_class: procgame.fakepinproc.FakePinPROC # comment out this line when using a real P-ROC.
    ```
- Run these commands:
    ```
    cd C:\P-ROC\JD2-SkeletonGame  
    python jd2.py
    ```
- If you have the Deadworld mod installed and would like to physically lock 2 balls, use the service buttons to go in the settings and change "Deadworld mod installed" to true. You only need to do this once.

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
JD-pyprocgame media pack used by permission of the author.

PyProcGameHD-SkeletonGame is  
Copyright (c) 2014-2015 Michael Ocean and Josh Kugler
