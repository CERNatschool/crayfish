import os
import fnmatch
import pypix

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


    def calculate_aggregate(self, file_extension):
        aggregate_frame = pypix.Frame(256, 256)
        self.get_children(file_extension)
        for folder_path in self.sub_folders:
            file_node = FileNode(folder_path, node_type=DIR)
            folder_frame = calculate_aggregate(file_extension)
            aggregate_frame.clusters.append(folder_frame.clusters)
            for pixel in folder_frame.pixels:
                aggregate_frame[pixel] += folder_frame[pixel]
        for frame_path in self.sub_frames:
            new_frame = Frame.from_file(frame_path)
            aggregate_frame.clusters.append(new_frame.clusters)
            for pixel in new_frame.pixels:
                aggregate_frame[pixel] += folder_frame[pixel]
        return aggregate_frame

    @property
    def name(self):
        return os.path.basename(self.path)

    def __repr__(self):
        return "File Node: " + self.path

