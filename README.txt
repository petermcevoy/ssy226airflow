### Airflow calibration tool ###
Code part of the project for SSY226.
2018 by Peter McEvoy, Henrik Eriksson, Yanda Shen.



This repositroy contains a python application with a GUI that allows user 
control of the calibration platform developed during this project course.

The GUI app internally uses the Galil python module and c library (gclib) in
order to communicate with the controller. The gui has options for loading a 
trajectory, either artifically generated trajectories or arbitry data imported 
via CSV. The software also handles measurment of the motors encoder position.
Both the genrated and measured positions can be exported as a CSV for further
analysis.

# Setup
    (We prepared the environmet in a virtual machine)
    Install requirements:
        Python 3
            modules:    PyQt5
                        pyqtgraph
                        numpy
        Galil C library (gclib http://www.galilmc.com/downloads/api)
        Properly setup network interface for galil controller (see our manual).

        To modify the user interface, open the .ui files in QtCreator.

    Start the app by running thte main.py script in the frontend folder:
        >> python3 frontend/main.py

# Basic usage
    - Connect to controller
        The GUI assumes that the controller is connected via Ethernet.
        To connect to the controller press File > Connect.
        Fill in the appropriate IP address for the controller, set during the 
        setup process for the network interface for the controller (see 
        Galil Design Kit). When connected a message will appear at the bottom 
        of the window.
    - To generate a new signal
        Select signal type in drop down and specify amplitude frequency and
        duration when applicable. Then press Generate.
    - Send target curve to controller
        - By pressing Start, the software will initialze the controller/motor,
        this often causes to linear motor to jolt a short distance in order to 
        localize itself. This might fail if the load is too much for the motor.
        - Once this is done a message will appear, telling you to move the piston
        in to the zero position. This zero position corresponds to zero in 
        the generated position curve.
        WARNING: Make sure that there is enough room from the zero position to
        perform the movement.
        - When the piston has been moved (by hand) to the zero position, 
        Press Ok. The movement will now start.
        - Once complete. The measured encoder position and value of the ADC will
        be plotted.
    - Exporting.
        File > Export CSV
    - Recording
        The text-field in front of the record button specifies the frequency at
        wich the encoder position and ADC values should be recorded.
        Tested range is 20-100Hz.
        Pressing record will sample the position encoder and ADC and plot the 
        result without moving the motor.
        


