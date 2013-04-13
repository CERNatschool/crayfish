import os
import fnmatch

DIR = 0
FRAME = 1


class FileNode():
    
    def __init__(self, path, node_type = DIR):
        self.path = os.path.abspath(path)
        self.node_type = node_type
        self.sub_folders = []
        self.sub_files = []
        self.expanded = False

    def get_children(self, file_extension):
        if not self.sub_folders or not self.sub_files:
            for item in os.listdir(self.path):
                item_path = os.path.join(self.path, item)
                if os.path.isdir(item_path):
                    self.sub_folders.append(FileNode(item_path))
                elif fnmatch.fnmatch(item, file_extension):
                    self.sub_files.append(FileNode(item_path, node_type=FRAME))
        return self.sub_folders, self.sub_files

    @property
    def name(self):
        return os.path.basename(self.path)

    def __repr__(self):
        return "File Node: " + self.path

