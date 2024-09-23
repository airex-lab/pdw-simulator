
---

# PDW Simulator for Project CAESAR

This repository contains a **Pulse Descriptor Word (PDW) Simulator** designed for the project CAESAR. The simulator models radar signals in a 2D environment and generates PDWs along with the corresponding "truth" data. 

## Overview

The PDW Simulator allows users to input specific **scenarios** and produce Pulse Descriptor Words, which encapsulate key radar signal parameters such as amplitude, frequency, pulse width, time of arrival (TOA), and angle of arrival (AOA). The generated PDWs can be used for testing machine learning models, replacing rule-based systems in radar classification tasks.

### Input

- **Scenario Geometry:** : The Scenario geometry is defined by the sensor and radar positions and movements
- **Radar Properties** : Customisable properties that a radar will possess
    Radar Properties are as follows:
    1. Rotation Period
    2. Radar antenna lobe pattern
    3. PRI
    4. Frequency
    5. Pulse width
- **Sensor Properties** Customisable properties that a sensor will possess
  
## Workflow


=======
```mermaid
graph TD;
    Input(Scenario) --> Simulator(PDW Simulator);
    Simulator --> Output(Pulse Descriptor Words + "Truth");
```

1. **Input (Scenario):** Users define a scenario, including radar, sensor, and geometric properties.
2. **PDW Simulator:** Processes the input and simulates radar pulses.
3. **Output:** Generates PDWs along with corresponding ground truth for further analysis or model training.

## To-Do List

### Classes to Implement

- **Scenario Geometry:**
- **Radar Properties:** 
- **Sensor Properties:**

### Assumptions

- The PDW Simulator operates in a **2D environment**.
  

## Paper Reference

please refer to the paper [link](https://ffi-publikasjoner.archive.knowledgearc.net/bitstream/handle/20.500.12242/970/13-00048.pdf).
