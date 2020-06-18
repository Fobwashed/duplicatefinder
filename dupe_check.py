import os
from os import path
import file_node
import PyQt5.QtCore

class getDupesThread(PyQt5.QtCore.QThread):# QThread):

    complete = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    message = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    cancelled = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    totalFiles = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    accessError = PyQt5.QtCore.pyqtSignal('PyQt_PyObject')
    
    isSendComplete = True

    def __init__(self):
        PyQt5.QtCore.QThread.__init__(self)        

    def run(self):
        self.threadActive = True
        self.isSendComplete = True
        self.fileCount = ""
        self.dupes = self.execute_search()

        if self.isSendComplete:
            self.complete.emit(self.dupes)

    def stop(self):
        print("Thread stop called")
        self.requestInterruption()

    def __del__(self):
        self.wait()

    def set_search_params(self, folders, isName, isSize, isHash):
        self.folders = folders
        self.isName = isName
        self.isSize = isSize
        self.isHash = isHash

    def execute_search(self):

        checkedFolders = set()
        allFiles = list()

        #Collect every file in selected folders and sub-folders
        for folder in self.folders:
            if self.isInterruptionRequested():
                self.message.emit("Search Cancelled")
                break
            if path.exists(folder) and path.isdir(folder):
                self.collect_all_files(checkedFolders, folder, allFiles)

        #Emit file count
        self.fileCount = str(len(allFiles))
        self.totalFiles.emit(self.fileCount)
        
        dupes = list()

        #Name is separate from size and hash. Hash will run size first to filter out mismatches faster
        #before running more computationally expensive hash checks
        if self.isName:
            dupes = self.search_hashtable_name(allFiles)

            if self.isSize or self.isHash:
                dupes = self.search_hashtable_also_size(dupes)

                if self.isHash:
                    dupes = self.search_hashtable_also_hash(dupes)
        elif self.isSize or self.isHash:
            dupes = self.search_hashtable_size(allFiles)

            if self.isHash:
                dupes = self.search_hashtable_also_hash(dupes)

        return dupes

    #Use hashtables to find name duplicates
    def search_hashtable_name(self, allFiles):
        fileHash = {}
        dupeHash = {}

        currentFile = 0

        for node in allFiles:
            if self.isInterruptionRequested():
                self.message.emit("Search Cancelled")
                break
            
            currentFile += 1

            self.message.emit("Name Check: {}/{} {}".format(str(currentFile), self.fileCount, node.data_location))

            toAdd = file_node.Node_Hash(node.data_size, node.data_name, node.data_location, False)

            existing = fileHash.get(node.data_name)
            if existing is None:
                fileHash[node.data_name] = toAdd
            else:
                existing.data_duplicates.append(toAdd)

                if dupeHash.get(node.data_name) is None:
                    dupeHash[node.data_name] = existing
        
        dupes = list()

        for dupe in dupeHash:
            dupes.append(dupeHash[dupe])
        
        return dupes

    #Use hashtables to find size duplicates
    def search_hashtable_size(self, allFiles):
        fileHash = {}
        dupeHash = {}

        currentFile = 0

        for node in allFiles:
            if self.isInterruptionRequested():
                self.message.emit("Search Cancelled")
                break
            
            currentFile += 1
            
            self.message.emit("Size Check: {}/{} {}".format(str(currentFile), self.fileCount, node.data_location))

            toAdd = file_node.Node_Hash(node.data_size, node.data_name, node.data_location, False)

            existing = fileHash.get(node.data_size)
            if existing is None:
                fileHash[node.data_size] = toAdd
            else:
                existing.data_duplicates.append(toAdd)

                if dupeHash.get(node.data_size) is None:
                    dupeHash[node.data_size] = existing

        dupes = list()

        for dupe in dupeHash:
            dupes.append(dupeHash[dupe])

        return dupes

    #Use hashtables to find size duplicates after name duplicates have been found
    def search_hashtable_also_size(self, dupes):
        returnDupes = list()

        currentFile = 0
        currentCount = 0
        for dupe in dupes:
            currentCount = currentCount + len(dupe.data_duplicates)
        currentFileCount = str(currentCount)

        for dupe in dupes:

            if self.isInterruptionRequested():
                self.message.emit("Search Cancelled")
                break

            allFiles = self.allFile_from_data_duplicates(dupe.data_duplicates)

            fileHash = {}
            dupeHash = {}

            for node in allFiles:
                currentFile += 1

                self.message.emit("Size Check: {}/{} {}".format(str(currentFile), currentFileCount, node.data_location))

                toAdd = file_node.Node_Hash(node.data_size, node.data_name, node.data_location, False)

                existing = fileHash.get(node.data_size)
                if existing is None:
                    fileHash[node.data_size] = toAdd
                else:
                    existing.data_duplicates.append(toAdd)

                    if dupeHash.get(node.data_size) is None:
                        dupeHash[node.data_size] = existing
            
            for dupe in dupeHash:
                returnDupes.append(dupeHash[dupe])
        
        return returnDupes

    #Use hashtables to find duplicates after size duplicates have been found
    def search_hashtable_also_hash(self, dupes):
        returnDupes = list()

        currentFile = 0
        currentCount = 0
        for dupe in dupes:
            currentCount = currentCount + len(dupe.data_duplicates)
        currentFileCount = str(currentCount)

        for dupe in dupes:

            if self.isInterruptionRequested():
                self.message.emit("Search Cancelled")
                break

            allFiles = self.allFile_from_data_duplicates(dupe.data_duplicates)
            
            fileHash = {}
            dupeHash = {}

            for node in allFiles:
                currentFile += 1

                self.message.emit("Hash Check: {}/{} {}".format(str(currentFile), currentFileCount, node.data_location))

                toAdd = file_node.Node_Hash(node.data_size, node.data_name, node.data_location, True)

                existing = fileHash.get(toAdd.data_hashSum)
                if existing is None:
                    fileHash[toAdd.data_hashSum] = toAdd
                else:
                    existing.data_duplicates.append(toAdd)

                    if dupeHash.get(existing.data_hashSum) is None:
                        dupeHash[existing.data_hashSum] = existing
            
            for dupe in dupeHash:
                returnDupes.append(dupeHash[dupe])
        
        return returnDupes

    #Separate out all files from previously matched nodes
    def allFile_from_data_duplicates(self, duplicates):
        allFiles = list()

        for node in duplicates:
            allFiles.append(node)
        
        for node in allFiles:
            node.data_duplicates = list()
        
        return allFiles
    
    #Recursive collection of all files in given folder
    def collect_all_files(self, checkedFolders, folder, allFiles):

        if self.isInterruptionRequested():
            self.message.emit("Search Cancelled")
            return

        if folder.lower() in checkedFolders:
            self.message.emit("{} has already been processed.".format(folder))
        else:
            self.message.emit("Processing Folder: {}".format(folder))
            checkedFolders.add(folder.lower())
            try:
                with os.scandir(folder) as dir_entries:
                    for entry in dir_entries:
                        if self.isInterruptionRequested():
                            self.message.emit("Search Cancelled")
                            return
                        if entry.is_dir():
                            self.collect_all_files(checkedFolders, entry.path, allFiles)
                        else:
                            toAdd = file_node.Node_Hash(entry.stat().st_size, entry.name, entry.path, False)
                            allFiles.append(toAdd)

            except PermissionError:
                self.accessError.emit("This program cannot Access \n{}\nwithout Admin Rights".format(folder))
                self.isSendComplete = False
                self.requestInterruption()

            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                self.accessError.emit(message)
                self.isSendComplete = False
                self.requestInterruption()