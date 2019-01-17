from PyQt5 import QtWidgets, uic
from PyQt5 import QtGui, QtCore

class CustomSignalWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi('ui/CustomSignalWidget.ui', self)

    def browse_file(self):
        fileDialog = QtGui.QFileDialog(self)
        fileDialog.setNameFilters(["CSV files (*.csv)"])
        fileDialog.selectNameFilter("CSV files (*.csv)")
        if fileDialog.exec():
            self.filePathLineEdit.setText(fileDialog.selectedFiles()[0])

