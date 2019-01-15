from PyQt5 import QtWidgets, uic

class ConnectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        #self.setAttributI#e(QtCore.Qt.WA_DeleteOnClose)
        uic.loadUi('ui/ConnectDialog.ui', self)
