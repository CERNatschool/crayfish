import os

import wx
import matplotlib
matplotlib.use("WXAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

import folder
import pypix

def display_error_message(title, message):
    msg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_WARNING)
    msg.ShowModal()
    msg.Destroy()


class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        # Initialise window using parent class
        super(MainWindow, self).__init__(parent, title=title, size=(900, 600))
        self._init_menu_bar()
        self._init_window()

        self.aggregate = False
        self.frame = None
        self.cluster = None

        self.Show()

    def _init_menu_bar(self):
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()

        menu_quit = file_menu.Append(wx.ID_EXIT)
        menu_open = file_menu.Append(wx.ID_OPEN)

        self.Bind(wx.EVT_MENU, self.on_quit, menu_quit)
        self.Bind(wx.EVT_MENU, self.on_open, menu_open)

        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

    def _init_window(self):
        self.SetBackgroundColour("#5f6059")
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(h_sizer)

        # File Browser Column
        self.file_select_panel = FileSelectPanel(self)
        h_sizer.Add(self.file_select_panel, 0, wx.EXPAND | wx.ALL, 5)
        # Trace/Graph View Column
        display_notebook = wx.Notebook(self, style = wx.NB_NOPAGETHEME)
        self.display_trace = TraceRender(display_notebook)
        self.display_graph = GraphRender(display_notebook)
        display_notebook.AddPage(self.display_trace, "Trace")
        display_notebook.AddPage(self.display_graph, "Graph")
        h_sizer.Add(display_notebook, 1, wx.EXPAND)
        # Actions Column
        self.trace_zoom_display = TraceRender(self, size=(250,250), zoom=True)
        actions_notebook = wx.Notebook(self, size = (300, -1), style=wx.NB_NOPAGETHEME)
        self.view_tab = ViewPanel(actions_notebook)
        self.plot_tab = PlotPanel(actions_notebook)
        self.train_tab = TrainPanel(actions_notebook)
        self.classify_tab = wx.Panel(actions_notebook)
        actions_notebook.AddPage(self.view_tab, "View")
        actions_notebook.AddPage(self.plot_tab, "Plot")
        actions_notebook.AddPage(self.train_tab, "Train")
        actions_notebook.AddPage(self.classify_tab, "Classify")

        actions_sizer = wx.BoxSizer(wx.VERTICAL)
        actions_sizer.Add(self.trace_zoom_display, 0, wx.ALIGN_CENTRE | wx.ALL, 16)
        actions_sizer.Add(actions_notebook, 1, wx.EXPAND)
        h_sizer.Add(actions_sizer, 0, wx.EXPAND)


    def on_quit(self, evt):
        self.Close()

    def on_open(self, evt):
        dialog =  wx.DirDialog(self, message="Select folder to open")
        if dialog.ShowModal() == wx.ID_OK:
            self.file_select_panel.file_tree.set_top_node(folder.FolderNode(dialog.GetPath()))
            self.file_select_panel.file_tree.extension = self.file_select_panel.ext_field.GetValue()

    def on_aggregate(self, evt):
        main_window.file_select_panel.aggregate_button.Disable()
        file_node = self.file_select_panel.file_tree.GetPyData(self.file_select_panel.file_tree.GetSelection())
        aggregate_frame = file_node.calculate_aggregate(self.file_select_panel.file_tree.extension)
        if aggregate_frame.number_of_hits == 0:
            display_error_message("Aggregation", "No hit pixels were found during the aggregation of the selected folder.")
        else:
            main_window.aggregate = True
            self.activate_frame(aggregate_frame)

    def activate_frame(self, frame):
        self.frame = frame
        self.display_trace.render(self.frame)
        self.view_tab.frame_table.set_attributes(self.frame)

    def activate_cluster(self, cluster):
        self.cluster = cluster
        self.trace_zoom_display.render(self.cluster)
        self.view_tab.cluster_table.set_attributes(self.cluster)
        self.train_tab.manual_class_menu.SetValue(self.cluster.manual_class)


class FileSelectPanel(wx.Panel):

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

    def __init__(self, parent):
        super(FileTreeCtrl, self).__init__(parent)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.on_expand_node, self)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select_node, self)

    def set_top_node(self, node):
        self.DeleteAllItems()
        self.top_node = node
        root = self.AddRoot(node.name)
        self.SetItemHasChildren(root)
        self.SetPyData(root, self.top_node)

    def on_expand_node(self, evt):
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

    def __init__(self, parent, size = wx.DefaultSize, zoom=False):
        super(RenderPanel, self).__init__(parent, size=size)
        self.fig = matplotlib.figure.Figure()
        self.canvas = FigureCanvas(self, -1, self.fig)
        centre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        centre_sizer.Add(self.canvas, 1, wx.ALIGN_CENTRE | wx.EXPAND)
        self.SetSizer(centre_sizer)
        min_dim = min(self.GetSize())
        self.canvas.SetSize((min_dim, min_dim))


class TraceRender(RenderPanel):

    def __init__(self, parent, size=None, zoom=False):
        super(TraceRender, self).__init__(parent, size)
        self.zoom = zoom
        if self.zoom:
            self.axes = self.fig.add_subplot(111)
        else:
            self.axes = self.fig.add_axes([0,0,1,1])
            self.fig.canvas.mpl_connect("button_press_event", self.on_mouse)
        self.axes.axes.set_xticks([])
        self.axes.axes.set_yticks([])
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def render(self, pixelgrid):
        if self.zoom:
            data = pixelgrid.render_energy_zoomed()
            aspect = None
        else:
            data = pixelgrid.render_energy()
            aspect = "auto"
        self.axes.imshow(data, origin="lower", interpolation="nearest", cmap="hot", aspect=aspect)
        self.canvas.draw()
        # Delete older images, matplotlib requires two in the buffer
        if len(self.axes.images) > 2:
            self.axes.images =  self.axes.images[:-2]

    def on_motion(self, event):
        # Parameter "event", not "evt", as this is a matplotlib event, not wx
        if main_window.frame:
            self._mouse_to_frame_coords(event.x, event.y)

    def on_mouse(self, event):
        # Parameter "event", not "evt", as this is a matplotlib event, not wx
        if main_window.frame and main_window.aggregate == False:
            frame_coords = self._mouse_to_frame_coords(event.x, event.y)
            cluster = main_window.frame.get_closest_cluster(frame_coords)
            main_window.activate_cluster(cluster)

    def _mouse_to_frame_coords(self, mouse_x, mouse_y):
        img_w, img_h = self.canvas.get_width_height()
        frame_x = int((mouse_x * 255)/img_w)
        frame_y = int((mouse_y * 255)/img_h)
        return frame_x, frame_y


class GraphRender(RenderPanel):

    def __init__(self, parent, size=None):
        super(GraphRender, self).__init__(parent, size=size)
        self.axes = None

    def render(self, x_axis, y_axis):
        # Delete old plots from memory
        if self.axes:
            self.axes.clear()
        self.axes = self.fig.add_subplot(111)
        if y_axis == "Histogram":
            self.axes.set_xlabel(x_axis)
            self.axes.set_ylabel("Frequency")
            x_function = pypix.attribute_table[x_axis][0]
            x_values = [x_function(cluster) for cluster in main_window.frame.clusters]
            self.axes.hist(x_values, 10, histtype='stepfilled')
        else:
            self.axes.set_xlabel(x_axis)
            self.axes.set_ylabel(y_axis)
            x_function = pypix.attribute_table[x_axis][0]
            y_function = pypix.attribute_table[y_axis][0]
            plot_clusters = main_window.frame.clusters[:] # Copy list, as we modify it
            if main_window.cluster:
                if not main_window.aggregate:
                    #TODO: Can't remove from list as clusters are different obects
                    # due to way aggregate funcion works (makes new clusters/frames)
                    plot_clusters.remove(main_window.cluster)
                self.axes.plot(x_function(main_window.cluster), y_function(main_window.cluster), "cx")
            x_values = [x_function(cluster) for cluster in plot_clusters]
            y_values = [y_function(cluster) for cluster in plot_clusters]
            self.axes.plot(x_values, y_values, "k.")
        self.canvas.draw()


class ViewPanel(wx.ScrolledWindow):

    def __init__(self, parent):
        super(ViewPanel, self).__init__(parent)
        self.SetScrollRate(1,1)
        v_sizer = wx.BoxSizer(wx.VERTICAL)

        cluster_table_label = wx.StaticText(self, label="Cluster Info")
        self.cluster_table = AttributeTable(self, pypix.Cluster)
        frame_table_label = wx.StaticText(self, label="Frame Info")
        self.frame_table = AttributeTable(self, pypix.Frame)

        v_sizer.Add(cluster_table_label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(self.cluster_table, 1, wx.ALIGN_CENTRE | wx.BOTTOM, 5)
        v_sizer.Add(frame_table_label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(self.frame_table, 1, wx.ALIGN_CENTRE)

        self.SetSizer(v_sizer)

class PlotPanel(wx.Panel):

    def __init__(self, parent):
        super(PlotPanel, self).__init__(parent)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(v_sizer)

        dimensions = [dim for dim in pypix.attribute_table if dim[2]]

        x_label = wx.StaticText(self, label="Plot x:")
        self.x_axis_menu = wx.ComboBox(self, value = dimensions[0], choices=dimensions, style=wx.CB_READONLY)
        x_sizer = wx.BoxSizer(wx.HORIZONTAL)
        x_sizer.Add(x_label, 0, wx.TOP, 5)
        x_sizer.Add(self.x_axis_menu)
        v_sizer.Add(x_sizer, 0, wx.ALIGN_CENTRE)

        y_label = wx.StaticText(self, label= ("Plot y:"))
        self.y_axis_menu = wx.ComboBox(self, value = dimensions[1], choices=dimensions + ["Histogram"], style=wx.CB_READONLY)
        y_sizer = wx.BoxSizer(wx.HORIZONTAL)
        y_sizer.Add(y_label, 0, wx.TOP, 5)
        y_sizer.Add(self.y_axis_menu)
        v_sizer.Add(y_sizer, 0, wx.ALIGN_CENTRE)

        plot_button = wx.Button(self, label = "Plot")

        self.Bind(wx.EVT_BUTTON, self.on_plot, plot_button)

        v_sizer.Add(plot_button, 0, wx.ALIGN_CENTRE)


    def on_plot(self, evt):
        if self.x_axis_menu.GetValue() == self.y_axis_menu.GetValue():
            display_error_message("Plot", "Cannot plot the same attribute against itself.")
            return
        if not main_window.frame:
            display_error_message("Plot", "No frame to plot. Please select a frame or aggregate a folder.")
            return
        main_window.display_graph.render(self.x_axis_menu.GetValue() , self.y_axis_menu.GetValue())

class TrainPanel(wx.Panel):

    def __init__(self, parent):
        super(TrainPanel, self).__init__(parent)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(v_sizer)

        algorithm_class_label = wx.StaticText(self, label="Algorithm Class")
        self.algorithm_class_display = wx.TextCtrl(self, value="Unclassified", size=(120,-1))
        algorithm_class_sizer = wx.BoxSizer(wx.HORIZONTAL)
        algorithm_class_sizer.Add(algorithm_class_label, 0, wx.TOP, 5)
        algorithm_class_sizer.Add(self.algorithm_class_display)
        v_sizer.Add(algorithm_class_sizer, 0, wx.ALIGN_RIGHT)

        manual_class_label = wx.StaticText(self, label="Manual Class")
        self.manual_class_menu = wx.ComboBox(self, value="Unclassified", choices=["Unclassified", "Alpha", "Beta", "Gamma"], style = wx.CB_READONLY, size=(120,-1))
        self.Bind(wx.EVT_COMBOBOX, self.on_manual_set, self.manual_class_menu)
        manual_class_sizer = wx.BoxSizer(wx.HORIZONTAL)
        manual_class_sizer.Add(manual_class_label, 0, wx.TOP, 5)
        manual_class_sizer.Add(self.manual_class_menu)
        v_sizer.Add(manual_class_sizer, 0, wx.ALIGN_RIGHT)

        save_trn_data_button = wx.Button(self, label = "Save Training Data")
        load_trn_data_button = wx.Button(self, label = "Load Training Data")
        info_text = wx.StaticText(self, label="Load/save applies to current frame, or the currently select folder and its subfolders.")
        self.Bind(wx.EVT_BUTTON, self.on_training_save, save_trn_data_button)
        self.Bind(wx.EVT_BUTTON, self.on_training_load, load_trn_data_button)

        v_sizer.Add(save_trn_data_button, 0, wx.TOP | wx.ALIGN_CENTRE, 20)
        v_sizer.Add(load_trn_data_button, 0, wx.TOP | wx.ALIGN_CENTRE, 10)
        v_sizer.Add(info_text, 1, wx.TOP | wx.ALIGN_CENTRE | wx.EXPAND, 10)

    def on_manual_set(self, evt):
        main_window.cluster.manual_class = self.manual_class_menu.GetValue()

    def on_training_save(self, evt):
        pass

    def on_training_load(self, evt):
        pass


class AttributeTable(wx.ListCtrl):

    def __init__(self, parent, obj_type):
        super(AttributeTable, self).__init__(parent, style=wx.LC_REPORT, size=(250,120))
        self.InsertColumn(0,"Attribute")
        self.InsertColumn(1,"Value")
        self.SetColumnWidth(0,130)
        self.SetColumnWidth(1,100)
        self.attribute_list = []
        for attr in pypix.attribute_table:
            if issubclass(obj_type, pypix.attribute_table[attr][1]):
                self.attribute_list += [(attr, pypix.attribute_table[attr])]
        # Setup row labels
        for i, attribute_row in enumerate(self.attribute_list):
            self.InsertStringItem(i, attribute_row[0])

    def set_attributes(self, obj):
        if hasattr(obj, "clusters"):
            print obj.clusters
        for i, attribute_row in enumerate(self.attribute_list):
            value = attribute_row[1][0](obj)
            if isinstance(value, float):
                value = "%.2f" % value
            if isinstance(value, tuple):
                new_value = "("
                for component in value:
                    if isinstance(component,float):
                        new_value += "%.2f, " % i
                    else:
                        new_value += str(i) + ", "
                value = new_value[:-2]  + ")"
            self.SetStringItem(i,1,str(value))


app = wx.App()

main_window = MainWindow(None, title="Crayfish")

app.MainLoop()
