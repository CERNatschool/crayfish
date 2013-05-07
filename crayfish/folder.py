"""
Contains function relating to the lazy evulation of the file tree.
"""
import os
import fnmatch

import pypix
from error_message import display_error_message

class FolderNode():
    """
    A folder node contains a number of FolderNodes (subfolders) and FrameNodes
    (frame files).
    """
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.sub_folders = []
        self.sub_frames = []
        self.expanded = False
        self.aggregate_frame = None

    def get_children(self, file_extension):
        """
        Queries the file system for child folders and child frames.

        Returns a 2-element tuple. The first element of the tuple contains a
        list of FolderNodes (subfolders) and the seconf element contains a list
        of FrameNodes (frames files).
        """
        if not (self.sub_folders or self.sub_frames):
            for item in os.listdir(self.path):
                item_path = os.path.join(self.path, item)
                # If it is a folder add it to the tree
                if os.path.isdir(item_path):
                    self.sub_folders.append(FolderNode(item_path))
                # If it is a frame with the correct extension add it to the tree
                elif fnmatch.fnmatch(item, file_extension):
                    new_frame = FrameNode(item_path)
                    if new_frame.loaded_correctly: # If it loaded correctly
                        self.sub_frames.append(new_frame)
        return self.sub_folders, self.sub_frames

    def calculate_aggregate(self, file_extension):
        """
        Calculates the aggregate frame from a depth-first inspection of the file
        tree.

        Returns the aggregate frame
        """
        aggregate_frame = pypix.Frame(256, 256)
        self.get_children(file_extension)
        # For each sub_folder call its aggregate method and add its
        # clusters/pixels to the aggregate frame
        for folder_path in self.sub_folders:
            folder_frame = folder_path.calculate_aggregate(file_extension)
            aggregate_frame.clusters += folder_frame.clusters
            for pixel in folder_frame.hit_pixels:
                aggregate_frame[pixel] = pypix.Hit(aggregate_frame[pixel].value + folder_frame[pixel].value)
        # For each sub frame calculate its clusters if not already calculated
        # and add these clusters (and the frame's pixels) to the aggregate frame
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
        """
        Returns the filename of the folder
        """
        return os.path.basename(self.path)

class FrameNode():
    """
    Contains a frame and is responsible for its loading
    """
    def __init__(self, path):
        self.path = path
        self.loaded_correctly = True
        try:
            self.frame = pypix.Frame.from_file(os.path.abspath(path))
        except:
            display_error_message("Error Reading File", "Couldn't read file: %s \nPlease check the formatting." % path)
            self.loaded_correctly = False
            return

    @property
    def name(self):
        """
        Returns the filename of the frame
        """
        return os.path.basename(self.path)
