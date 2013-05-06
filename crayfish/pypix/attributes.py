# The attribute list
#
# To add an attribute define it as a standard function here.
#
# Then apply the attribute function decorator::
#
#     @attribute(object_type, name, plottable, trainable)
#
# Where:
#     object_type is the type of object that the attribute is applicable to,
#     either Frame or Cluster, or PixelGrid for either.
#
#     name is a human readable label which is used to identify it in the GUI
#
#     plottable is a boolean that describes whether the attribute is polottable on
#     a graph (may be omitted, defualts to false)
#
#     plottable is a boolean that describes whether the attribute is usable in
#     machine learning algorithms (may be omitted, defualts to the value of
#     plottable)
#
#
# The attribute functions may be defined in any order. The order in which they are
# defined here is the order in which they will appear in the GUI
"""
.. note:: Although these functions appear in the documentation as functions, they are
    converted into properties at runtime so do not need to be called with
    parenthesis.
"""
import hashlib

from .pypix import *
# ============== Attributes begin here and maintain order ===============

@attribute(PixelGrid, "No. of hits", True)
def number_of_hits(self):
    return len(self.hit_pixels)

@attribute(PixelGrid, "Volume", True)
def volume(self):
    return sum(self.counts)

@attribute(PixelGrid, "Mean count", True)
def mean_count(self):
    return float(self.volume)/self.number_of_hits

@attribute(PixelGrid, "Count std. dev.", True)
def standard_deviation(self):
    mean_square = (float(sum([count**2 for count in self.counts]))
            /self.number_of_hits)
    square_mean = self.mean_count**2
    return (mean_square - square_mean)**0.5

@attribute(Frame, "No. of clusters")
def number_of_clusters(self):
    if not self.clusters:
        self.calculate_clusters()
    return len(self.clusters)

@attribute(Cluster, "Geo. centre")
def geometric_centre(self):
    return (self.cluster_width/2.0 + self.min_x,
            self.cluster_height/2.0 + self.min_y)

@attribute(Cluster, "C. of mass")
def centre_of_mass(self):
    weighted_hits = [tuple([self[hit].value * coord for coord in hit])
            for hit in self.hit_pixels]
    x_coords, y_coords = zip(*weighted_hits)
    total_weight = float(self.volume)
    return (sum(x_coords)/total_weight, sum(y_coords)/total_weight)

@attribute(Cluster, "Radius", True)
def radius(self):
    # Call centre of mass once to save computing multiple times
    cofm_x, cofm_y = self.centre_of_mass
    distances_squared = []
    for pixel in self.hit_pixels:
        x_diff = pixel[0] - cofm_x
        y_diff = pixel[1] - cofm_y
        distances_squared.append(x_diff**2 + y_diff**2)
    return max(distances_squared)**0.5

@attribute(Cluster, "Most neighbours", True)
def most_neighbours(self):
    return self.get_max_neighbours()[0]

@attribute(Cluster, "UUID")
def UUID(self):
    """
    Return the cluster UUID
    (SHA1 digest of the cluster.ascii_grid representation).
    """
    return hashlib.sha1(self.ascii_grid).hexdigest()
