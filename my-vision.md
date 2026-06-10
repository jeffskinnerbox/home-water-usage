
# Household Daily Water Usage
My city water provider sends me a daily email stating my homes water usage.
I receive this daily email at my Gmail account `waterusagejirland@gmail.com`.
That email has the following example format:

```text
title:    Water Usage Notification
from:     <no-reply@leesburgva.gov>
to:       <waterusagejirland@gmail.com>
date:     Jun 9, 2026, 11:02 AM
subject:  Water Usage Notification
body:     On June 06, 2026, your water usage of 359 exceeded your threshold of 10 for account 40002423000.
```

I want to create a commandline Python utility that will create a graph of household water usage.
This solution will log into my gmail account and pull the required emails to make the graph.

## Key Features to be Built
These are the key features I expect the solution to have:
1. Solution Name - The commandline Python utility should be call `home-water-usage.py`
1. Default Parameter Values - All titles, fonts, line color & widths & types, graph dimensions, directory location for temporary files,
   true/false options for things like deletion of temporary file, etc. will have default values located in a single file called `parameter_values.yaml`
1. Commandline Parameters - All "Default Parameter Values" can be overridden via a Python commandline parameter.
1. Data Gathering - pull from the gmail account required emails, parse the data needed, and place the data in a temporary file.
   The date that should be plot is in the email body, NOT the date the email was received.
   When pulling the emails, pull three extra emails before and after the dates requested.
1. Time Interval - provide me a line graph of daily water usage over a specified time interval.
1. Usage Averages - superimpose on that graph will be horizontal dotted lines of annual, winter, spring, summer, fall usage averages.
1. Graph Titles - title of graphs left column is "Household Water Usage" and title of graphs bottom row "Date" and title of whole graph is "Household Water Usage"
1. Data Display - The graph will be a pop-up window and a optional PDF of the graph.

## Core Principles
These items are very important and should be placed in the `constitution.md` file:
* Solution should be written in Python and run in a Linux terminal window.
* The solution must be information rich for the user but nicely formatted & visually appealing.
* Using color ASCII characters to display the progress & status of the program. Show status at all steps in the workflow.
* If the solution fails or errors, the solution must write a clear description and likely root cause of the failure/error.
* The solutions default look & feel (colors, sizes, fonts, etc.) & behavior (thresholds, animation speed, etc.)
  need to be configurable in the `parameter_values.yaml` file.
* Use a Test-Driven Development (TDD) process using such things as `pytest` and `unnitest`.

## Core Software Components
These items are very important and should be placed in the `constitution.md` file:
* All coding should be in Python, and when needed, Bash
* Python `uv` workflow should be used.
* Use the Seaborn libraries for the graph

## Core Hardware Components
These items are very important and should be placed in the `constitution.md` file:
* There is no special hardware components for this solution.  Everything should run in a Linux terminal session.

## How to Use `my-vision.md`
Using the this `my-vision.md` file,
create for me a product requirements document (PRD) call `PRD.md` using the skills `/prd-generator`.
Also use the skill `/grill-me` to ask me any clarifying questions concerning the PRD.

```


