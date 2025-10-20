###########################
3. Building the MicroMAP
###########################

This section describes the assembly of the MicroMAP enclosure, which houses the core components.

1. 3D Printing the Enclosure
============================

The system is housed in a custom enclosure ($140~mm \times 65~mm \times 67~mm$).

* **Get 3D Models**: All 3D models are available on the project's GitHub.
* **Print**: Fabricate the enclosure from PLA plastic using a 3D printer.

2. Component Assembly
=====================
The enclosure is designed to house the **Arduino Due** and a **Raspberry Pi** (RPi).

* Install the Arduino Due and RPi into their designated slots in the 3D-printed case.
* (Optional) A fan can be added for cooling, powered by the RPi's 5V and ground pins.

3. Wiring
=========

The system requires wiring between the Arduino and an external connector (e.g., RJ45) to interface with the headstage.

* **RHD Headstage**: Requires an 8-contact RJ45 connector, using 6 terminals.
* **ADS Headstage**: Requires a 12-contact connector or similar interface.

Refer to Figure 1A and Supplementary Table 2 in the manuscript for detailed wiring schemes between the Arduino and the headstage connector.

Finally, connect the Arduino ground to a pin fixed to the enclosure to ensure proper grounding.