import sys
#from ui.MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QGridLayout, QWidget, QComboBox
from PyQt5 import QtWidgets
from PyQt5 import QtGui, uic

from ui.CustomSignalWidget import CustomSignalWidget

import pyqtgraph as pg
import numpy as np

class MainWindow(QMainWindow):
    legend = None;

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/MainWindow.ui', self)
        self.show()

        image = QtGui.QImage(100, 100, QtGui.QImage.Format_Mono)
        image.fill(0)
        
        #graphicsScene = QtWidgets.QGraphicsScene()
        #graphicsScene.addPixmap( QtGui.QPixmap.fromImage(image) )
        #self.graphicsView.setScene(graphicsScene)

        self.legend = self.plotView.addLegend()

        # Setup signals and slots
        self.generateButton.clicked.connect(self.generate_curve)
        self.signalGenTypeComboBox.currentTextChanged.connect(self.change_signal_widget)


    def change_signal_widget(self):
        current_signal_type = self.signalGenTypeComboBox.currentText()
        if current_signal_type == "Custom":
            self.signalGenStackedWidget.setCurrentIndex(1)
        else: 
            self.signalGenStackedWidget.setCurrentIndex(0)

        
        

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
