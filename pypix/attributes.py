import hashlib

from .pypix import *
# @attribute(Class, Text Label, Plottable = False, Trainable = Plottable)
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
    return hashlib.sha1(self.ascii_grid).hexdigest()
