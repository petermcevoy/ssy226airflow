from PyQt5 import QtWidgets, uic

class SignalGenWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi('ui/SignalGenWidget.ui', self)  # Loads all widgets of uifile.ui into self
