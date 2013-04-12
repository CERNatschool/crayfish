class PixelGrid(dict):

    def __missing__(self, key):
        if self.in_grid(key):
            return 0
        else:
            raise KeyError("Point outside of PixelGrid")

    def in_grid(self, pixel):
        # Strict inequalities as x,y start from 0
        x, y = pixel
        return 0 <= x < self.width and 0 <= y < self.height

    @property
    def hits(self):
        return self.keys()

    @property
    def num_hits(self):
        return len(hit_pixels)

    @property
    def counts(self):
        return self.values()

    @property
    def volume(self):
        return sum(self.counts)

    @property
    def max_count(self):
        return max(self.counts)

    @property
    def mean_count(self):
        return float(self.max_count)/self.num_hits

    @property
    def min_x(self):
        return min([hit[0] for hit in self.hits])
    @property
    def max_x(self):
        return max([hit[0] for hit in self.hits])
    @property
    def min_y(self):
        return min([hit[1] for hit in self.hits])
    @property
    def max_y(self):
        return max([hit[1] for hit in self.hits])

    def number_of_neighbours(self, pixel):
        x, y = pixel
        x_values = [x + offset for offset in [-1,0,1]]
        y_values = [y + offset for offset in [-1,0,1]]
        return sum([1 for i in x_values for j in y_values
                if self.in_grid((i,j)) and (i,j) != pixel and self[i,j]])

    def get_max_neighbours(self):
        neighbours = {}
        for pixel in self.hits:
            num_neighbours = self.number_of_neighbours(pixel)
            if num_neighbours in neighbours:
                neighbours[num_neighbours].append(pixel)
            else:
                neighbours[num_neighbours] = [pixel]
        max_neighbours = max(neighbours)
        return max_neighbours, neighbours[max_neighbours]

        # ==Alternative Algorithm==
        # neighbours = [(pixel, self.number_of_neighbours(pixel))
        #         for pixel in self.hits]
        # max_neighbours = max(neighbours, key = lambda x: x[1])[1]
        # return max_neighbours, [pixel[0] for pixel in neighbours
        #         if pixel[1] == max_neighbours]

class Frame(PixelGrid):

    def calculate_clusters(self):
        self.clusters = []

    @staticmethod
    def from_file(filepath, file_format = "lsc"):
        frame = Frame()
        if file_format == "lsc":
            with open(filepath) as f:
                for line in f:
                    if line[:2] == "//":
                        continue
                    pixel, count = line.strip().split()
                    pixel = tuple([int(coord) for coord in pixel.split(",")])
                    frame[pixel] = count
            frame.width = 256
            frame.height = 256
        else:
            raise Exception("File format not supported: " + file_format)
        return frame

class Cluster(PixelGrid):

    @property
    def width(self):
        return self.max_x

    @property
    def width(self):
        return self.max_y

    @property
    def geometric_centre(self):
        return (self.width/2.0, self/height/2.0)

    @property
    def centre_of_mass(self):
        weighted_hits = [tuple([self[hit] * coord for coord in hit])
                for hit in self.hits]
        x_coords, y_coords = zip(*weighted_hits)
        total_weight = float(self.volume)
        return (sum(x_coords)/total_weight, sum(y_coords)/total_weight)

    @property
    def radius(self):
        # Call centre of mass once to save computing multiple times
        cofm_x, cofm_y = self.centre_of_mass
        distances_squared = []
        for hit in self.hits:
            x_diff = hit[0] - cofm_x
            y_diff = hit[1] - cofm_x
            distances_squared.append(x_diff**2 + y_diff**2)
        return max(distances_squared)**0.5
