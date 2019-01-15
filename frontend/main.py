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

class ControllerRecordThread(QtCore.QThread):
    signal = QtCore.pyqtSignal('PyQt_PyObject')
    recording = False;
    frequency = 100; #Hz
    galil_handle = None;

    def __init__(self, galil_handle=None, frequency=100):
        QtCore.QThread.__init__(self)
        self.frequency = frequency
        # Caller is responsible to make sure that galil_handle is ok
        self.galil_handle = galil_handle

    def run(self):
        print('Recording Thread running...')
        nsamples = int(1*self.frequency)
        start_timestamp = datetime.now()
        timestamps = np.zeros(nsamples)
        values = np.zeros(nsamples)

        for i in range(0,nsamples):
            t1 = datetime.now()
            timestamps[i] = (datetime.now() - start_timestamp).total_seconds()
            value = self.galil_handle.GCommand('TP')
            values[i] = float(value)
            t2 = datetime.now()
            exec_time = t2 - t1
            time.sleep(1.0/self.frequency - exec_time.total_seconds())
        
        #timedeltas = (np.array(timestamps) - start_timestamp)
        #helper = np.vectorize(lambda x: x.total_seconds())
        #timedeltas = helper(timedeltas)


        data = {
                'timedeltas': timestamps,
                'values': np.array(values)/SYSTEM_STEPS_PER_MM,
        }
        self.signal.emit(data)

class MainWindow(QMainWindow):
    legend = None;
    galil_handle = None;
    recording_thread = None;

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/MainWindow.ui', self)
        self.show()

        image = QtGui.QImage(100, 100, QtGui.QImage.Format_Mono)
        image.fill(0)
        
        self.legend = self.plotView.addLegend()

        # Setup signals and slots
        self.generateButton.clicked.connect(self.generate_curve)
        self.startButton.clicked.connect(self.start_motion)
        self.stopButton.clicked.connect(self.stop_motion)
        self.signalGenTypeComboBox.currentTextChanged.connect(self.change_signal_widget)
        self.recordButton.clicked.connect(self.record_position)
       
        self.actionConnect.triggered.connect(self.open_connect_dialog)


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
            print(disp(val))
            print('accepted!')

    def change_signal_widget(self):
        current_signal_type = self.signalGenTypeComboBox.currentText()
        if current_signal_type == "Custom":
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
        self.galil_handle.GCommand('KP 30')
        self.galil_handle.GCommand('KI 0')
        self.galil_handle.GCommand('KD 0')
        self.galil_handle.GCommand('TL 5')      # current limit (1A)/(0.2A/V) = 5 V -> (TL n=5)
        self.galil_handle.GCommand('TK 2')      # torque limit (2A)/(0.2A/V) = 10 V -> (TK n=10)
        self.galil_handle.GCommand('OE 1')      # motor off on error
        self.galil_handle.GCommand('MT 1')      # motor type
        self.galil_handle.GCommand('LC 1')      # reduce holding current
        self.galil_handle.GCommand('AC 20000') # Acceleration
        self.galil_handle.GCommand('DC 20000') # Decceleration
        self.galil_handle.GCommand('DC 8000')   # Speed
        self.galil_handle.GCommand('BAA')       # Specify A - axis for sinusoidal	 commutation
        self.galil_handle.GCommand('BMA = %d' % SYSTEM_STEPS_PER_CYCLE) # Specify counts/magnetic cycle
        self.galil_handle.GCommand('BZA = 4')   # Commutate motor using 3V
        
        #TODO Tell user to put syringe in start position.
        self.galil_handle.GCommand('DP 0')      # Define 0 pos
        self.galil_handle.GCommand('SHA')       # Initialize motor A

        return True

    def start_motion(self):
        self.controller_init()
    
    def stop_motion(self):
        self.galil_handle.GCommand('AB')
        self.galil_handle.GCommand('MO')
        
    def record_finished(self, result):
        print('Finished recording: %s' % str(result))
        self.plotView.plot(result['timedeltas'], result['values'], name = 'Measurued', pen='r')
        
    def record_position(self):
        self.controller_init()
        frequency = self.sampleFrequencySpinBox.value();

        # TODO: Setup a thread to continously pull the current encoder position according to frequency.
        self.recording_thread = ControllerRecordThread(galil_handle=self.galil_handle, frequency=frequency);
        self.recording_thread.signal.connect(self.record_finished)
        self.recording_thread.start()
        
        print('RECORD! %g' % frequency)

        # TODO: Start a thread for controlling movement.



    def generate_curve(self):
        self.legend.scene().removeItem(self.legend)
        self.legend = self.plotView.addLegend()
        self.plotView.clear()

        amplitude = self.signalGen.amplitudeDoubleSpinBox.value();
        frequency = self.signalGen.frequencyDoubleSpinBox.value();

        sample_rate = 0.01
        time = np.arange(0,1, sample_rate)

        y = 0;

        current_signal_type = self.signalGenTypeComboBox.currentText()
        if current_signal_type == "Sine":
            y = amplitude*np.sin(time*frequency*2*np.pi)
        elif current_signal_type == "Triangle":
            print("TODO!")
        elif current_signal_type == "Custom":
            print("TODO!")
            print("Custom gen.gen")
        
        self.plotView.plot(time, y, name='Target curve')
        self.plotView.setLabel('left', 'Position [mm]')
        self.plotView.setLabel('bottom', 'Time [s]')

        signal_type = str(self.signalGenTypeComboBox.currentText())

        print("Button clicked! button was " + signal_type +"")

def alert(titlestr, msgstr):
    msg_box = QtWidgets.QMessageBox()
    msg_box.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    msg_box.setWindowTitle(titlestr);
    msg_box.setText(msgstr);
    msg_box.exec();

def triangle2(length, amplitude):
    section = length // 4
    x = np.linspace(0, amplitude, section+1)
    mx = -x
    return np.r_[x, x[-2::-1], mx[1:], mx[-2:0:-1]]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit( ret )


