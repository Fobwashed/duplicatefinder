from os import path
import PyQt5.QtCore

class makeOriginalFolder(PyQt5.QtCore.QThread):

    complete = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    message = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    cancelled = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')

    isSendComplete = True

    def __init__(self):
        PyQt5.QtCore.QThread.__init__(self)

    def run(self):
        self.threadActive = True
        self.isSendComplete = True

        self.execute_original_folder()

        if self.isSendComplete:
            self.complete.emit(self.dupes)

    def stop(self):
        print("Thread stop called")
        self.requestInterruption()

    def __del__(self):
        self.wait()

    def set_params(self, dir_path, dupes):
        self.dir_path = dir_path
        self.dupes = dupes

    def execute_original_folder(self):
        
        for entry in self.dupes:
            self.message.emit("Checking: {}".format(str(entry.data_name)))
            entry.set_primary_folder(self.dir_path)
        
        self.message.emit("{} folder set as original location.".format(self.dir_path))
        self.complete.emit(self.dir_path)
