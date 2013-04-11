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
    def centre_of_mass(self):
        weighted_hits = [tuple([self[hit] * coord for coord in hit])
                for hit in self.hits]
        x_coords, y_coords = zip(*weighted_hits)
        total_weight = float(self.volume)
        return (sum(x_coords)/total_weight, sum(y_coords)/total_weight)

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
