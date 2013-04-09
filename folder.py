import os

class Folder():

    def __init__(self, path):
        if (not os.path.exists(path)) or (not os.path.isdir(path)):
            raise IOError("Not a directory: \"%s\"" % path)
        self.path = os.path.abspath(path)
        self.build_subtree()

    def build_subtree(self):
        self.sub_folders = []
        self.files = []
        for item in os.listdir(self.path):
            item_path = os.path.join(self.path, item)
            if os.path.isdir(item_path):
                self.sub_folders.append(Folder(item_path))
            else:
                self.files.append(item_path)
    
    def __repr__(self):
        return self.path
