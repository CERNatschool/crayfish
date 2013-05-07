"""
Contains the classification aglorithms that are available to the system.
"""
from collections import Counter

import wx
from wx.lib.dialogs import ScrolledMessageDialog

import pypix
from error_message import display_error_message

# The algorithm table maps a natural algorithm name to an algorithm class
algorithm_table = {}

def algorithm(name):
    """
    A function decorator that is used to add an algorithm's Python class to the
    algorithm_table.

    Args:
        A human readable label for the algorithm that is used to identify it in
        the GUI
    """
    def decorator(class_):
        algorithm_table[name] = class_
        return class_
    return decorator


class MLAlgorithm(object):
    """
    A base class for machine learing algorithms
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.is_trained = False

    def get_display_panel(self, parent):
        """
        Return the display panel containing algorithm settings. In this ML base
        class the display contains the button "Train", "Classify" and "Info".
        The idea is that this is extended by the sub class.

        Returns a 2-element tuple. The first element is the panel and the
        second element is its sizer.
        """
        panel = wx.Panel(parent)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(v_sizer)
        info_button = wx.Button(panel, label="Info")
        train_button = wx.Button(panel, label="Train")
        classify_button = wx.Button(panel, label="Classify")

        panel.Bind(wx.EVT_BUTTON, self.on_info, info_button)
        panel.Bind(wx.EVT_BUTTON, self.on_train, train_button)
        panel.Bind(wx.EVT_BUTTON, self.on_classify, classify_button)

        v_sizer.Add(info_button, 0, wx.TOP | wx.ALIGN_CENTRE, 5)
        v_sizer.Add(train_button, 0, wx.TOP | wx.ALIGN_CENTRE, 5)
        v_sizer.Add(classify_button, 0, wx.TOP | wx.ALIGN_CENTRE, 5)
        return panel, v_sizer

    def on_train(self, evt):
        """
        Prompts the user to select a training file to train the algorithm. This
        class then checks to see if the training file is compatable with this
        version of Crayfish and then it passes the data to to sub class so to
        train itself.
        """
        dialog =  wx.FileDialog(None, message="Select training file")
        if dialog.ShowModal() == wx.ID_OK:
            with open(dialog.GetPath()) as f:
                data = f.readlines()
                header = data[0].strip().split(",")[2:]
                missing_items = []
                for item in header:
                    if item not in pypix.attribute_table:
                        missing_items.append(item)
                if missing_items:
                    display_error_message("Missing Properties",
                            "The training file contains the following properties that cannot be calculated with this installation of Crayfish: "
                            + ", ".join(missing_items) + ".\nThis may prevent certain algorithms from functioning correctly or at all.")
            self.train(data)

    def on_classify(self, evt):
        """
        Checks to see if the algorithm has been trained and that there is a
        frame available with clusters to be classified, before calling the
        sub class algorithm to classify each cluster.
        """
        if not self.is_trained:
            display_error_message("Classification","Algorithm not yet trained. Please select a training file by clicking train.")
            return
        if not self.main_window.frame:
            display_error_message("Classification","Please select a frame or aggregate a subfolder to classify")
            return
        for cluster in self.main_window.frame.clusters:
            self.classify(cluster)

    def on_info(self, evt):
        """""
        Displays an info dialog with information about the algorithm, reading
        the information from the class docstring.
        """
        wx.lib.dialogs.ScrolledMessageDialog(None, type(self).__doc__, "Algorithm Info").Show()


@algorithm("K Nearest Neighbours")
class KNN(MLAlgorithm):
    """
    This algorithm finds closest k points to the cluster to be
    classified when the properties of the training data and the
    cluster to be classified are plotted on an n-dimensional graph.
    The algorithm then assigns the modal class of these k points to
    the cluster to be classified.

    ==Params==
    k -- The number of closest points to inspect
    Checkboxes -- Checked attributes will be include in calculations
    """
    def __init__(self, main_window):
        super(KNN, self).__init__(main_window)
        self.training_data = []
        self.functions = []

    def get_display_panel(self, parent):
        """
        Returns the settings panel for the algorithm
        """
        panel, v_sizer = super(KNN, self).get_display_panel(parent)
        k_label = wx.StaticText(panel, label = "K")

        self.k_input = wx.SpinCtrl(panel, value="5")
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(k_label, 0, wx.TOP, 5)
        h_sizer.Add(self.k_input)
        v_sizer.Add(h_sizer, 0, wx.ALIGN_CENTRE | wx.TOP, 10)

        dim_selector_label = wx.StaticText(panel, label="Include Dimensions:")
        self.dim_selector = wx.CheckListBox(panel, size=(200, 120))
        v_sizer.Add(dim_selector_label, 0, wx.ALIGN_CENTRE | wx.TOP, 5)
        v_sizer.Add(self.dim_selector, 0, wx.ALIGN_CENTRE, wx.TOP, 2)
        return panel

    @property
    def k(self):
        """
        Returns the value of k set in the settings panel.

        In production use of this algorithm the property K of a class instance
        will be set explicitly as required, eg. classifier.k =5

        Using the property decorator makes this transparent to the interface,
        the algorithm can access it using self.k whether it calls this function
        or it is explicitly defined.
        """
        return self.k_input.GetValue()

    def train(self, data):
        """
        Trains the algorithm using data, which should be a list of CSV records,
        with the first row being a header, with each header (bar the first two)
        being used as a key to attribute_table to retrieve the appropiate
        attribute calculation function.

        The first entry of each row corresponds to the cluster UUID and is
        ignored as it is not useful for training. The second entry is the
        cluster type which is of course used in the training process.
        """
        self.training_data = []
        self.dim_selector.Clear()
        # Load attributes from header row, ignoring first two entries (see
        # docsttring)
        attributes = data[0].strip().split(",")[2:]
        # Set dimensions checkbox items
        self.dim_selector.Set(attributes)
        self.functions = [pypix.attribute_table[attr][0] for attr in attributes]
        # [1:] To ignore header row and UUID column
        rows = [row.strip().split(",")[1:] for row in data[1:]]
        # Add data to training_data list, whose elements
        # have format [class, (properties)]
        for row in rows:
            # Head of list `[0]` - is the classification,
            # the tail `[1:]` contains the properties
            self.training_data.append((row[0], tuple([float(i) for i in row[1:]])))
        # Set appropialte limits for k input selector, if we k_input is defined
        # (ie. alogorithm is being run in the GUI)
        if hasattr(self, "k_input"):
            self.k_input.SetRange(1,len(self.training_data))
        self.is_trained = True

    def classify(self, cluster):
        """
        Classify cluster
        The `algorithm_class` attribute of cluster is updated to reflect the
        estimated cluster
        """
        square_distances = []
        for training_datum in self.training_data:
            # Sum the squared differences between the training cluster and cluster
            # to be classified for each dimension if the dimension has been
            # specified.
            square_distance = sum([(value - self.functions[i](cluster))**2
                                    for i, value in enumerate(training_datum[1])
                                        if self.dim_selector.IsSelected(i)])
            square_distances.append((training_datum[0], square_distance))
        # Find closest k points
        square_distances.sort(key=lambda x: x[1])
        nearest_k = square_distances[0:self.k]
        # Extract types of nearest k items
        nearest_k_types = [item[0] for item in nearest_k]
        # Counter.most_common returns a list of (item, frequency)
        # Ask for the most common, take the 0th one (there may be more than one
        # with the same frequency) and then take the 0th item of this tuple,
        # which is the modal class of the nearest k training points.
        cluster.algorithm_class = Counter(nearest_k_types).most_common(1)[0][0]

@algorithm("ID3")
class ID3(MLAlgorithm):

    def get_display_panel(self, parent):
        panel, v_sizer = super(ID3, self).get_display_panel(parent)
        return panel
