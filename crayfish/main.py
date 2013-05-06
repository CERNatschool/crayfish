"""
The main Crayfish file, responsible for handling all of the GUI elements and
interfacing with alogithms.

The argument `parent` is related to the wx heirachy and is not related to
object inheritance.

Any method with argument `evt` is called by wx in responce to a UI event.
Likewise any method with argument `event` signifies an event that is called by
matplotlib.
"""
import os

import wx
import matplotlib
matplotlib.use("WXAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

import folder
import pypix
import algorithms
from error_message import display_error_message

# Classes dictionary, for mapping class type to graph plot style
CLASSES = {"Unclassified": ("k"), "Alpha": ("r"), "Beta": ("y"), "Gamma": ("b")}

class MainWindow(wx.Frame):
    """
    The root Crayfish window.

    Contains all of the UI elements as well as references to the currently
    selected frame and cluster.

    Args:
        title: The title of the main window
    """
    def __init__(self, title):
        super(MainWindow, self).__init__(None, title=title, size=(900, 600))
        self._init_menu_bar()
        self._init_window()

        self.aggregate = False
        self.frame = None
        self.cluster = None

        self.Show()

    def _init_menu_bar(self):
        """
        Initialises the menubar.
        """
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()

        menu_quit = file_menu.Append(wx.ID_EXIT)
        menu_open = file_menu.Append(wx.ID_OPEN)

        self.Bind(wx.EVT_MENU, self.on_quit, menu_quit)
        self.Bind(wx.EVT_MENU, self.on_open, menu_open)

        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

    def _init_window(self):
        """
        Arranges and initialises all of the UI widgets that form part of the
        window.
        """
        self.SetBackgroundColour("#5f6059")
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(h_sizer)

        # File Browser Column
        self.file_select_panel = FileSelectPanel(self)
        h_sizer.Add(self.file_select_panel, 0, wx.EXPAND | wx.ALL, 5)
        # Trace/Graph View Column
        display_notebook = wx.Notebook(self, style = wx.NB_NOPAGETHEME)
        self.display_trace = TraceRenderLarge(display_notebook)
        self.display_graph = GraphRender(display_notebook)
        display_notebook.AddPage(self.display_trace, "Trace")
        display_notebook.AddPage(self.display_graph, "Graph")
        h_sizer.Add(display_notebook, 1, wx.EXPAND)
        # Actions Column
        self.trace_zoom_display = TraceRenderZoom(self, size=(250,250))
        actions_notebook = wx.Notebook(self, size = (300, -1), style=wx.NB_NOPAGETHEME)
        self.view_tab = ViewPanel(actions_notebook)
        self.plot_tab = PlotPanel(actions_notebook)
        self.train_tab = TrainPanel(actions_notebook)
        self.classify_tab = ClassifyPanel(actions_notebook)
        actions_notebook.AddPage(self.view_tab, "View")
        actions_notebook.AddPage(self.plot_tab, "Plot")
        actions_notebook.AddPage(self.train_tab, "Train")
        actions_notebook.AddPage(self.classify_tab, "Classify")

        actions_sizer = wx.BoxSizer(wx.VERTICAL)
        actions_sizer.Add(self.trace_zoom_display, 0, wx.ALIGN_CENTRE | wx.ALL, 16)
        actions_sizer.Add(actions_notebook, 1, wx.EXPAND)
        h_sizer.Add(actions_sizer, 0, wx.EXPAND)


    def on_quit(self, evt):
        """
        Closes the window, and consequently the progam.
        """

        self.Close()

    def on_open(self, evt):
        """
        Open a top level folder.

        Displays a dialog allowing the user to select a top level directory.
        The directory is then opened in the frame browser column, displaying
        frames with the extension specified in the extensions text field.
        """
        dialog =  wx.DirDialog(self, message="Select folder to open")
        if dialog.ShowModal() == wx.ID_OK:
            self.file_select_panel.file_tree.set_top_node(folder.FolderNode(dialog.GetPath()))
            self.file_select_panel.file_tree.extension = self.file_select_panel.ext_field.GetValue()

    def on_aggregate(self, evt):
        """
        Aggregates all the frames in a folder.

        Aggregates all the frames in the selected folder on the frame browser.
        This calculates the clusters for each frame in the folder and its
        subfolders, and then loads it into the main window as if it were one
        frame, eg. for the large trace view and frame info table

        As this calculates the clusters in all frames below the folder in the
        file heirachy, many UI actions enforce the user to aggregate a frame
        first if they require details of clusters in subfolders. An example of
        this would be plotting a folder.
        """
        main_window.file_select_panel.aggregate_button.Disable()
        file_tree = self.file_select_panel.file_tree
        file_node = file_tree.GetPyData(self.file_tree.GetSelection())
        aggregate_frame = file_node.calculate_aggregate(self.file_select_panel.file_tree.extension)
        if aggregate_frame.number_of_hits == 0:
            display_error_message("Aggregation", 
                    "No hit pixels were found during the aggregation of the selected folder.")
        else:
            main_window.aggregate = True
            self.activate_frame(aggregate_frame)

    def activate_frame(self, frame):
        """
        Set frame to be the window's active frame.

        Renders the frame on the large trace view and tells the frame info table to
        update.
        """
        self.frame = frame
        self.display_trace.render(self.frame)
        self.view_tab.frame_table.set_attributes(self.frame)

    def activate_cluster(self, cluster):
        """
        Sets cluster to be the window's active cluster

        Renders the cluster on the trace zoom display and tells other UI
        elements to update.
        """

        self.cluster = cluster
        self.trace_zoom_display.render(self.cluster)
        self.view_tab.cluster_table.set_attributes(self.cluster)
        self.train_tab.manual_class_menu.SetValue(self.cluster.manual_class)
        self.train_tab.algorithm_class_display.SetValue(self.cluster.algorithm_class)


class FileSelectPanel(wx.Panel):
    """
    The file select panel contains UI elements relating to the frame browser and
    frame selection.
    """

    def __init__(self, parent, size=(200, -1)):
        super(FileSelectPanel, self).__init__(parent, size=size)

        self.file_tree = FileTreeCtrl(self)
        self.aggregate_button = wx.Button(self, label="Aggregate")
        ext_label = wx.StaticText(self, label="Ext:")
        self.ext_field = wx.ComboBox(self, value="*.lsc", choices=["*.lsc", "*.ascii"])
        open_button = wx.Button(self, wx.ID_OPEN, label="Open...")
        self.aggregate_button.Disable()

        self.Bind(wx.EVT_BUTTON, parent.on_open, open_button)
        self.Bind(wx.EVT_BUTTON, parent.on_aggregate, self.aggregate_button)

        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(v_sizer)
        v_sizer.Add(self.file_tree, 1, wx.EXPAND)
        v_sizer.Add(self.aggregate_button, 0, wx.ALIGN_RIGHT | wx.TOP, 5)
        v_sizer.AddSpacer(5)
        open_sizer = wx.BoxSizer(wx.HORIZONTAL)
        open_sizer.Add(ext_label, 0, wx.TOP, 5)
        open_sizer.Add(self.ext_field, 1)
        open_sizer.Add(open_button, 0, wx.TOP, 3)
        v_sizer.Add(open_sizer, 0, wx.ALIGN_RIGHT)


class FileTreeCtrl(wx.TreeCtrl):
    """
    Interfaces with `folder.py` to handle the open directory.

    Lazily adds children when a node is expanded.

    Each node in the FileTreeCtrl has its pydata attribute set to either a
    FolderNode or FrameNode instance that corresponds to a node in asimilar
    tree structure.
    """
    def __init__(self, parent):
        super(FileTreeCtrl, self).__init__(parent)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.on_expand_node, self)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select_node, self)

    def set_top_node(self, node):
        """Sets the top node of the frame browser."""
        self.DeleteAllItems()
        self.top_node = node
        root = self.AddRoot(node.name)
        self.SetItemHasChildren(root)
        self.SetPyData(root, self.top_node)

    def on_expand_node(self, evt):
        """
        Called by wx when a frame tree item is expanded.

        If the tree item has not yet been expanded the children are retrieved
        from the FolderNode instance that was expanded.
        """
        parent_tree_node = evt.GetItem()
        parent_file_node = self.GetPyData(parent_tree_node)
        if not parent_file_node.expanded:
            child_dirs, child_frames = parent_file_node.get_children(self.extension)
            for child_file_node in child_dirs:
                child_tree_node = self.AppendItem(parent_tree_node, child_file_node.name)
                self.SetItemHasChildren(child_tree_node)
                self.SetPyData(child_tree_node, child_file_node)
            for child_frame in child_frames:
                child_tree_node = self.AppendItem(parent_tree_node, child_frame.name)
                self.SetPyData(child_tree_node, child_frame)
            parent_file_node.expanded = True

    def on_select_node(self, evt):
        """
        Called when the a new item is selected in the frame browser.

        Either activates a new frame or enables aggregation depending if the
        new item is a frame or folder respectively.
        """
        item = evt.GetItem()
        data = self.GetPyData(item)
        if isinstance(data, folder.FrameNode):
            main_window.activate_frame(data.frame)
            main_window.file_select_panel.aggregate_button.Disable()
            main_window.aggregate = False
        if isinstance(data, folder.FolderNode):
            main_window.frame = None
            main_window.file_select_panel.aggregate_button.Enable()



class RenderPanel(wx.Panel):
    """
    The base class for both the trace and graph renderers.

    Handles the initialisation of the matplotlib figure.
    """

    def __init__(self, parent, size=wx.DefaultSize):
        super(RenderPanel, self).__init__(parent, size=size)
        self.fig = matplotlib.figure.Figure()
        self.canvas = FigureCanvas(self, -1, self.fig)
        centre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        centre_sizer.Add(self.canvas, 1, wx.ALIGN_CENTRE | wx.EXPAND)
        self.SetSizer(centre_sizer)
        min_dim = min(self.GetSize())
        self.canvas.SetSize((min_dim, min_dim))


class TraceRenderBase(RenderPanel):
    """
    Base class for trace renderers.
    """

    def _remove_axes_ticks(self):
        """
        Removes axes interval marks from the plot
        """
        self.axes.axes.set_xticks([])
        self.axes.axes.set_yticks([])

    def _cleanup_old_images(self):
        """
        Deletes old images to free up memory.

        By default matplotlib keeps a reference to previously plotted images.
        This function removes these references as we don't access them again.
        """
        # Delete older images, matplotlib requires two in the buffer
        if len(self.axes.images) > 2:
            self.axes.images =  self.axes.images[:-2]


class TraceRenderLarge(TraceRenderBase):
    """
    Responsible for the large trace view.
    """

    def __init__(self, parent, size=wx.DefaultSize):
        super(TraceRenderLarge, self).__init__(parent, size=size)
        self.axes = self.fig.add_axes([0,0,1,1])
        self._remove_axes_ticks()
        self.fig.canvas.mpl_connect("button_press_event", self.on_mouse)

    def render(self, pixelgrid):
        """
        Renders the trace view.

        pixelgrid is a 2d array of integers or floats of the form so that
        pixelgrid[y][x] corresponds to the value of (x, y). The values need not
        be normalised as this is done by the matplotlib `imshow()` function.
        """
        data = pixelgrid.render_energy()
        # Set origin to lower to match the display seen in Pixelman
        self.axes.imshow(data, origin="lower", interpolation="nearest", cmap="hot", aspect="auto")
        self.canvas.draw()
        self._cleanup_old_images()

    def on_mouse(self, event):
        """
        Called when the mouse is clicked on the rendered frame.

        The nearest hit pixel to the click position in calculated and its
        cluster activated as the current cluster.
        """
        # Parameter "event", not "evt", as this is a matplotlib event, not wx
        if main_window.frame and main_window.aggregate == False:
            frame_coords = self._mouse_to_frame_coords(event.x, event.y)
            cluster = main_window.frame.get_closest_cluster(frame_coords)
            main_window.activate_cluster(cluster)

    def _mouse_to_frame_coords(self, mouse_x, mouse_y):
        """
        Converts the click co-ordinates of the render to the corresponds
        co-ordinates of the frame.

        Returns a tuple of coords, ie. (frame_x_coord, frame_y_coord)
        """
        if main_window.frame:
            img_w, img_h = self.canvas.get_width_height()
            frame_x = int((mouse_x * main_window.frame.width)/img_w)
            frame_y = int((mouse_y * main_window.frame.height)/img_h)
            return frame_x, frame_y

class TraceRenderZoom(TraceRenderBase):
    """
    Responsible for the zoomed trace display.
    """

    def __init__(self, parent, size=wx.DefaultSize):
        super(TraceRenderZoom, self).__init__(parent, size=size)
        self.axes = self.fig.add_subplot(111)
        self._remove_axes_ticks()
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def render(self, pixelgrid):
        """
        Renders the trace view.

        pixelgrid is a 2d array of integers or floats of the form so that
        pixelgrid[y][x] corresponds to the value of (x, y). The values need not
        be normalised as this is done by the matplotlib `imshow()` function.

        pixelgrid should the size of one  whole frame but only contain the
        pixels that are wished to be zoomed (ie. the cluster). This method will
        then render the grid clipped to the bounding box of pixels.
        """
        data = pixelgrid.render_energy_zoomed()
        self.axes.imshow(data, origin="lower", interpolation="nearest", cmap="hot")
        self.canvas.draw()
        self._cleanup_old_images()

    def on_motion(self, event):
        """
        Called when the mouse is moved over the rendered display.

        Updates the pixel info line of the view tab with the corresponding
        position and energy.
        """
        # Parameter "event", not "evt", as this is a matplotlib event, not wx
        if main_window.cluster and event.xdata and event.ydata:
            x, y = [int(round(n)) for n in (event.xdata, event.ydata)]
            x += main_window.cluster.min_x
            y += main_window.cluster.min_y
            main_window.view_tab.pixel_info.SetLabel("Pixel (%03d %03d): %d" 
                    % (x, y, main_window.cluster[(x,y)].value))

class GraphRender(RenderPanel):
    """
    Responsible for the plotting and rendering of graphs.
    """

    def __init__(self, parent, size=wx.DefaultSize):
        super(GraphRender, self).__init__(parent, size=size)
        self.axes = None

    def render(self, x_axis, y_axis, class_property):
        """
        Plots and renders a graph.

        Args:
        x_axis: The attribute to be plotted on the x-axis.
        y_axis: The attribute to be plotted on the x-axis.
        class_property: The Python object property of each cluster that should
        be inspected in order to find out the class of each cluster. Used for
        switching between manually and algorithmically assigned cluster class.

        x_axis and y_axis should be a key of pypix.attribute_table so that
        the relevant function for calculating the attribute for each
        cluster can be retrieved.

        Additionally, y_axis mat have value "Histogram" in which case a
        histogram of the values of x_axis will be generated.

        """
        # Delete old plots from memory
        if self.axes:
            self.axes.clear()
        self.axes = self.fig.add_subplot(111)
        if y_axis == "Histogram":
            self.axes.set_xlabel(x_axis)
            self.axes.set_ylabel("Frequency")
            # Retrieve x function from pypix.attribute_table
            x_function = pypix.attribute_table[x_axis][0]
            # For each cluster class
            for class_ in CLASSES:
                # Loop over the clusters of the frame, calculating the value of
                # x_function for each cluster of the class we are currently inspecting
                x_values = [x_function(cluster) for cluster in main_window.frame.clusters
                        if getattr(cluster, class_property) == class_]
                # If we have calculated any values for the current class
                if x_values:
                    # Plot them on the histogram with the style defined in CLASSES
                    self.axes.hist(x_values, bins=100, histtype='stepfilled', color=CLASSES[class_][0])
        else:
            self.axes.set_xlabel(x_axis)
            self.axes.set_ylabel(y_axis)
            # Retrieve the relevant functions from pypix.attribute_table
            x_function = pypix.attribute_table[x_axis][0]
            y_function = pypix.attribute_table[y_axis][0]
            plot_clusters = main_window.frame.clusters[:] # Copy list, as we modify it
            # If we have a cluster selected, plot it now with a special style.
            if main_window.cluster:
                if main_window.cluster in plot_clusters:
                    plot_clusters.remove(main_window.cluster) #Don't plot twice
                    self.axes.plot(x_function(main_window.cluster),
                                    y_function(main_window.cluster), "cx")
                # Move plot line to this indentation to plot selected cluster
                # on all frames, even those it doesn't usually belong to.
            # For each cluster class calculate x/y values and plot them with
            # the style defined in CLASSES
            for class_ in CLASSES:
                x_values = [x_function(cluster) for cluster in plot_clusters if getattr(cluster, class_property) == class_]
                y_values = [y_function(cluster) for cluster in plot_clusters if getattr(cluster, class_property) == class_]
                self.axes.plot(x_values, y_values, CLASSES[class_][0] + ".")
        self.canvas.draw()


class ViewPanel(wx.ScrolledWindow):
    """
    Displays information about the current frame/cluster/pixel
    """
    def __init__(self, parent):
        super(ViewPanel, self).__init__(parent)
        self.SetScrollRate(1,1)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(v_sizer)

        self.pixel_info = wx.StaticText(self, label="Pixel (000,000): ")
        cluster_table_label = wx.StaticText(self, label="Cluster Info")
        self.cluster_table = AttributeTable(self, pypix.Cluster)
        frame_table_label = wx.StaticText(self, label="Frame Info")
        self.frame_table = AttributeTable(self, pypix.Frame)

        v_sizer.Add(self.pixel_info, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(cluster_table_label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(self.cluster_table, 1, wx.ALIGN_CENTRE | wx.BOTTOM, 5)
        v_sizer.Add(frame_table_label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(self.frame_table, 1, wx.ALIGN_CENTRE)


class PlotPanel(wx.ScrolledWindow):
    """
    Contains input elements relating to the plotting of graphs
    """

    def __init__(self, parent):
        super(PlotPanel, self).__init__(parent)
        self.SetScrollRate(1,1)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(v_sizer)

        #Load possible attributes for plotting, loading only those that have been defined as plottable
        dimensions = [dim for dim in pypix.attribute_table if pypix.attribute_table[dim][2]]

        x_label = wx.StaticText(self, label="Plot x ")
        self.x_axis_menu = wx.ComboBox(self, value=dimensions[0], choices=dimensions, style=wx.CB_READONLY)
        x_sizer = wx.BoxSizer(wx.HORIZONTAL)
        x_sizer.Add(x_label, 0, wx.TOP, 5)
        x_sizer.Add(self.x_axis_menu)

        y_label = wx.StaticText(self, label= ("Plot y "))
        self.y_axis_menu = wx.ComboBox(self, value=dimensions[1], choices=dimensions + ["Histogram"], style=wx.CB_READONLY)
        y_sizer = wx.BoxSizer(wx.HORIZONTAL)
        y_sizer.Add(y_label, 0, wx.TOP, 5)
        y_sizer.Add(self.y_axis_menu)

        source_label = wx.StaticText(self, label= ("Class Source "))
        self.source_menu = wx.ComboBox(self, value = "Manual", choices=["Manual", "Algorithm"], style=wx.CB_READONLY)
        source_sizer = wx.BoxSizer(wx.HORIZONTAL)
        source_sizer.Add(source_label, 0, wx.TOP, 5)
        source_sizer.Add(self.source_menu)

        plot_button = wx.Button(self, label = "Plot")
        self.Bind(wx.EVT_BUTTON, self.on_plot, plot_button)

        v_sizer.Add(x_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT, 20)
        v_sizer.Add(y_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT, 20)
        v_sizer.Add(source_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT, 20)
        v_sizer.Add(plot_button, 0, wx.ALIGN_CENTRE | wx.TOP, 10)


    def on_plot(self, evt):
        """
        Tells the GraphRender panel to render the graph with the required
        attribute axes.
        """
        if self.x_axis_menu.GetValue() == self.y_axis_menu.GetValue():
            display_error_message("Plot", "Cannot plot the same attribute against itself.")
            return
        if not main_window.frame:
            display_error_message("Plot", "No frame to plot. Please select a frame or aggregate a folder.")
            return
        source = self.source_menu.GetValue()
        if source == "Manual":
            class_property = "manual_class"
        elif source == "Algorithm":
            class_property = "algorithm_class"
        else:
            # Raise a ValueError, rather than calling display_error_message as this
            # code path shouldn't happen during normal execution of the code,
            # and represents an error on the part of the program, rather than
            # an error on the part of the user.
            raise ValueError("Unkown classification data source")
        main_window.display_graph.render(self.x_axis_menu.GetValue() , self.y_axis_menu.GetValue(), class_property)

class TrainPanel(wx.ScrolledWindow):
    """
    The UI panel contains inputs and displays information related to
    manual classification and the calculation of training data. In addition the
    class contains methods for the savind and loading of training data.
    """
    def __init__(self, parent):
        super(TrainPanel, self).__init__(parent)
        self.SetScrollRate(1,1)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(v_sizer)

        algorithm_class_label = wx.StaticText(self, label="Algorithm Class")
        self.algorithm_class_display = wx.TextCtrl(self, value="Unclassified", size=(120,-1))
        algorithm_class_sizer = wx.BoxSizer(wx.HORIZONTAL)
        algorithm_class_sizer.Add(algorithm_class_label, 0, wx.TOP, 5)
        algorithm_class_sizer.Add(self.algorithm_class_display)

        manual_class_label = wx.StaticText(self, label="Manual Class")
        self.manual_class_menu = wx.ComboBox(self, value="Unclassified",
                choices=["Unclassified", "Alpha", "Beta", "Gamma"], style = wx.CB_READONLY, size=(120,-1))
        self.Bind(wx.EVT_COMBOBOX, self.on_manual_set, self.manual_class_menu)
        manual_class_sizer = wx.BoxSizer(wx.HORIZONTAL)
        manual_class_sizer.Add(manual_class_label, 0, wx.TOP, 5)
        manual_class_sizer.Add(self.manual_class_menu)

        save_trn_data_button = wx.Button(self, label = "Save Training Data")
        load_trn_data_button = wx.Button(self, label = "Load Training Data")
        info_text = wx.StaticText(self,
                label="Load/save applies to current frame, or the currently selected folder and its subfolders.",
                    size=(0,-1))
        self.Bind(wx.EVT_BUTTON, self.on_training_save, save_trn_data_button)
        self.Bind(wx.EVT_BUTTON, self.on_training_load, load_trn_data_button)

        v_sizer.Add(algorithm_class_sizer, 0, wx.ALIGN_RIGHT)
        v_sizer.Add(manual_class_sizer, 0, wx.ALIGN_RIGHT)
        v_sizer.Add(save_trn_data_button, 0, wx.TOP | wx.ALIGN_CENTRE, 20)
        v_sizer.Add(load_trn_data_button, 0, wx.TOP | wx.ALIGN_CENTRE, 10)
        v_sizer.Add(info_text, 1, wx.TOP | wx.ALIGN_CENTRE | wx.EXPAND, 10)

    def on_manual_set(self, evt):
        """"
        Updates the manual cluster class.

        Called when the manual cluster class is changed view the dropdown menu"
        """
        main_window.cluster.manual_class = self.manual_class_menu.GetValue()

    def on_training_save(self, evt):
        """
        Saves the manually assigned cluster classification to a training file.
        """
        if not main_window.frame:
            display_error_message("Save Training File",
                    "Please select a frame or aggregate a subfolder to save training data from.")
            return
        dialog =  wx.FileDialog(self, message="Select save location", style=wx.FD_SAVE, defaultFile="training_data")
        if dialog.ShowModal() == wx.ID_OK:
            with open(dialog.GetPath(), "w") as f:
                # Generate the header by looping over attributes in attributes
                # table and adding they apply to clusters and are described as
                # trainable. Prepend the UUID and Classification headers as
                # these don't appear on the table.
                header = ["UUID", "Classification"] + [attr for attr in pypix.attribute_table
                    if issubclass(pypix.Cluster, pypix.attribute_table[attr][1]) and
                    pypix.attribute_table[attr][3]]
                f.write(",".join(header) + "\n")
                f.write(main_window.frame.get_training_rows())

    def on_training_load(self, evt):
        """
        Loads the training data and sets the manual class of all clusters that
        have a corresponding entry in the selected training_data file.
        """
        if not main_window.frame:
            display_error_message("Load Training File","Please select a frame or aggregate a subfolder to load training data into.")
            return
        dialog =  wx.FileDialog(self, message="Select open location")
        if dialog.ShowModal() == wx.ID_OK:
            with open(dialog.GetPath()) as f:
                UUID_keys = []
                classes = []
                next(f) # Skip header row
                for line in f:
                    data = line.strip().split(",")
                    UUID_keys.append(data[0])
                    classes.append(data[1])
                # Create a mapping from UUID to class and use this to load the
                # taining data.
                main_window.frame.load_training_data(dict(zip(UUID_keys, classes)))


class ClassifyPanel(wx.ScrolledWindow):
    """
    Contains input items for classifying clusters.
    """

    def __init__(self, parent):
        super(ClassifyPanel, self).__init__(parent)
        self.SetScrollRate(1,1)
        self.v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.v_sizer)

        algorithms_list = algorithms.algorithm_table.keys()
        self.algorithm_select = wx.ComboBox(self, value="None", choices=algorithms_list, style=wx.CB_READONLY)

        self.Bind(wx.EVT_COMBOBOX, self.on_algorithm_change, self.algorithm_select)

        self.v_sizer.Add(self.algorithm_select, 0, wx.TOP | wx.ALIGN_CENTER, 5)
        self.algorithm_panel = None

    def on_algorithm_change(self, evt):
        """
        Initialises a new algorithm
        Called when a new algorithm type is selected on the dropdown menu
        """
        self._set_algorithm(self.algorithm_select.GetValue())

    def _set_algorithm(self, algorithm):
        # Remove old algorithm settings panel
        if self.algorithm_panel:
            self.v_sizer.Remove(self.algorithm_panel)
            self.algorithm_panel.Destroy()
        self.algorithm = algorithms.algorithm_table[algorithm](main_window)
        # Algorithms have their own settings which are configured on a panel
        # they supply, so get this panel and add it to this classify panel
        # We must then recalculate the layout of _this_ panel.
        self.algorithm_panel = self.algorithm.get_display_panel(self)
        self.v_sizer.Add(self.algorithm_panel, 1, wx.EXPAND | wx.ALL, 5)
        self.v_sizer.Layout()



class AttributeTable(wx.ListCtrl):
    """
    Displays a table with information on objects, with info calculated from
    pypix.attribute_table
    """
    def __init__(self, parent, obj_type):
        """
        Initialise the table

        Populates the row headings from retrieved from pypix.attribute_table

        Args:
        obj_type: The object type (ie. a Class object) that the table will be
        calculating information about.
        """
        super(AttributeTable, self).__init__(parent, style=wx.LC_REPORT, size=(250,120))
        self.InsertColumn(0,"Attribute")
        self.InsertColumn(1,"Value")
        self.SetColumnWidth(0,130)
        self.SetColumnWidth(1,100)
        self.attribute_list = []
        # Loop over the attribute table
        for attr in pypix.attribute_table:
            # add them to a local instance variable attribute list if the
            # attribute applies to objects of the type `obj_type`
            # ie. if obj_type is a subclass (or the same class) as the class
            # for which the attribute was described
            if issubclass(obj_type, pypix.attribute_table[attr][1]):
                self.attribute_list += [(attr, pypix.attribute_table[attr])]
        # Setup row labels
        for i, attribute_row in enumerate(self.attribute_list):
            self.InsertStringItem(i, attribute_row[0])

    def set_attributes(self, obj):
        """
        Loads info on `obj` into the table
        """
        for i, attribute_row in enumerate(self.attribute_list):
            value = attribute_row[1][0](obj)
            if isinstance(value, float): # Format floats to 2 decimal places
                value = "%.2f" % value
            if isinstance(value, tuple): # Format each item of a tuple independently
                new_value = "("
                for component in value:
                    if isinstance(component,float):
                        new_value += "%.2f, " % i 
                    else:
                        new_value += str(i) + ", "
                value = new_value[:-2]  + ")"
            # Add the value to the table
            self.SetStringItem(i,1,str(value))


# Initialise wx
app = wx.App()

# Initialise the main app window
main_window = MainWindow(title="Crayfish")

# Begin the wx loop
app.MainLoop()
