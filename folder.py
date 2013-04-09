import os
import fnmatch

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
            elif fnmatch.fnmatch(item,"*.bmp"):
                self.files.append(item_path)

    @property
    def name(self):
        return os.path.basename(self.path)
    
    def add_children(self, file_tree, file_tree_node):
        for folder in self.sub_folders:
            new_node = file_tree.AppendItem(file_tree_node, folder.name)
            folder.add_children(file_tree, new_node)
        for item in self.files:
            file_tree.AppendItem(file_tree_node, os.path.basename(item))

    
    def __repr__(self):
        return self.path
