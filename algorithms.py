from collections import Counter

import wx

from error_message import *

import pypix

algorithm_table = {}

def algorithm(name):
    def decorator(class_):
        algorithm_table[name] = class_
        return class_
    return decorator


class MLAlgorithm(object):

    def __init__(self, main_window):
        self.main_window = main_window
        self.is_trained = False

    def get_display_panel(self, parent):
        panel = wx.Panel(parent)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(v_sizer)
        train_button = wx.Button(panel, label="Train")
        classify_button = wx.Button(panel, label="Classify")
        panel.Bind(wx.EVT_BUTTON, self.on_train, train_button)
        panel.Bind(wx.EVT_BUTTON, self.on_classify, classify_button)
        v_sizer.Add(train_button, 0, wx.TOP | wx.ALIGN_CENTRE, 5)
        v_sizer.Add(classify_button, 0, wx.TOP | wx.ALIGN_CENTRE, 5)
        return panel, v_sizer

    def on_train(self, evt):
        dialog =  wx.FileDialog(None, message="Select training file")
        if dialog.ShowModal() == wx.ID_OK:
            with open(dialog.GetPath()) as f:
                data = f.readlines()
                header = data[0].strip().split(",")[2:]
                for item in header:
                    missing_items = []
                    if item not in pypix.attribute_table:
                        missing_items.append(item)
                    if missing_items:
                        display_error_message("Missing Properties",
                                "The training file contains the following properties that cannot be calculated with this installation of Crayfish, which may cause certain algorithms to fail: "
                                + ",".join(missing_items))
                self.train(data)

    def on_classify(self, evt):
        if not self.is_trained:
            display_error_message("Classification","Algorithm not yet trained. Pleas select a training file by clicking train.")
            return
        if not self.main_window.frame:
            display_error_message("Classification","Please select a frame or aggregate a subfolder to classify")
            return
        for cluster in self.main_window.frame.clusters:
            self.classify(cluster)

@algorithm("K Nearest Neighbours")
class KNN(MLAlgorithm):

    def __init__(self, main_window):
        super(KNN, self).__init__(main_window)
        self.training_data = []
        self.functions = []

    def get_display_panel(self, parent):
        panel, v_sizer = super(KNN, self).get_display_panel(parent)
        k_label = wx.StaticText(panel, label = "K")
        self.k_input = wx.SpinCtrl(panel, value="5")
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(k_label, 0, wx.TOP, 5)
        h_sizer.Add(self.k_input)
        v_sizer.Add(h_sizer, 0, wx.ALIGN_CENTRE | wx.TOP, 10)
        return panel

    @property
    def k(self):
        return self.k_input.GetValue()

    def train(self, data):
        self.training_data = []
        self.functions = [pypix.attribute_table[attr][0] for attr in data[0].strip().split(",")[2:]]
        # [1:] To ignore header row and UUID
        rows = [row.strip().split(",")[1:] for row in data[1:]]
        for row in rows:
            # Head of list is the classification, the tail are the properties
            self.training_data.append((row[0], tuple([float(i) for i in row[1:]])))
        self.k_input.SetRange(1,len(self.training_data))
        self.is_trained = True

    def classify(self, cluster):
        square_distances = []
        for training_datum in self.training_data:
            print training_datum
            square_distance = sum([(value - self.functions[i](cluster))**2 for i, value in enumerate(training_datum[1])])
            square_distances.append((training_datum[0], square_distance))
        square_distances.sort(key=lambda x: x[1])
        nearest_k = square_distances[0:self.k]
        nearest_k_types = [item[0] for item in nearest_k]
        cluster.algorithm_class = Counter(nearest_k_types).most_common(1)[0][0]

@algorithm("ID3")
class ID3(MLAlgorithm):

    def get_display_panel(self, parent):
        panel, v_sizer = super(ID3, self).get_display_panel(parent)
        return panel
