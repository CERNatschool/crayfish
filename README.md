# Crayfish

Crayfish is a visualisation and analysis tool for frames produced by the Medipix family of particle detectors.

## Features

#### Visualisation
- 2D heat map of pixel count.
- Enlarged heat map of selected particle trace.

#### Analysis
- Automatic clustering of pixels corresponding to a single particle trace.
- Statistical information about the selected frame or particle trace.
- Ability to view an aggregate of all frames in a folder, including those in sub folders.

#### Classification
- Run classification algorithms on particle traces, in order to determine the type of particle incident.
- Manually classify particle traces, and then save these in a training data file for use in machine learning algorithms.

#### Graph Plotting
- Plot histograms of particle trace properties or properties against each other in a scatter plot.
- Colour data points/data bars by particle trace class (either the manually or algorithmically assigned class).

#### Extensibility
- Easy to use attribute system which makes adding statistical functions as simple as writing a function - no knowledge of the code base required!
- Attributes can then be viewed in the interface, plotted on graphs or used in classification algorithms.
- Similar system for classification algorithms.
- Written in Python - a language which has both powerful features and scientific libraries available, yet is easy to learn for novice programmers.

## Dependencies

#### Application
- Python 2.7
- wxPython 2.9
- matplotlib 1.2

#### Documentation Generation (Optional)
- Sphinx 1.2
- Graphviz 2.30 (for inheritance diagrams, may be omitted)

Crayfish may work with older versions, but this is neither tested or supported.

## Installation and Usage

Currently dependencies must be installed manually.

Once dependencies are installed clone this repository and run the
application using the following command:

    python crayfish/crayfish.py

You can generate the developer documentation using Sphinx. Currently
this is little more than a convenient way to view docstrings.

    cd docs
    make html

## User Guide

The user guide will be uploaded shortly.

## Acronym

The name Crayfish originally came from the acroynm **C**omprehensive **RAY**
**F**rame **I**nspection, **S**tatistics and **H**euristics. _Comprehensive_ and _RAY_ are in reference to projects using Medipix detectors whose requirements led to the development of this software.
