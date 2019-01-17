import sys
#from ui.MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QGridLayout, QWidget, QComboBox
from PyQt5 import QtWidgets, QtCore
from PyQt5 import QtGui, uic

from ui.CustomSignalWidget import CustomSignalWidget
from ui.ConnectDialog import ConnectDialog

import pyqtgraph as pg
import numpy as np

from datetime import datetime
import time

import gclib # galil python module

SYSTEM_MAGNETIC_PITCH = 24      #24 mm per encoder cycle
SYSTEM_STEPS_PER_CYCLE = 4096   
SYSTEM_STEPS_PER_MM = SYSTEM_STEPS_PER_CYCLE/SYSTEM_MAGNETIC_PITCH
SYSTEM_MAX_STEPS = int(110*SYSTEM_STEPS_PER_MM)  #Do not allow acutator to move more than 120 mm from home.
SYSTEM_MIN_STEPS = -10    #Do not allow acutator to move below 0 mm from home.
SYSTEM_GENERATE_SAMPLE_RATE = 250    # Sample rate at which to genreate and control
SYSTEM_MAX_DISPLACEMENT_PER_SAMPLE = 10000  # Set a limit to how much we can move in 1/250 = 4ms.

class ControllerRecordThread(QtCore.QThread):
    signal = QtCore.pyqtSignal('PyQt_PyObject')
    recording = False;
    #frequency = 100; #Hz
    galil_handle = None;

    def __init__(self, ip_address=None, frequency=100, duration=2):
        QtCore.QThread.__init__(self)
        self.frequency = frequency
        self.duration = duration

        # Caller is responsible to make sure that ip address is ok
        self.galil_handle = gclib.py();
        try:
            self.galil_handle.GOpen('%s --direct -s ALL' % ip_address)
        except gclib.GclibError:
            print("ERROR: recording thread uanble to connect to controller")


    def run(self):
        print('Recording Thread running...')
        nsamples = int(self.duration*self.frequency)
        start_timestamp = datetime.now()
        
        pos_timestamps = np.zeros(nsamples)
        pos_values = np.zeros(nsamples)

        analog1_timestamps = np.zeros(nsamples)
        analog1_values = np.zeros(nsamples)

        analog2_timestamps = np.zeros(nsamples)
        analog2_values = np.zeros(nsamples)

        for i in range(0,nsamples):
            t1 = datetime.now()
            pos_timestamps[i] = (datetime.now() - start_timestamp).total_seconds()
            pos_values[i] = float(self.galil_handle.GCommand('TP'))
            
            analog1_timestamps[i] = (datetime.now() - start_timestamp).total_seconds()
            analog1_values[i] = float(self.galil_handle.GCommand('MG @AN[1]'))
            
            #analog2_timestamps[i] = (datetime.now() - start_timestamp).total_seconds()
            #analog2_values[i] = float(self.galil_handle.GCommand('MG @AN[2]'))
            
            t2 = datetime.now()
            exec_time = t2 - t1
            time.sleep(1.0/self.frequency - exec_time.total_seconds())
        
        data = {
                'pos_timestamps': pos_timestamps,
                'pos_values': np.array(pos_values)/SYSTEM_STEPS_PER_MM,
                'analog1_timestamps': np.array(analog1_timestamps),
                'analog1_values': np.array(analog1_values),
                'analog2_timestamps': np.array(analog2_timestamps),
                'analog2_values': np.array(analog2_values),
        }
        self.signal.emit(data)

class MainWindow(QMainWindow):
    legend = None;
    galil_handle = None;
    galil_ip = None;
    recording_thread = None;
    generated_curve = [];
    timestamp_generated_curve = [];
    plot_position = None;
    plot_analog_input = None;
    latest_record_data = None;

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/MainWindow.ui', self)
        self.show()

        image = QtGui.QImage(100, 100, QtGui.QImage.Format_Mono)
        image.fill(0)
        
        l = pg.GraphicsLayout()
        self.plotView.setCentralItem(l)
        self.plotView.show()

        self.plot_position = l.addPlot(0,0)
        self.plot_analog_input = l.addPlot(1,0)

        self.plot_position.setTitle('Position') 
        self.plot_position.setLabel('left', 'Position [mm]')
        self.plot_position.setLabel('bottom', 'Time [s]')

        self.plot_analog_input.setTitle('Analog input') 
        self.plot_analog_input.setLabel('left', 'Voltage [V]')
        self.plot_analog_input.setLabel('bottom', 'Time [s]')

        self.plot_position.addLegend()
        self.plot_analog_input.addLegend()

        # Setup signals and slots
        self.generateButton.clicked.connect(self.generate_curve)
        self.clearButton.clicked.connect(self.clear_plots)
        self.startButton.clicked.connect(self.start_motion)
        self.stopButton.clicked.connect(self.stop_motion)
        self.signalGenTypeComboBox.currentTextChanged.connect(self.change_signal_widget)
        self.recordButton.clicked.connect(self.record_position)
        
        self.customGen.browseFileButton.clicked.connect(self.customGen.browse_file)
       
        self.actionConnect.triggered.connect(self.open_connect_dialog)
        self.actionExport_CSV.triggered.connect(self.export_csv)


    def open_connect_dialog(self):
        connect_dialog = ConnectDialog(self)
        if (connect_dialog.exec() == QtWidgets.QDialog.Accepted):
            # Make a please wait message
            waitmsg_box = QtWidgets.QMessageBox(self)
            waitmsg_box.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            waitmsg_box.setWindowTitle("Connecting....");
            waitmsg_box.setText('Connecting...');
            waitmsg_box.show();
            QApplication.processEvents();


            if self.galil_handle is not None:
                self.galil_handle.GClose()

            self.galil_handle = gclib.py();
            print('Initialized gclib version:', self.galil_handle.GVersion())
            
            # Try to connect to controller.
            ip_address = connect_dialog.ipLineEdit.text()
            try:
                self.galil_handle.GOpen('%s --direct -s ALL' % ip_address)
                self.ip_address = ip_address
                #print('placeholder')
            except gclib.GclibError:
                waitmsg_box.close()
                errorstr = 'Error: Unable to connect to controller.'
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setText(errorstr);
                msg_box.exec();
                return;

            waitmsg_box.close()
            self.statusbar.showMessage('Connected to %s.' % ip_address)

            print(self.galil_handle.GInfo())
            print('accepted!')

    def clear_plots(self):
        self.plot_position.legend.scene().removeItem(self.plot_position.legend)
        self.plot_position.clear()
        self.plot_position.addLegend()
        
        self.plot_analog_input.legend.scene().removeItem(self.plot_analog_input.legend)
        self.plot_analog_input.clear()
        self.plot_analog_input.addLegend()

    def export_csv(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save File", "", "CSV (*.csv)");
        if filename[0] != '':
            arr = np.asarray([ 
                self.timestamp_generated_curve,
                self.generated_curve, 
                self.latest_record_data['pos_timestamps'],
                self.latest_record_data['pos_values'],
                self.latest_record_data['analog1_timestamps'],
                self.latest_record_data['analog1_values']
                ])
            max_len = np.max([len(a) for a in arr])
            arr = np.asarray([np.pad(a, (0, max_len - len(a)), 'constant', constant_values=0) for a in arr]).T
            np.savetxt(filename[0], arr, delimiter=",", header="'Timestamp Control signal', Control signal', 'Timestamp Encoder position', 'Encoder position', 'Timestamp Input 1', 'Input 1'")

    def change_signal_widget(self):
        current_signal_type = self.signalGenTypeComboBox.currentText()
        if current_signal_type == "From CSV":
            self.signalGenStackedWidget.setCurrentIndex(1)
        else: 
            self.signalGenStackedWidget.setCurrentIndex(0)

    def controller_init(self):
        if self.galil_handle is None:
            alert('Controller not connected', 'Error: There is no connection to the controller.');
            return False

        #TODO Tell user to put syringe in start position.

        self.galil_handle.GCommand('AB')        # Abort motion and program
        self.galil_handle.GCommand('MO')        # Turn of all motors
        self.galil_handle.GCommand('AF12')      # Set resolution sin/cos encoder
        self.galil_handle.GCommand('BM 4096')   # Set magnetic modulus (tau).
        self.galil_handle.GCommand('KP 150')
        self.galil_handle.GCommand('KI 0')
        self.galil_handle.GCommand('KD 0')
        self.galil_handle.GCommand('TL 5')      # current limit (1A)/(0.2A/V) = 5 V -> (TL n=5)
        self.galil_handle.GCommand('TK 8')      # torque limit (2A)/(0.2A/V) = 10 V -> (TK n=10)
        self.galil_handle.GCommand('OE 1')      # motor off on error
        self.galil_handle.GCommand('MT 1')      # motor type
        self.galil_handle.GCommand('LC 1')      # reduce holding current
        self.galil_handle.GCommand('AC 20000')  # Acceleration
        self.galil_handle.GCommand('DC 20000')  # Decceleration
        self.galil_handle.GCommand('DC 18000')  # Speed
        self.galil_handle.GCommand('IT .2')     # Motion smoothing
        self.galil_handle.GCommand('BAA')       # Specify A - axis for sinusoidal	 commutation
        self.galil_handle.GCommand('BMA = %d' % SYSTEM_STEPS_PER_CYCLE) # Specify counts/magnetic cycle
        self.galil_handle.GCommand('BZA = 4')   # Commutate motor using 3V
        
        #TODO Tell user to put syringe in start position.
        alert('Home position', 'Please put motor in home position.');
        self.galil_handle.GCommand('DP 0')      # Define 0 pos
        #self.galil_handle.GCommand('SHA')       # Initialize motor A
        
        #self.galil_handle.GCommand('PRA = 4096')
        #self.galil_handle.GCommand('BGA')

        return True

    def start_motion(self):
        self.controller_init()
        # Use contour mode on the galil controller.
        # Sample our signal at an appropriate rate and set the 
        # position waypoints. See page 79 in the DMC manual.

        self.galil_handle.GCommand('SHA')       # Initialize motor A

        if not self.generated_curve:
            alert('No curve to follow', 'Error: There is no curve to follow.')
            return False;
        
        values = self.generated_curve

        #move to initial position
        old_absolute_steps = int(values[0]*SYSTEM_STEPS_PER_MM);
        if old_absolute_steps < SYSTEM_MIN_STEPS or old_absolute_steps > SYSTEM_MAX_STEPS:
            errorstr = 'Error: Control step is out of bounds %d (%g mm). Halting.' % (absolute_steps, absolute_steps/SYSTEM_STEPS_PER_MM);
            print(errorstr);
            alert('Error: Out of bounds', errorstr)
            self.stop_motion()
            return False;

        self.galil_handle.GCommand('SPA=2000') # set speed
        self.galil_handle.GCommand('PRA=%d' % old_absolute_steps) # move to inital position
        self.galil_handle.GCommand('BG A') # Start motion
        print('start pre motion')
        self.galil_handle.GMotionComplete('A')
        print('end pre motion')
        
        self.galil_handle.GCommand('CM A') # set contouring mode on A (this resets the contouring buffer)
        self.galil_handle.GCommand('DT -1') # Pause to allow buffer to fill
        prebuffer = True;

        nsamples = len(values)
        for i in range(0,nsamples):
            if (prebuffer and (i > 100 or i >= nsamples)):
                print('Resuming contour i: %d' % i)
                prebuffer = False;
                self.galil_handle.GCommand('DT 2')
                self.record_position()

            absolute_steps = int(values[i]*SYSTEM_STEPS_PER_MM)
            steps_to_move = absolute_steps - old_absolute_steps
            old_absolute_steps = absolute_steps

            # Saftey checks!
            if absolute_steps < SYSTEM_MIN_STEPS or absolute_steps > SYSTEM_MAX_STEPS:
                errorstr = 'Error: Control step is out of bounds %d (%g mm). Halting.' % (absolute_steps, absolute_steps/SYSTEM_STEPS_PER_MM);
                print(errorstr);
                alert('Error: Out of bounds', errorstr)
                self.stop_motion()
                return False;

            if steps_to_move > SYSTEM_MAX_DISPLACEMENT_PER_SAMPLE:
                errorstr = 'Error: Control step is too fast %d steps in 4ms (%g mm/s). Halting.' % (steps_to_move, steps_to_move/SYSTEM_STEPS_PER_MM);
                print(errorstr);
                alert('Error: Speed limit', errorstr)
                self.stop_motion()
                return False;
            
        
            if (int(self.galil_handle.GCommand('CM?')) > 509):
                print('buffer starved (i = %d): %s' % (i, self.galil_handle.GCommand('CM?')))

            while (int(self.galil_handle.GCommand('CM?')) < 10):
                # buffer full
                print('buffer full')

                time.sleep(0.1); # Wait until more of buffer has been consumed.
                
            self.galil_handle.GCommand('CD %d' % steps_to_move) # Add to buffer

        # wait until motion is done.
        while (int(self.galil_handle.GCommand('CM?')) < 511):
            print('waiting to complete: %s' % self.galil_handle.GCommand('CM?'))
            time.sleep(0.1); 
        
        print('motion done.')
        self.stop_motion()
    
    def stop_motion(self):
        self.galil_handle.GCommand('AB')
        self.galil_handle.GCommand('MO')
        
    def record_finished(self, result):
        print('Finished recording: %s' % str(result))
        self.latest_record_data = result;
        self.plot_position.plot(result['pos_timestamps'], result['pos_values'], name = 'Measured position', pen='r', symbol='+')
        self.plot_analog_input.plot(result['analog1_timestamps'], result['analog1_values'], name = 'Analog input 1', pen='y')
        #self.plot_analog_input.plot(result['analog2_timestamps'], result['analog2_values'], name = 'Analog input 2', pen='y')
        
    def record_position(self):
        #self.controller_init()
        frequency = self.sampleFrequencySpinBox.value()
        duration = 2.0
        if self.generated_curve == False: 
            duration = len(self.generated_curve)/SYSTEM_GENERATE_SAMPLE_RATE

        # TODO: Setup a thread to continously pull the current encoder position according to frequency.
        self.recording_thread = ControllerRecordThread(ip_address=self.ip_address, frequency=frequency, duration=duration);
        self.recording_thread.signal.connect(self.record_finished)
        self.recording_thread.start()
        
        print('RECORD! %g' % frequency)

    def generate_curve(self):
        self.plot_position.legend.scene().removeItem(self.plot_position.legend)
        self.plot_position.clear()
        self.plot_position.addLegend()

        amplitude = self.signalGen.amplitudeDoubleSpinBox.value();
        frequency = self.signalGen.frequencyDoubleSpinBox.value();
        duration  = self.signalGen.durationDoubleSpinBox.value();

        sample_interval = 1/SYSTEM_GENERATE_SAMPLE_RATE - 0.0001
        timevec = np.arange(0, duration, sample_interval)

        y = 0;

        current_signal_type = self.signalGenTypeComboBox.currentText()
        if current_signal_type == "Sine":
            y = amplitude*(1+np.sin(timevec*frequency*2*np.pi))
        elif current_signal_type == "Triangle":
            y = amplitude*triangle2(timevec, frequency)
        elif current_signal_type == "Custom":
            print("TODO!")
            print("Custom gen.gen")
        
        self.plot_position.plot(timevec, y, name='Target curve')

        self.generated_curve = y;
        self.timestamp_generated_curve = timevec;

        signal_type = str(self.signalGenTypeComboBox.currentText())

        print("Button clicked! button was " + signal_type +"")

def alert(titlestr, msgstr):
    msg_box = QtWidgets.QMessageBox()
    msg_box.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    msg_box.setWindowTitle(titlestr);
    msg_box.setText(msgstr);
    msg_box.exec();

def triangle2(timevec, frequency):
    y = np.zeros(len(timevec))
    for i, t in enumerate(timevec):
        tmod = t*frequency % 1
        k = 4
        c = 0
        if tmod > 0.5:
            k = -4
            c = 4

        y[i] = k*tmod + c
        
    return y

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit( ret )


