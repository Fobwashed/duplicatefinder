from PyQt5 import QtWidgets
from os import path
import window

class Duplicate_Finder():

    def __init__(self):
        self.folders = set()
        self.dupes = list()

    def main(self):
        self.app = QtWidgets.QApplication([])
        self.fileBrowser = window.MyFileBrowser()
        self.fileBrowser.set_duplicate_finder(self)
        self.fileBrowser.show()
        self.app.exec_()

    #Return number of folders selected
    def folders_length_check(self):
        if len(self.folders) > 0:
            return True
        else:
            return False

    #Called by window to add selected folder
    def add_to_list(self, folderToAdd):
        if path.exists(folderToAdd) and path.isdir(folderToAdd):
            print("Adding: ", folderToAdd)
            if self.folders.__contains__(folderToAdd):
                self.fileBrowser.statusbar.showMessage(folderToAdd + " is already in search directories")
            else:
                self.folders.add(folderToAdd)
                self.fileBrowser.statusbar.showMessage("Adding: {} to search directories".format(folderToAdd))
                self.fileBrowser.add_to_selected_folders(folderToAdd)

    #Called by window to remove selected folder
    def remove_from_list(self, folderToRemove):
        if path.exists(folderToRemove) and path.isdir(folderToRemove):
            if self.folders.__contains__(folderToRemove):
                self.folders.remove(folderToRemove)
                self.fileBrowser.statusbar.showMessage("Removing: {} from Search directories".format(folderToRemove))
                self.fileBrowser.remove_from_selected_folders(folderToRemove)
            else:
                self.fileBrowser.statusbar.showMessage("{} is not in search directories".format(folderToRemove))

    #Check if a folder is already in the list
    def is_folder_in_list(self, file_path):
        if self.folders.__contains__(file_path):
            return True
        return False

if __name__ == "__main__":
    df = Duplicate_Finder()
    df.main()