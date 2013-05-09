"""
Attributes designed for viewing, plotting and training in the
Crayfish UI are not defined here but instead in pypix/attributes.py

Definitions:
    Hit: A hit is any pixel with non zero value

    Pixel: A pixel is any (x,y) tuple co-ordinate, usually of a hit

    Count: A count is an integer corresponding to the value of a hit

"""
from collections import OrderedDict

class Hit(object):
    """
    A Hit object denotes a hit pixel and has the following properties:

    value: The value of the pixel
    cluster: The cluster that the pixel belongs to
    """
    def __init__(self, value, cluster=None):
        self.value = value
        self.cluster = None

    # For debug purposes
    def __str__(self):
        return str(self.value)

class PixelGrid(dict):
    """
    A base class that frame and cluster derive from. It contains methods
    applicable to any grid of pixels. Optional data argument may be a
    dictionary mapping (x,y) tuples to Hit objects
    """
    # PixelGrid dictionary effectively implements a  sparse array. As most of
    # the values of the 256*256 frame matrix will be 0, this greatly reduces
    # the memory footprint of the programming, but does require slightly more
    # processing to access each item in the array. If there is an attempt to
    # retrieve a pixel co-ord that is not in the dictionary, the method
    # __missing__ is called, which returns 0 if the pixel coords lie within the
    # grid, or otherwise raise a KeyError.
    def __init__(self, width, height, data=[]):
        super(PixelGrid, self).__init__(data)
        self.width = width
        self.height = height

    def __missing__(self, key):
        # If we do not have an explicit Hit value for key (x,y), check to see
        # if it appears i=within the grid. If so, return a Hit object with
        # value 0
        if self.in_grid(key):
            return Hit(0)
        else:
            raise KeyError("Point outside of PixelGrid")

    def in_grid(self, pixel):
        """
        Return True if pixel is within the pixel grid

        Args:
            pixel: (x,y)
        """
        # Strict inequalities as x,y start from 0
        x, y = pixel
        return 0 <= x < self.width and 0 <= y < self.height

    @property
    def hit_pixels(self):
        """
        Returns a list of the locations of pixels showing hits
        """
        return self.keys()

    @property
    def counts(self):
        """
        Returns a list of hit counts
        """
        return [pixel.value for pixel in self.values()]

    @property
    def min_x(self):
        return min([pixel[0] for pixel in self.hit_pixels])
    @property
    def max_x(self):
        return max([pixel[0] for pixel in self.hit_pixels])
    @property
    def min_y(self):
        return min([pixel[1] for pixel in self.hit_pixels])
    @property
    def max_y(self):
        return max([pixel[1] for pixel in self.hit_pixels])

    def number_of_neighbours(self, pixel):
        x, y = pixel
        x_values = [x + offset for offset in [-1,0,1]]
        y_values = [y + offset for offset in [-1,0,1]]
        return sum([1 for i in x_values for j in y_values
                if self.in_grid((i,j)) and (i,j) != pixel and self[i,j].value])

    def get_max_neighbours(self):
        """
        Return a 2-element tuple. The first item is a the most neighbours any
        one particular pixel has, and the second item is a list of the (x,y)
        locations of every pixel that has this many neighbours
        """
        neighbours = {}
        for pixel in self.hit_pixels:
            num_neighbours = self.number_of_neighbours(pixel)
            if num_neighbours in neighbours:
                neighbours[num_neighbours].append(pixel)
            else:
                neighbours[num_neighbours] = [pixel]
        max_neighbours = max(neighbours)
        return max_neighbours, neighbours[max_neighbours]

        # ==Alternative Algorithm Implementation==
        # neighbours = [(pixel, self.number_of_neighbours(pixel))
        #         for pixel in self.hit_pixels]
        # max_neighbours = max(neighbours, key = lambda x: x[1])[1]
        # return max_neighbours, [pixel[0] for pixel in neighbours
        #         if pixel[1] == max_neighbours]

    def render_energy(self):
        """
        Renders a grid with each value corresponding to the ernergy of the
        relevant pixel.
        """
        grid = [[0]*self.width for _ in range(self.height)]
        for pixel in self.hit_pixels:
            x, y = pixel
            grid[y][x] = self[pixel].value
        return grid

    def render_energy_zoomed(self, min_x = None, min_y = None, max_x = None, max_y = None):
        """
        Renders a clipped grid with each value corresponding to the energy of
        the relevant pixel.
        """
        if not min_x: min_x = self.min_x
        if not max_x: max_x = self.max_x
        if not min_y: min_y = self.min_y
        if not max_y: max_y = self.max_y
        return [[self[x,y].value
                for x in range(min_x, max_x+1)] for y in range(min_y, max_y+1)]


class Frame(PixelGrid):
    """
    A frame object corresponds to the data in a frame file.
    """
    def __init__(self,width=256, height=256, data=[]):
        super(Frame, self).__init__(width, height, data)
        self.clusters = []

    @staticmethod
    def from_file(filepath, file_format = "lsc"):
        """
        Returns a new frame with data read from a lsc formatted file
        """
        frame = Frame()
        if file_format == "lsc":
            with open(filepath) as f:
                try:
                    for line in f:
                        if line[:2] == "//":
                            continue
                        pixel, count = line.strip().split()
                        pixel = tuple([int(coord) for coord in pixel.split(",")])
                        frame[pixel] = Hit(int(count))
                except:
                    raise Exception("Could not read " + filepath
                            + "\n Please check the formatting."  )
        else:
            raise Exception("File format not supported: " + file_format)
        return frame

    def calculate_clusters(self):
        """
        Called to calculated clusters. This is an expensive operation that is
        cached, ie. calling this function will not recalculate clusters if they
        have already been calculated.

        Returns the list of clusters
        """
        if not self.clusters:
            for pixel in self.hit_pixels:
                self[pixel].cluster = None
            self.clusters = []
            for pixel in self.hit_pixels:
                if not self[pixel].cluster:
                    new_cluster = Cluster(256, 256)
                    self.clusters.append(new_cluster)
                    new_cluster.add(pixel, self[pixel])
                    self._add_neighbouring_pixels(new_cluster)
        return self.clusters

    def _add_neighbouring_pixels(self, cluster):
        """
        Called recursively whenever a new pixel is added to a cluster. It
        searches the the list of pixels and if an unclustered pixel neghbours
        the cluster it adds it to the cluster and calls the function again to
        check for more neighbours.
        """
        for pixel in self.hit_pixels:
            if not self[pixel].cluster and cluster.is_neighbour(pixel):
                cluster.add(pixel, self[pixel])
                # Cluster now has more pixels, so check for new neighbours
                self._add_neighbouring_pixels(cluster)

    def get_closest_cluster(self, point):
        """
        Returns the closest clusters to a pixel
        """
        if not self.clusters:
            self.calculate_clusters()
        x, y = point
        square_distances = []
        for pixel in self.hit_pixels:
            pixel_x, pixel_y = pixel
            x_diff = pixel_x - x
            y_diff = pixel_y - y
            square_distances.append((self[pixel].cluster, x_diff**2 + y_diff**2))
        return min(square_distances, key=lambda x: x[1])[0]

    def get_training_rows(self):
        """
        Outputs a training row for each manually classified cluster.
        """
        return "\n".join([cluster.get_training_row() for cluster in self.clusters if cluster.manual_class != "Unclassified"])

    def load_training_data(self, data):
        """
        Load manual classes from data.

        Args:
            Data: A dictionary mapping cluster UUIDs to classes
        """
        for UUID_key in data:
            for cluster in self.clusters:
                if UUID_key == cluster.UUID:
                    cluster.manual_class = data[UUID_key]

class Cluster(PixelGrid):
    """
    A cluster object corresponds to one cluster. Its properties width and
    height are the same as its containing frame. To find the width and height
    of the cluster use cluster_width and cluster_height.
    """
    def __init__(self, width, height):
        super(Cluster, self).__init__(width, height)
        self.manual_class = "Unclassified"
        self.algorithm_class = "Unclassified"

    def add(self, pixel, hit):
        """
        Adds a hit to the cluster, and sets the cluster property of the hit to
        this cluster.
        """
        hit.cluster = self
        self[pixel] = hit

    def is_neighbour(self, other_pixel):
        """
        Returns True if other_pixel neighbours any of the pixels in the
        cluster.
        """
        for pixel in self.hit_pixels:
            if are_neighbours(pixel, other_pixel):
                return True
        return False

    @property
    def cluster_width(self):
        """
        The actual width of the cluster.
        """
        return self.max_x - self.min_x +1

    @property
    def cluster_height(self):
        """
        The actual height of the cluster
        """
        return self.max_y - self.min_y + 1

    @property
    def ascii_grid(self):
        """
        Returns an ascii grid representation of the cluster, with rows
        separated by new line characters and columns separated by tabs.
        """
        grid = [[0] * self.cluster_width for _ in range(self.cluster_height)]
        for pixel in self.hit_pixels:
            x, y = pixel
            grid[y - self.min_y][x - self.min_x] = self[pixel].value
        # User group convention to have lower origin, so flip
        grid.reverse()
        return "\n".join(["\t".join([str(value) for value in row]) for row in grid])

    def get_training_row(self):
        """
        Returns a training row corresponding to this cluster.
        """
        record = [self.UUID, self.manual_class]
        record += [str(attribute_table[attr][0](self)) for attr in attribute_table
                if isinstance(self, attribute_table[attr][1]) and
                    attribute_table[attr][3]]
        return ",".join(record)


def are_neighbours(pixel1,pixel2):
    """
    Return True if if each of the x/y coords if pixel1 and pixel2 differ by two
    or less, ie. each pixel not at the edge has 9 neighbours (including
    itself).
    """
    x1, y1 = pixel1
    x2, y2 = pixel2
    return abs(x2 - x1) <= 1 and abs (y2 - y1) <= 1

# Use an ordered dict so that the table maintains the order in which
# attributes are defined in attributes.py
attribute_table = OrderedDict()

def attribute(class_, name, plottable=False, trainable=None):
    """
    A function decorator that adds a function to the attribute table along with
    its applicable Python object class that it can be called on. It also adds
    to the attribute table whether it is plottable or trainable.

    It then applies the function as a property to the relevant class so that the
    item is accessible in the same manner as any other property as::
        object.property

    Args:
        class\_: The class that the attribute function may be called on
        instances of

        name: A human readable label for the attribute that is used in the GUI

        plottable: Whether the attribute is plottable on a graph

        trainable: Whether the attribute can be used in machine learning
        algorithms (defaults to the value of plottable)
    """
    if not trainable:
        trainable = plottable
    def decorator(function):
        attribute_table[name] = (function, class_, plottable, trainable)
        setattr(class_, function.__name__, property(function))
        return function
    return decorator

# Import attributes
from attributes import *
