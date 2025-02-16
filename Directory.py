import os
import File
import fnmatch

class Directory :
    def __init__(self, path):
        if not os.path.isdir(path) :
            raise f'{path} is not a directory!'
        self.path = path


    def translate(self):
        for filename in os.listdir(self.path):
            if '.txt' in filename.lower():
                file_path = os.path.join(self.path, filename)
                File.File(file_path).translate_file()