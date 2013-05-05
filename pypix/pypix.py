class Hit(object):
    def __init__(self, value,cluster=None):
        self.value = value
        self.cluster = None

    def __str__(self):
        return str(self.value)

class PixelGrid(dict):

    def __init__(self, width, height, data=[]):
        super(PixelGrid, self).__init__(data)
        self.width = width
        self.height = height

    def __missing__(self, key):
        if self.in_grid(key):
            return Hit(0)
        else:
            raise KeyError("Point outside of PixelGrid")

    def in_grid(self, pixel):
        # Strict inequalities as x,y start from 0
        x, y = pixel
        return 0 <= x < self.width and 0 <= y < self.height

    @property
    def hit_pixels(self):
        return self.keys()

    @property
    def counts(self):
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
        neighbours = {}
        for pixel in self.hit_pixels:
            num_neighbours = self.number_of_neighbours(pixel)
            if num_neighbours in neighbours:
                neighbours[num_neighbours].append(pixel)
            else:
                neighbours[num_neighbours] = [pixel]
        max_neighbours = max(neighbours)
        return max_neighbours, neighbours[max_neighbours]

        # ==Alternative Algorithm==
        # neighbours = [(pixel, self.number_of_neighbours(pixel))
        #         for pixel in self.hit_pixels]
        # max_neighbours = max(neighbours, key = lambda x: x[1])[1]
        # return max_neighbours, [pixel[0] for pixel in neighbours
        #         if pixel[1] == max_neighbours]

    def render_energy(self):
        grid = [[0]*self.width for _ in range(self.height)]
        for pixel in self.hit_pixels:
            x, y = pixel
            grid[y][x] = self[pixel].value
        return grid

    def render_energy_zoomed(self, min_x = None, min_y = None, max_x = None,
            max_y = None):
        if not min_x: min_x = self.min_x
        if not max_x: max_x = self.max_x
        if not min_y: min_y = self.min_y
        if not max_y: max_y = self.max_y
        return [[self[x,y].value
                for x in range(min_x, max_x+1)] for y in range(min_y, max_y+1)]

class Frame(PixelGrid):

    def __init__(self,width=256, height=256, data=[]):
        super(Frame, self).__init__(width, height, data)
        self.clusters = []

    @staticmethod
    def from_file(filepath, file_format = "lsc"):
        frame = Frame(256,256)
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
        for pixel in self.hit_pixels:
            self[pixel].cluster = None
        self.clusters = []
        for pixel in self.hit_pixels:
            if not self[pixel].cluster:
                new_cluster = Cluster(256, 256)
                self.clusters.append(new_cluster)
                new_cluster.add(pixel, self[pixel])
                self._add_neighbouring_pixels(new_cluster)

    def _add_neighbouring_pixels(self, cluster):
        for pixel in self.hit_pixels:
            if not self[pixel].cluster and cluster.is_neighbour(pixel):
                cluster.add(pixel, self[pixel])
                # Cluster now has more pixels, so check for new neighbours
                self._add_neighbouring_pixels(cluster)

    def get_closest_cluster(self, point):
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


class Cluster(PixelGrid):

    def add(self, pixel, hit):
        hit.cluster = self
        self[pixel] = hit

    def is_neighbour(self, other_pixel):
        for pixel in self.hit_pixels:
            if are_neighbours(pixel, other_pixel):
                return True
        return False

    @property
    def cluster_width(self):
        return self.max_x - self.min_x

    @property
    def cluster_height(self):
        return self.max_y - self.min_y


def are_neighbours(pixel1,pixel2):
    x1, y1 = pixel1
    x2, y2 = pixel2
    return abs(x2-x1) <= 1 and abs (y2-y1) <= 1

from attributes import *
