###########################
4. Building the Headstage
###########################

MicroMAP uses a custom horizontal headstage designed to be low-cost and reduce torque on the animal's head. The system is compatible with two main headstage designs:

* **Texas Instruments (TI) ADS1298**
* **Intan RHD2000 family**

1. Fabrication
==============

* **Get PCB Designs**: The printed circuit board (PCB) designs, created in **KICAD 8**, are available on the project's GitHub.
* **Fabricate PCBs**: Fabricate the main headstage PCB based on the KiCAD files.
* **Fabricate Connector Plug**: A flat connector plug, implemented as a double-sided PCB, is also required. This design uses plated through-holes for soldering the electrodes.

2. Assembly
===========

* **Attach ADC**: The ADC (e.g., ADS1298 or RHD) is attached to the **top layer** of the headstage PCB.
* **Attach Socket**: A 20-pin connector socket is attached to the **bottom layer** of the PCB. This socket interfaces with the flat connector plug.

Refer to Figure 2A (ADS) and 2B (RHD) for 3D renderings and circuit schematics of the headstages.