#################################
1. Installing Python and MicroMAP
#################################

The MicroMAP system uses a cross-platform Graphical User Interface (GUI) developed in Python 3.12 with the PyQt5 library. This GUI runs on a host computer or a microcomputer like a Raspberry Pi.

Prerequisites
=============

* Python 3.12 or newer
* Git (for cloning the repository)

Installation Steps
==================

1.  **Download the Software**

    First, download the software from the official GitHub repository.

    .. code-block:: bash

        $ git clone https://github.com/nnc-ufmg/micromap.git
        $ cd micromap

2.  **Install Dependencies**

    The GUI requires specific Python dependencies to run. Install them using the provided requirements file (assumed to be on GitHub). The primary dependency is PyQt5.

    .. code-block:: bash

        $ pip install -r requirements.txt 

3.  **Run the GUI**

    Once dependencies are installed, you can run the program from an IDE or directly via the command line.

    .. code-block:: bash

        $ python interface_visual.py