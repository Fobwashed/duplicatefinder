import hashlib
import os

class Node_Hash():
    BUF_SIZE = 65536

    data_size = 0
    data_name = ""
    data_location = ""
    data_hashSum = ""
    data_duplicates = list()

    def __init__(self, size, name, location, isHash):
        self.data_size = size
        self.data_name = name
        self.data_location = location

        self.data_duplicates = list()
        self.data_duplicates.append(self)

        if isHash:
            self.calculate_hash()

    def calculate_hash(self):
        
        md5 = hashlib.md5()
        with open(self.data_location, 'rb') as f:
            while True:
                data = f.read(self.BUF_SIZE)
                if not data:
                    break
                md5.update(data)
        
        self.data_hashSum = md5.hexdigest()

    def swap_primary(self, file_path):
        for entry in self.data_duplicates:
            if entry.data_location == file_path:
                tempSize = entry.data_size
                tempName = entry.data_name
                tempLocation = entry.data_location
                tempHash = entry.data_hashSum
                tempDupes = list()
                for dupe in self.data_duplicates:
                    tempDupes.append(dupe)
                
                entry.data = self.data_size
                entry.data_name = self.data_name
                entry.data_location = self.data_location
                entry.data_hashSum = self.data_hashSum
                entry.data_duplicates.clear()
                entry.data_duplicates.append(entry)

                self.data_size = tempSize
                self.data_name = tempName
                self.data_location = tempLocation
                self.data_hashSum = tempHash
                self.data_duplicates = tempDupes

                break

    def set_primary_folder(self, file_path):
        for entry in self.data_duplicates:
            folder_path = os.path.dirname(entry.data_location)
            if file_path == folder_path:
                self.swap_primary(entry.data_location)
                return        
    
    def delete_file(self, file_path, fb):
        if os.path.exists(file_path):
            fb.statusbar.showMessage("Deleting: {}".format(file_path))
            os.remove(file_path)
            fb.write_to_output_file("Deleted: {}".format(file_path))
        else:
            fb.create_popup_message("File Not Found", "{}\ndoes not exist at given path".format(file_path))
            fb.statusbar.showMessage("{} not found".format(file_path))

    def delete_duplicate(self, file_path, fb):
        
        replacementList = list()
        for entry in self.data_duplicates:
            if entry.data_location != file_path:
                replacementList.append(entry)
        
        self.data_duplicates = replacementList

        self.delete_file(file_path, fb)

    def delete_all_duplicates(self, fb):
        replacementList = list()
        
        for entry in self.data_duplicates:
            if entry.data_location != self.data_location:
                self.delete_file(entry.data_location, fb)
        
        replacementList.append(self)
        self.data_duplicates = replacementList
