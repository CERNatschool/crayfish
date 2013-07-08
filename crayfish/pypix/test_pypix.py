import unittest
from pypix import *

# Dictionaries of frame data, seperated into a list corresponding to cluster
CLUSTERS = [{
    (175,10): 51,
    (176,10): 82,
    (176,12): 9,
    (174,10): 6,
    (174,11): 59,
    (175,11): 117,
    (176,11): 62,
    (174,12): 46,
    (175,12): 128}, {
    (146,41): 32,
    (147,41): 45,
    (146,42): 211,
    (147,42): 89}, {
    (95,176): 81,
    (96,176): 73,
    (92,177): 38,
    (93,177): 27,
    (94,177): 48,
    (91,178): 156,
    (92,178): 16,
    (93,178): 57,
    (91,179): 183}, {
    (147,240): 25,
    (148,240): 219}, {
    (156,253): 22,
    (156,254): 44,
    (157,254): 37,
    (157,255): 21,
    (158,255): 42,
    (159,255): 54}, {
    (75,75): 36 }
]

# Calculate the data for the whole frame by combining the data for each cluster
TEST_FRAME_DATA = dict()
for cluster in CLUSTERS:
    TEST_FRAME_DATA.update(cluster)

class TestFrame(unittest.TestCase):

    # Read test frame
    def setUp(self):
        self.f = Frame.from_file("test_frame.lsc")

    def test_width(self):
        # TEST 1.1
        self.assertEqual(self.f.width, 256)

    def test_height(self):
        # TEST 1.2
        self.assertEqual(self.f.height, 256)

    def test_in_grid(self):
        # Boundary testing
        # Check origin boundary
        # TEST 2.1
        self.assertEqual(self.f.in_grid((0,0)), True, "(0,0) should be in_grid")
        # TEST 2.2
        self.assertEqual(self.f.in_grid((0,-1)), False, "(0,-1) should not be in_grid")
        # Test 2.3
        self.assertEqual(self.f.in_grid((-1,0)), False, "(-1,0) should not be in_grid")

        # Check furthest corner boundary
        width = self.f.width
        height = self.f.height
        # Indices start from 0, so (width, height) should be outside grid
        # Test 2.4
        self.assertEqual(self.f.in_grid((width-1,height-1)), True, "(width-1,height-1) should be in_grid")
        # Test 2.5
        self.assertEqual(self.f.in_grid((width,height-1)), False, "(width,height-1) should not be in_grid")
        # Test 2.6
        self.assertEqual(self.f.in_grid((width-1,height)), False, "(width-1,height) should not be in_grid")

    def test_grid_access(self):
        # Test 3.1
        self.assertEqual(type(self.f[(175,10)]), Hit, "Dictionary access of frame object should return hit object")
        # Test 3.2
        self.assertEqual(self.f[(175,10)].value, 51, "Dictionary access of frame object should return Hit with correct value")
        # assertRaises requires a function, so wrap the invalid co-ordinate in lambda
        # Test 3.3
        self.assertRaises(KeyError, lambda: self.f[(500,500)])

    def test_pixel_values(self):
        # Test 4
        for x in range(self.f.width):
            for y in range(self.f.height):
                self.assertEqual(self.f[(x,y)].value, TEST_FRAME_DATA.get((x,y), 0),
                        "Incorrect pixel value for (%d, %d). Should be %d, got %d"
                            % (x, y, TEST_FRAME_DATA.get((x,y), 0), self.f[(x,y)].value))

    def test_pixels(self):
        # Use assertEqual so order doesn't matter
        # Test 5
        self.assertItemsEqual(self.f.hit_pixels, TEST_FRAME_DATA.keys())

    def test_counts(self):
        # Use assertEqual so order doesn't matter
        # Test 6
        self.assertItemsEqual(self.f.counts, TEST_FRAME_DATA.values())

    def test_min_x(self):
        # Test 7.1
        self.assertEqual(self.f.min_x, 75)
    def test_max_x(self):
        # Test 7.2
        self.assertEqual(self.f.max_x, 176)
    def test_min_y(self):
        # Test 7.3
        self.assertEqual(self.f.min_y, 10)
    def test_max_y(self):
        # Test 7.4
        self.assertEqual(self.f.max_y, 255)

    def test_number_of_neighbours(self):
        # Test 8.1
        self.assertEqual(self.f.number_of_neighbours((175,11)), 8)
        # Test 8.2
        self.assertEqual(self.f.number_of_neighbours((75,75)), 0)
        # Test 8.3
        self.assertEqual(self.f.number_of_neighbours((93,177)), 4)

    def test_get_max_neighbours(self):
        # Test 9
        self.assertEqual(self.f.get_max_neighbours(), (8, [(175, 11)]))

    def test_calculate_clusters(self):
        # Test 10
        # Cluster is done on pixel positions only, so we check each pixel
        # is in the correct cluster
        frame_clusters = self.f.calculate_clusters()
        # Grab copies of the correct and calculated clusters, as lists of sorted pixel coords.
        # Sorting the lists makes sure that Python sees the sublists of frame_cluster_pixels and
        # correct_cluster_pixels as the same.
        frame_cluster_pixels = [cluster.hit_pixels.sort() for cluster in frame_clusters]
        correct_cluster_pixels = [cluster.keys().sort() for cluster in CLUSTERS]
        self.assertItemsEqual(frame_cluster_pixels, correct_cluster_pixels)

# Run the tests
unittest.main(verbosity=2)
