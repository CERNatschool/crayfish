import os
import fnmatch

import pypix
from error_message import display_error_message

class FolderNode():
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.sub_folders = []
        self.sub_frames = []
        self.expanded = False
        self.aggregate_frame = None

    def get_children(self, file_extension):
        if not (self.sub_folders or self.sub_frames):
            for item in os.listdir(self.path):
                item_path = os.path.join(self.path, item)
                if os.path.isdir(item_path):
                    self.sub_folders.append(FolderNode(item_path))
                elif fnmatch.fnmatch(item, file_extension):
                    new_frame = FrameNode(item_path)
                    if new_frame.loaded_correctly:
                        self.sub_frames.append(new_frame)
        return self.sub_folders, self.sub_frames

    def calculate_aggregate(self, file_extension):
        aggregate_frame = pypix.Frame(256, 256)
        self.get_children(file_extension)
        for folder_path in self.sub_folders:
            folder_frame = folder_path.calculate_aggregate(file_extension)
            aggregate_frame.clusters += folder_frame.clusters
            for pixel in folder_frame.hit_pixels:
                aggregate_frame[pixel] = pypix.Hit(aggregate_frame[pixel].value + folder_frame[pixel].value)
        for frame_file in self.sub_frames:
            frame = frame_file.frame
            if not frame.clusters:
                frame.calculate_clusters()
            aggregate_frame.clusters += frame.clusters
            for pixel in frame.hit_pixels:
                aggregate_frame[pixel] = pypix.Hit(aggregate_frame[pixel].value + frame[pixel].value)
        return aggregate_frame

    @property
    def name(self):
        return os.path.basename(self.path)

class FrameNode():
    def __init__(self, path):
        self.path = path
        self.loaded_correctly = True
        try:
            self.frame = pypix.Frame.from_file(os.path.abspath(path))
        except:
            display_error_message("Error reading file", "Couldn't read file: %s \nPlease check the formatting." % path)
            self.loaded_correctly = False
            return



    @property
    def name(self):
        return os.path.basename(self.path)