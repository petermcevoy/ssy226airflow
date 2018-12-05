from PyQt5 import QtWidgets, uic

class CustomSignalWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi('ui/CustomSignalWidget.ui', self)
