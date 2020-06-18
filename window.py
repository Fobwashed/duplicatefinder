from PyQt5 import QtCore, QtGui, QtWidgets, Qt
import duplicateFinderUI
import os
import csv
import time
import dupe_check
import make_original_folder
import sys

class MyFileBrowser(duplicateFinderUI.Ui_MainWindow, QtWidgets.QMainWindow):

    resized = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super(MyFileBrowser, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Duplicate File Finder")

        self.timer = time.time()

        self.deleted_files = list()
        
        #Context Menus

        #windowDirectory
        self.windowDirectory.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.windowDirectory.customContextMenuRequested.connect(self.context_windowDirectory)
        #windowSelected
        self.windowSelected.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.windowSelected.customContextMenuRequested.connect(self.context_windowSelected)
        #windowFoundPrimary
        self.windowFoundPrimary.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.windowFoundPrimary.customContextMenuRequested.connect(self.context_windowFoundPrimary)
        #windowFoundDuplicates
        self.windowFoundDuplicates.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.windowFoundDuplicates.customContextMenuRequested.connect(self.context_windowFoundDuplicates)

        #Button Actions
        #windowDirectory
        self.buttonAdd.clicked.connect(self.execute_buttonAdd)
        self.buttonRemove.clicked.connect(self.execute_buttonRemove)
        self.buttonSearch.clicked.connect(self.execute_buttonSearch)
        #windowSelected
        self.buttonBack.clicked.connect(self.execute_buttonBack)
        self.buttonClearEmpty.clicked.connect(self.execute_buttonClearEmpty)
        self.buttonSwapOriginal.clicked.connect(self.execute_buttonSwapOriginal)
        self.buttonDeleteSelected.clicked.connect(self.execute_buttonDeleteSelected)
        self.buttonDeleteDuplicates.clicked.connect(self.execute_buttonDeleteDuplicates)
        self.buttonDeleteAll.clicked.connect(self.execute_buttonDeleteAll)
        self.buttonSaveCSV.clicked.connect(self.execute_buttonSaveCSV)

        #widget focus
        #bools
        self.isFocusWindowDirectory = False
        self.isFocusWindowSelected = False
        self.isFocusWindowFoundPrimary = False
        self.isFocusWindowFoundDuplicates = False
        #Event Filter
        self.windowDirectory.installEventFilter(self)
        self.windowSelected.installEventFilter(self)
        self.windowFoundPrimary.installEventFilter(self)
        self.windowFoundDuplicates.installEventFilter(self)

        self.isAskToDelete = True

        self.dupes = list()
        self.currentPrimaryNode = None
        self.totalFileCount = ""

        #populate lists
        self.populate()

        #Threads
        self.searchThread = dupe_check.getDupesThread() #getDupesThread()
        self.searchThread.complete.connect(self.thread_search_finished)
        self.searchThread.message.connect(self.thread_status_message)
        self.searchThread.cancelled.connect(self.thread_search_cancelled)
        self.searchThread.totalFiles.connect(self.thread_total_files)
        self.searchThread.accessError.connect(self.thread_access_error)

        self.makeOriginalFolderThread = make_original_folder.makeOriginalFolder()
        self.makeOriginalFolderThread.complete.connect(self.thread_originalFolder_finished)
        self.makeOriginalFolderThread.message.connect(self.thread_status_message)
        self.makeOriginalFolderThread.cancelled.connect(self.thread_originalFolder_cancelled)

        print("PyQt version:", Qt.PYQT_VERSION_STR)

        #LEGAL
        self.isAgreeToUse = False
        self.create_popup_ok_cancel("USER AGREEMENT", 
        ("The purpose of this program is to find duplicate files in the folders selected by the user. " 
        "Once files are found, the user has the option to delete them. " 
        "By clicking OK, the user is agreeing to take full responsibility for any and all actions taken on files and folders by this program."), self.EULAAccept, QtWidgets.QMessageBox.Warning)
        if not self.isAgreeToUse:
            sys.exit()

        self.statusbar.showMessage("Programmed by Steve Kim. Twitter: @Fobwashed")
        
    def EULAAccept(self):
        self.isAgreeToUse = True

    #Window Resize Methods
    def resizeEvent(self, event):
        self.resized.emit(event)
        return super(MyFileBrowser, self).resizeEvent(event)

    def resize_event(self):
        size = self.frameGeometry()
        width = size.width()
        height = size.height()
        
        print("Width: {}  Height: {}".format(width, height))
        sixth = int(width / 6)
        widthDirectory = sixth * 3
        buttonPosX = widthDirectory + 30
        selectedFolderPos = widthDirectory + 176
        widthSelectedFolder = width - 15 - 176 - widthDirectory
        posSearchY = height - 250
        if posSearchY < 144:
            posSearchY = 144
        
        self.menubar.setGeometry(0, 0, width - 2, 21)
        self.stackedWidget.setGeometry(-1, 0, width, height)

        self.windowDirectory.setGeometry(15,40, widthDirectory, height - 120)
        self.windowSelected.setGeometry(selectedFolderPos, 40, widthSelectedFolder, height -120)
        self.buttonAdd.setGeometry(buttonPosX, 40, 131, 41)
        self.buttonRemove.setGeometry(buttonPosX, 92, 131, 41)
        self.buttonSearch.setGeometry(buttonPosX, posSearchY, 131, 51)
        self.checkBoxFileName.setGeometry(buttonPosX, posSearchY + 90, 121, 16)
        self.checkBoxFileSize.setGeometry(buttonPosX, posSearchY + 110, 121, 16)
        self.checkBoxHashSum.setGeometry(buttonPosX, posSearchY + 130, 121, 16)
        self.labelSearchOptions.setGeometry(buttonPosX + 20, posSearchY + 60, 91, 20)
        self.labelFolderSelection.setGeometry(20, 10, 131, 21)
        self.labelSelectedFolders.setGeometry(selectedFolderPos, 10, 131, 21)
        
        resultsWidth = width - 30
        resultsWindowWidth = int((resultsWidth - 140) / 2)
        resultsButtonX = resultsWindowWidth + 30
        posDeleteAllY = height - 250
        if posDeleteAllY < 310:
            posDeleteAllY = 310

        self.labelOriginal.setGeometry(20, 10, 131, 21)
        self.windowFoundPrimary.setGeometry(15, 40, resultsWindowWidth, height - 120)
        self.labelDuplicates.setGeometry(resultsWindowWidth + 155, 10, 131, 21)
        self.windowFoundDuplicates.setGeometry(resultsWindowWidth + 155, 40, resultsWindowWidth, height - 120)

        self.buttonSwapOriginal.setGeometry(resultsButtonX, 40, 110, 41)
        self.buttonDeleteSelected.setGeometry(resultsButtonX, 120, 110, 41)
        self.buttonDeleteDuplicates.setGeometry(resultsButtonX, 170, 110, 41)
        
        self.buttonClearEmpty.setGeometry(resultsButtonX, 300, 110, 41)
        self.checkBoxClearEmpty.setGeometry(resultsButtonX + 10, 350, 91, 31)

        self.buttonDeleteAll.setGeometry(resultsButtonX, posDeleteAllY, 110, 41)
        self.buttonBack.setGeometry(resultsButtonX, posDeleteAllY + 140, 110, 41)
        
        self.buttonSaveCSV.setGeometry(resultsButtonX, posDeleteAllY + 95, 110, 41)

    #Populate Files/Folders Methods
    def populate(self):
        #windowDirectory
        self.modelWindowDirectory = QtWidgets.QFileSystemModel()
        self.modelWindowDirectory.setRootPath((QtCore.QDir.rootPath()))
        self.windowDirectory.setModel(self.modelWindowDirectory)
        self.windowDirectory.setSortingEnabled(True)
        self.windowDirectory.setColumnWidth(0,270)

        #windowSelected
        self.modelWindowSelected = QtGui.QStandardItemModel()
        self.windowSelected.setModel(self.modelWindowSelected)
        self.windowSelected.clicked[QtCore.QModelIndex].connect(self.clicked_windowSelected)

        #windowFoundPrimary
        self.modelWindowFoundPrimary = QtGui.QStandardItemModel()
        self.modelWindowFoundPrimary.setColumnCount(1)
        self.windowFoundPrimary.setModel(self.modelWindowFoundPrimary)
        self.windowFoundPrimary.clicked[QtCore.QModelIndex].connect(self.clicked_windowFoundPrimary)
        self.selModWindowFoundPrimary = self.windowFoundPrimary.selectionModel()

        self.selModWindowFoundPrimary.currentChanged.connect(self.primaryChanged)

        self.resized.connect(self.resize_event)
        
        #windowFoundDuplicates
        self.modelWindowFoundDuplicates = QtGui.QStandardItemModel()
        self.windowFoundDuplicates.setModel(self.modelWindowFoundDuplicates)
        self.windowFoundDuplicates.clicked[QtCore.QModelIndex].connect(self.clicked_windowFoundDuplicates)
        self.selModWindowFoundDuplicates = self.windowFoundDuplicates.selectionModel()
    
    def primaryChanged(self):
        index = self.windowFoundPrimary.currentIndex()
        if index.isValid():
            item = self.modelWindowFoundPrimary.itemFromIndex(index)

            for entry in self.dupes:
                if entry.data_location == item.text():
                    self.currentPrimaryNode = entry
                    break
                    
        self.populate_found_duplicates()
        
    def populateFound(self, dupes):
        self.dupes = dupes
        
        self.isAskToDelete = True

        for dupe in self.dupes:
            if self.currentPrimaryNode is None:
                self.currentPrimaryNode = dupe
            toAdd = QtGui.QStandardItem(dupe.data_location)
            self.modelWindowFoundPrimary.appendRow(toAdd)
        
        if self.currentPrimaryNode is None:
            self.statusbar.showMessage("No Duplicates Found")
        else:
            self.populate_found_duplicates()

        dupeCount = 0
        dupeCount -= len(self.dupes)
        dupeSize = 0
        e = time.time()
        timetoSearch = (e - self.timer)
        for entry in self.dupes:
            dupeCount += len(entry.data_duplicates)

            dupeSize += entry.data_size * (len(entry.data_duplicates) - 1)
        
        #convert bytes to mb
        dupeSize = dupeSize / 1000000
        dupeSizeStr = "%.2f" % dupeSize + " MB"

        searchTime = "%.2f" % timetoSearch
        
        result = "Searched {} Files and found {} files that have a total of {} duplicates in {} seconds. Duplicate Files total size = {}.".format(self.totalFileCount, str(len(self.dupes)), str(dupeCount), searchTime, dupeSizeStr)
        self.create_popup_message("Duplicates Found", result)
        self.statusbar.showMessage(result)

    def populate_change_found_windows(self):
        self.modelWindowFoundPrimary.clear()

        for dupe in self.dupes:
            toAdd = QtGui.QStandardItem(dupe.data_location)
            self.modelWindowFoundPrimary.appendRow(toAdd)
        
        self.populate_found_duplicates()

    def populate_found_duplicates(self):
        self.modelWindowFoundDuplicates.clear()

        if self.currentPrimaryNode is not None:

            for dupe in self.currentPrimaryNode.data_duplicates:
                if dupe.data_location == self.currentPrimaryNode.data_location:
                    continue
                toAdd = QtGui.QStandardItem(dupe.data_location)
                self.modelWindowFoundDuplicates.appendRow(toAdd)

    #Focus Control
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.FocusIn:

            self.isFocusWindowDirectory = False
            self.isFocusWindowSelected = False
            self.isFocusWindowFoundPrimary = False
            self.isFocusWindowFoundDuplicates = False

            if obj == self.windowDirectory:
                self.isFocusWindowDirectory = True
            elif obj == self.windowSelected:
                self.isFocusWindowSelected = True
            elif obj == self.windowFoundPrimary:
                self.isFocusWindowFoundPrimary = True
            elif obj == self.windowFoundDuplicates:
                self.isFocusWindowFoundDuplicates = True
            else:
                print("none have focus")
                
        return super(MyFileBrowser, self).eventFilter(obj, event)

    #Clicked Windows
    def clicked_windowSelected(self, index):
        item = self.modelWindowSelected.itemFromIndex(index)
        print(item.text())

    def clicked_windowFoundPrimary(self, index):
        item = self.modelWindowFoundPrimary.itemFromIndex(index)
        
        for entry in self.dupes:
            if entry.data_location == item.text():
                self.currentPrimaryNode = entry
                break

        self.populate_found_duplicates()

    def clicked_windowFoundDuplicates(self, index):
        item = self.modelWindowFoundDuplicates.itemFromIndex(index)
        print(item.text())

    #Context Methods
    #Menus
    def context_windowDirectory(self):
        menu = QtWidgets.QMenu()

        index = self.windowDirectory.currentIndex()
        file_path = self.modelWindowDirectory.filePath(index)

        if os.path.isdir(file_path):
            if self.df.is_folder_in_list(file_path):
                removeFolderFromSearch = menu.addAction("Remove Folder From Search")
                removeFolderFromSearch.triggered.connect(self.context_command_removeDirectory)
            else:
                addFolderToSearch = menu.addAction("Add Folder to Search")
                addFolderToSearch.triggered.connect(self.context_command_addDirectory)
            
            openBrowser = menu.addAction("Open Folder in Browser")
            openBrowser.triggered.connect(self.context_command_open)
        else:
            openFile = menu.addAction("Open File")
            openFile.triggered.connect(self.context_command_open)

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def context_windowSelected(self):
        menu = QtWidgets.QMenu()

        openBrowser = menu.addAction("Open Folder in Browser")
        openBrowser.triggered.connect(self.context_command_open)

        remove = menu.addAction("Remove Folder From Search")
        remove.triggered.connect(self.context_command_removeDirectory)

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def context_windowFoundPrimary(self):
        menu = QtWidgets.QMenu()

        openFile = menu.addAction("Open File")
        openFile.triggered.connect(self.context_command_open)

        openDirectory = menu.addAction("Show in Browser")
        openDirectory.triggered.connect(self.context_command_open_directory)

        removeFromList = menu.addAction("Remove From List")
        removeFromList.triggered.connect(self.context_remove_from_list)

        makeOriginalFolder = menu.addAction("Set Folder as Original for All Files")
        makeOriginalFolder.triggered.connect(self.context_make_original_folder)

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    def context_windowFoundDuplicates(self):
        menu = QtWidgets.QMenu()

        openFile = menu.addAction("Open File")
        openFile.triggered.connect(self.context_command_open)

        openDirectory = menu.addAction("Show in Browser")
        openDirectory.triggered.connect(self.context_command_open_directory)

        makePrimary = menu.addAction("Assign as Original")
        makePrimary.triggered.connect(self.context_make_primary)

        removeFromList = menu.addAction("Remove From List")
        removeFromList.triggered.connect(self.context_remove_from_list)

        deleteFile = menu.addAction("Delete File")
        deleteFile.triggered.connect(self.context_command_delete)

        makeOriginalFolder = menu.addAction("Set Folder as Original for All Files")
        makeOriginalFolder.triggered.connect(self.context_make_original_folder)

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    #Methods
    def context_command_open(self):
        file_path = ""

        if self.isFocusWindowDirectory:
            index = self.windowDirectory.currentIndex()
            if index.isValid():
                file_path = self.modelWindowDirectory.filePath(index)
        elif self.isFocusWindowSelected:
            index = self.windowSelected.currentIndex()
            if index.isValid():
                file_path = self.modelWindowSelected.itemFromIndex(index).text()
        elif self.isFocusWindowFoundPrimary:
            index = self.windowFoundPrimary.currentIndex()
            if index.isValid():
                file_path = self.modelWindowFoundPrimary.itemFromIndex(index).text()
            elif self.currentPrimaryNode is not None:
                file_path = self.currentPrimaryNode.data_location
        elif self.isFocusWindowFoundDuplicates:
            index = self.windowFoundDuplicates.currentIndex()
            if index.isValid():
                file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()
        
        if file_path != "":
            try:
                os.startfile(file_path)
                self.statusbar.showMessage("Opening {}".format(file_path))
            except Exception as ex:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                self.create_popup_message("Error", message)
        else:
            self.statusbar.showMessage("File or Directory to Open not selected")

    def context_command_open_directory(self):
        file_path = ""

        if self.isFocusWindowDirectory:
            index = self.windowDirectory.currentIndex()
            if index.isValid():
                file_path = self.modelWindowDirectory.filePath(index)
        elif self.isFocusWindowSelected:
            index = self.windowSelected.currentIndex()
            if index.isValid():
                file_path = self.modelWindowSelected.filePath(index)
        elif self.isFocusWindowFoundPrimary:
            index = self.windowFoundPrimary.currentIndex()
            if index.isValid():
                file_path = self.modelWindowFoundPrimary.itemFromIndex(index).text()
            elif self.currentPrimaryNode is not None:
                file_path = self.currentPrimaryNode.data_location
        elif self.isFocusWindowFoundDuplicates:
            index = self.windowFoundDuplicates.currentIndex()
            if index.isValid():
                file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()

        if file_path != "":
            dir_path = os.path.dirname(file_path)
            os.startfile(dir_path)
        else:
            self.statusbar.showMessage("File or Directory to Open not selected")

    def context_command_addDirectory(self):
        if self.isFocusWindowDirectory:
            index = self.windowDirectory.currentIndex()
            file_path = self.modelWindowDirectory.filePath(index)
            self.df.add_to_list(file_path)
            self.isFocusWindowDirectory = self.isFocusWindowSelected = False

    def context_remove_from_list(self):
        file_path = "None Set"
        if self.isFocusWindowFoundPrimary:

            indexes = self.selModWindowFoundPrimary.selectedIndexes()
            for index in indexes:
                file_path = self.modelWindowFoundPrimary.itemFromIndex(index).text()
                for entry in self.dupes:
                    if entry.data_location == file_path:
                        if self.currentPrimaryNode is not None and entry.data_location == self.currentPrimaryNode.data_location:
                            self.currentPrimaryNode = None
                        self.dupes.remove(entry)
                        break
            self.populate_change_found_windows()

        elif self.isFocusWindowFoundDuplicates:

            if self.currentPrimaryNode is not None:

                indexes = self.selModWindowFoundDuplicates.selectedIndexes()
                for index in indexes:
                    replacement = list()
                    file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()
                    for dupe in self.currentPrimaryNode.data_duplicates:
                        if dupe.data_location == file_path:
                            continue
                        else:
                            replacement.append(dupe)
                    self.currentPrimaryNode.data_duplicates = replacement
            
            self.populate_change_found_windows()

    def context_make_original_folder(self):

        file_path = "None Set"

        if self.isFocusWindowFoundPrimary:
            index = self.windowFoundPrimary.currentIndex()
            if index.isValid():
                file_path = self.modelWindowFoundPrimary.itemFromIndex(index).text()
            elif self.currentPrimaryNode is not None:
                file_path = self.currentPrimaryNode.data_location
        elif self.isFocusWindowFoundDuplicates:
            index = self.windowFoundDuplicates.currentIndex()
            if index.isValid():
                file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()

        if file_path != "":
            dir_path = os.path.dirname(file_path)
            
            self.buttonSwapOriginal.setEnabled(False)
            self.buttonDeleteSelected.setEnabled(False)
            self.buttonDeleteDuplicates.setEnabled(False)
            self.buttonDeleteAll.setEnabled(False)
            self.buttonBack.setEnabled(False)
            self.buttonClearEmpty.setEnabled(False)
            self.buttonAdd.setEnabled(False)
            self.buttonRemove.setEnabled(False)
            self.checkBoxFileName.setEnabled(False)
            self.checkBoxFileSize.setEnabled(False)
            self.checkBoxHashSum.setEnabled(False)
            self.windowDirectory.setEnabled(False)
            self.windowSelected.setEnabled(False)
            self.buttonSearch.setEnabled(False)

            self.makeOriginalFolderThread.set_params(dir_path, self.dupes)
            self.makeOriginalFolderThread.start()

        else:
            self.statusbar.showMessage("Directory not selectable")

    def context_command_removeDirectory(self):
        file_path = ""

        if self.isFocusWindowDirectory:        
            index = self.windowDirectory.currentIndex()
            if index.isValid():
                file_path = self.modelWindowDirectory.filePath(index)
            else:
                self.statusbar.showMessage("No directory to Remove selected")
        elif self.isFocusWindowSelected:
            index = self.windowSelected.currentIndex()
            if index.isValid():
                file_path = self.modelWindowSelected.itemFromIndex(index).text()
            else:
                self.statusbar.showMessage("No directory to Remove selected")

        self.df.remove_from_list(file_path)
        self.isFocusListViewSelectedFolders = self.isFocusTreeView = False

    def context_make_primary(self):
        index = self.windowFoundDuplicates.currentIndex()
        if index.isValid():
            file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()
            self.currentPrimaryNode.swap_primary(file_path)
            self.populate_change_found_windows()
            self.statusbar.showMessage("Setting {} as Original".format(file_path))

            self.restore_index_to_windowFoundPrimary()
        else:
            self.statusbar.showMessage("Unable to change to Original")

    def context_command_delete(self):
        file_path = "None Set"
        indexes = self.selModWindowFoundDuplicates.selectedIndexes()
        
        if len(indexes) > 0:
            for index in indexes:
                file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()
                self.currentPrimaryNode.delete_duplicate(file_path, self)

            if(self.checkBoxClearEmpty.isChecked()):
                self.execute_buttonClearEmpty()
            else:
                self.populate_change_found_windows()

            self.restore_index_to_windowFoundPrimary()
        else:
            self.statusbar.showMessage("No file to Delete selected")

    #Button Methods
    def execute_buttonAdd(self):
        self.context_command_addDirectory()

    def execute_buttonRemove(self):

        if self.isFocusWindowDirectory:
            index = self.windowDirectory.currentIndex()
            if index.isValid():
                file_path = self.modelWindowDirectory.filePath(index)
                self.df.remove_from_list(file_path)
                self.statusbar.showMessage("Removing {} from search directories".format(file_path))
            else:
                self.statusbar.showMessage("No item to Remove selected")
        else:
            index = self.windowSelected.currentIndex()
            if index.isValid():
                file_path = self.modelWindowSelected.itemFromIndex(index).text()
                self.df.remove_from_list(file_path)
                self.statusbar.showMessage("Removing {} from search directories".format(file_path))
            else:
                self.create_popup_message("Unable to Remove Folder","No Folder to Remove selected")
                self.statusbar.showMessage("No item to Remove selected")

        self.isFocusListViewSelectedFolders = self.isFocusTreeView = False

    def execute_buttonBack(self):
        self.dupes.clear()
        self.currentPrimaryNode = None
        self.stackedWidget.setCurrentIndex(0)

    def execute_buttonSwapOriginal(self):
        index = self.windowFoundDuplicates.currentIndex()
        if index.isValid():
            file_path = self.modelWindowFoundDuplicates.itemFromIndex(index).text()
            self.currentPrimaryNode.swap_primary(file_path)
            self.populate_change_found_windows()
            self.statusbar.showMessage("Setting {} as Original".format(file_path))
            
            self.restore_index_to_windowFoundPrimary()
        else:
            self.create_popup_message("Unable to Swap","File to assign as Original not selected")
            self.statusbar.showMessage("File to assign as Original not selected")

    def execute_buttonDeleteSelected(self):
        index = self.windowFoundDuplicates.currentIndex()
        if index.isValid():
            self.context_command_delete()
        else:
            self.create_popup_message("Unable to Delete","No file to Delete selected")
            self.statusbar.showMessage("No file to Delete selected")
        
    def execute_buttonDeleteDuplicates(self):
        if self.currentPrimaryNode is not None:
            if len(self.currentPrimaryNode.data_duplicates) > 1:
                if self.isAskToDelete:
                    dupeCount = len(self.currentPrimaryNode.data_duplicates) - 1
                    self.create_popup_ok_cancel_checkBox("Delete Duplicates?", "Delete ALL {} Duplicate Files for {}?".format(str(dupeCount), self.currentPrimaryNode.data_name), self.delete_dupes, self.CheckBox_isAskToDelete, QtWidgets.QMessageBox.Warning)
                else:
                    self.delete_dupes()
            else:
                self.create_popup_message("Unable to Delete", "No Duplicates for selected Original found")
        else:
            self.create_popup_message("Unable to Delete", "No Original File selected")
            
    def execute_buttonClearEmpty(self):
        dupeReplace = list()
        for dupe in self.dupes:
            if len(dupe.data_duplicates) > 1:
                dupeReplace.append(dupe)
        
        self.dupes = dupeReplace

        if self.currentPrimaryNode is not None:
            if len(self.currentPrimaryNode.data_duplicates) <= 1:
                self.currentPrimaryNode = None

        self.populate_change_found_windows()

    def CheckBox_isAskToDelete(self, setTo):
        print("CheckBox isAskToDelete set to {}".format(str(setTo)))
        self.isAskToDelete = not setTo

    def delete_dupes(self):
        if self.currentPrimaryNode is not None:
            self.currentPrimaryNode.delete_all_duplicates(self)

            if(self.checkBoxClearEmpty.isChecked()):
                self.execute_buttonClearEmpty()
            else:
                self.populate_change_found_windows()

            self.restore_index_to_windowFoundPrimary()

    def execute_buttonDeleteAll(self):
        dupeCount = 0
        dupeCount -= len(self.dupes)
        for entry in self.dupes:
            dupeCount += len(entry.data_duplicates)
        
        if dupeCount > 0:
            self.create_popup_ok_cancel("DELETE ALL?", "Delete ALL {} Duplicate Files Found Across ALL Original Files?".format(str(dupeCount)), self.delete_all, QtWidgets.QMessageBox.Warning)

    def delete_all(self):
        for entry in self.dupes:
            entry.delete_all_duplicates(self)
        
        if(self.checkBoxClearEmpty.isChecked()):
            self.execute_buttonClearEmpty()
        else:
            self.populate_change_found_windows()

    def execute_buttonSaveCSV(self):
        self.create_output_file()

    def restore_index_to_windowFoundPrimary(self):
        for index in range(self.modelWindowFoundPrimary.rowCount()):
            item = self.modelWindowFoundPrimary.item(index)
            if self.currentPrimaryNode is not None and item.text() == self.currentPrimaryNode.data_location:
                self.windowFoundPrimary.setCurrentIndex(self.modelWindowFoundPrimary.indexFromItem(item))
                break

    def set_duplicate_finder(self, dfToSet):
        self.df = dfToSet

    def add_to_selected_folders(self, folderToAdd):
        toAdd = QtGui.QStandardItem(folderToAdd)
        self.modelWindowSelected.appendRow(toAdd)

    def remove_from_selected_folders(self, folderToRemove):
        for index in range(self.modelWindowSelected.rowCount()):
            item = self.modelWindowSelected.item(index)
            if item.text() == folderToRemove:
                self.modelWindowSelected.removeRow(index)
                break

    def write_to_output_file(self, output_text):
        self.deleted_files.append(output_text)

    def create_output_file(self):
        with open('deleted_files.csv','w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for deleted in self.deleted_files:
                csv_writer.writerow([deleted])

    def create_popup_ok_cancel(self, textTitle, textMessage, executeMethod, icon):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(icon)
        msgBox.setText(textMessage)
        msgBox.setWindowTitle(textTitle)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)        

        returnValue = msgBox.exec()

        if returnValue == QtWidgets.QMessageBox.Ok:
            print("OK Clicked")
            executeMethod()
        elif returnValue == QtWidgets.QMessageBox.Cancel:
            print("Cancel Clicked")

    def create_popup_ok_cancel_checkBox(self, textTitle, textMessage, executeMethod, checkBoolMethod, icon):
        cb =  QtWidgets.QCheckBox("Don't Show This Again")
        
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(icon)
        msgBox.setText(textMessage)
        msgBox.setWindowTitle(textTitle)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        msgBox.setCheckBox(cb)

        cb.toggled.connect(lambda:checkBoolMethod(cb.checkState()))

        returnValue = msgBox.exec()

        if returnValue == QtWidgets.QMessageBox.Ok:
            print("OK Clicked")
            executeMethod()
        elif returnValue == QtWidgets.QMessageBox.Cancel:
            print("Cancel Clicked")

    def create_popup_message(self, textTitle, textMessage):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText(textMessage)
        msgBox.setWindowTitle(textTitle)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msgBox.exec()

    def msgButtonClick(self, i):
        print("Button clicked is: {}".format(i.text()))

    def execute_buttonSearch(self):

        if self.buttonSearch.text() == "CANCEL SEARCH":
            self.searchThread.stop()
        else:
            if self.checkBoxFileName.isChecked() or self.checkBoxFileSize.isChecked() or self.checkBoxHashSum.isChecked():
                self.modelWindowFoundPrimary.clear()
                self.modelWindowFoundDuplicates.clear()
                self.currentPrimaryNode = None
                if self.df.folders_length_check():

                    self.buttonSwapOriginal.setEnabled(False)
                    self.buttonDeleteSelected.setEnabled(False)
                    self.buttonDeleteDuplicates.setEnabled(False)
                    self.buttonDeleteAll.setEnabled(False)
                    self.buttonBack.setEnabled(False)
                    self.buttonClearEmpty.setEnabled(False)
                    self.buttonAdd.setEnabled(False)
                    self.buttonRemove.setEnabled(False)
                    self.checkBoxFileName.setEnabled(False)
                    self.checkBoxFileSize.setEnabled(False)
                    self.checkBoxHashSum.setEnabled(False)
                    self.windowDirectory.setEnabled(False)
                    self.windowSelected.setEnabled(False)
                    self.buttonSearch.setText("CANCEL SEARCH")

                    self.searchThread.set_search_params(self.df.folders, self.checkBoxFileName.isChecked(), self.checkBoxFileSize.isChecked(), self.checkBoxHashSum.isChecked())
                    self.searchThread.start()

                    self.timer = time.time()

                else:
                    self.create_popup_message("No Folders Selected", "Please Select Folders to Search")
                    self.statusbar.showMessage("No Folders Selected")
            else:
                self.create_popup_message("No Search Options Checked", "Please Select a Search Option")
                self.statusbar.showMessage("No Search Options Checked")

    #THREAD METHODS
    def thread_originalFolder_finished(self, result):

        self.populate_change_found_windows()
        self.restore_index_to_windowFoundPrimary()
        self.thread_originalFolder_cancelled(result)

    def thread_originalFolder_cancelled(self, result):
        self.buttonSearch.setEnabled(True)
        self.checkBoxFileName.setEnabled(True)
        self.checkBoxFileSize.setEnabled(True)
        self.checkBoxHashSum.setEnabled(True)
        self.windowDirectory.setEnabled(True)
        self.windowSelected.setEnabled(True)
        self.buttonAdd.setEnabled(True)
        self.buttonRemove.setEnabled(True)
        self.buttonSearch.setEnabled(True)

        self.buttonSwapOriginal.setEnabled(True)
        self.buttonDeleteSelected.setEnabled(True)
        self.buttonDeleteDuplicates.setEnabled(True)
        self.buttonDeleteAll.setEnabled(True)
        self.buttonBack.setEnabled(True)
        self.buttonClearEmpty.setEnabled(True)

    def thread_search_finished(self, result):

        self.stackedWidget.setCurrentIndex(1)
        
        self.buttonSearch.setText("SEARCH")
        self.checkBoxFileName.setEnabled(True)
        self.checkBoxFileSize.setEnabled(True)
        self.checkBoxHashSum.setEnabled(True)
        self.windowDirectory.setEnabled(True)
        self.windowSelected.setEnabled(True)
        self.buttonAdd.setEnabled(True)
        self.buttonRemove.setEnabled(True)
        self.buttonSearch.setEnabled(True)

        self.buttonSwapOriginal.setEnabled(True)
        self.buttonDeleteSelected.setEnabled(True)
        self.buttonDeleteDuplicates.setEnabled(True)
        self.buttonDeleteAll.setEnabled(True)
        self.buttonBack.setEnabled(True)
        self.buttonClearEmpty.setEnabled(True)

        self.populateFound(result)

    def thread_status_message(self, result):

        self.statusbar.showMessage(result)

    def thread_search_cancelled(self, result):

        self.buttonSearch.setText("SEARCH")
        self.checkBoxFileName.setEnabled(True)
        self.checkBoxFileSize.setEnabled(True)
        self.checkBoxHashSum.setEnabled(True)
        self.windowDirectory.setEnabled(True)
        self.windowSelected.setEnabled(True)
        self.buttonAdd.setEnabled(True)
        self.buttonRemove.setEnabled(True)
        self.buttonSearch.setEnabled(True)

        self.buttonSwapOriginal.setEnabled(True)
        self.buttonDeleteSelected.setEnabled(True)
        self.buttonDeleteDuplicates.setEnabled(True)
        self.buttonDeleteAll.setEnabled(True)
        self.buttonBack.setEnabled(True)
        self.buttonClearEmpty.setEnabled(True)
    
    def thread_total_files(self, result):
        self.totalFileCount = result

    def thread_access_error(self, result):
        self.thread_search_cancelled(False)
        self.create_popup_message("ERROR", result)
