import os

import wx
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas



import folder
import pypix

TESTING = False

def ErrorMessage(title, message):
    msg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_WARNING)
    msg.ShowModal()
    msg.Destroy()


class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        # Initialise window using parent class
        wx.Frame.__init__(self, parent, title=title, size = (900, 600))

        self.init_menu_bar()
        self.init_window()
        self.Show()

    def init_menu_bar(self):
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()

        menu_quit = file_menu.Append(wx.ID_EXIT)
        menu_open = file_menu.Append(wx.ID_OPEN)

        self.Bind(wx.EVT_MENU, self.on_quit, menu_quit)
        self.Bind(wx.EVT_MENU, self.on_open, menu_open)

        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

    def init_window(self):
        window_panel = wx.Panel(self)
        window_panel.SetBackgroundColour("#5f6059")

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # File Browser Column
        ext_label = wx.StaticText(window_panel, label="Ext:")
        self.ext_field = wx.ComboBox(window_panel, size = (70, -1), value="*.lsc",choices=["*.lsc", "*.ascii"])
        self.file_tree = FileTreeCtrl(window_panel, size=(200, -1))
        open_button = wx.Button(window_panel, wx.ID_OPEN, label="Open...")
        self.aggregate_button = wx.Button(window_panel, label="Aggregate")
        self.aggregate_button.Disable()
        self.aggregate = False

        self.Bind(wx.EVT_BUTTON, self.on_open, open_button)
        self.Bind(wx.EVT_BUTTON, self.on_aggregate, self.aggregate_button)

        file_sizer = wx.BoxSizer(wx.VERTICAL)
        file_sizer.Add(self.file_tree, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT)
        file_sizer.Add(self.aggregate_button, 0, wx.ALIGN_RIGHT | wx.TOP, 5)
        file_sizer.AddSpacer(5)
        ext_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ext_input_sizer.Add(ext_label, 0, wx.TOP, 5)
        ext_input_sizer.Add(self.ext_field, 0,)
        ext_input_sizer.Add(open_button, 0, wx.TOP, 3)
        file_sizer.Add(ext_input_sizer, 0, wx.ALIGN_RIGHT)
        h_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 5)
        # Trace/Graph View Column
        display_notebook = wx.Notebook(window_panel, style = wx.NB_NOPAGETHEME)
        self.display_trace = TraceRender(display_notebook)
        display_notebook.AddPage(self.display_trace, "Trace")
        self.display_graph = GraphPanel(display_notebook)
        display_notebook.AddPage(self.display_graph, "Graph")

        centre_sizer = wx.BoxSizer(wx.VERTICAL)
        centre_sizer.Add(display_notebook, 1, wx.EXPAND)
        h_sizer.Add(centre_sizer, 1, wx.EXPAND)

        # Settings Column
        self.trace_zoom_display = TraceRender(window_panel, size=(250,250), zoom=True)
        settings_notebook = wx.Notebook(window_panel, size = (300, -1), style=wx.NB_NOPAGETHEME)
        self.settings_view = ViewPanel(settings_notebook)
        settings_notebook.AddPage(self.settings_view, "View")
        settings_plot = PlotPanel(settings_notebook)
        settings_notebook.AddPage(settings_plot, "Plot")
        settings_classify = wx.Panel(settings_notebook)
        settings_notebook.AddPage(settings_classify, "Classify")

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(self.trace_zoom_display, 0, wx.ALIGN_CENTRE | wx.ALL, 16)
        settings_sizer.Add(settings_notebook, 1, wx.EXPAND)
        h_sizer.Add(settings_sizer, 0, wx.EXPAND)

        window_panel.SetSizer(h_sizer)

        self.frame = None
        self.cluster = None

        if TESTING:
            self.file_tree.set_top_node(folder.FileNode("/Users/Richard/Projects/Star Centre/"))
            self.file_tree.extension = self.ext_field.GetValue()


    def on_quit(self, evt):
        self.Close()

    def on_open(self, evt):
        dialog =  wx.DirDialog(self, message="Select containing folder")
        if dialog.ShowModal() == wx.ID_OK:
            self.file_tree.set_top_node(folder.FileNode(dialog.GetPath()))
            self.file_tree.extension = self.ext_field.GetValue()

    def on_aggregate(self, evt):
        main_window.aggregate_button.Disable()
        file_node = self.file_tree.GetPyData(self.file_tree.GetSelection())
        aggregate_frame = file_node.calculate_aggregate(self.file_tree.extension)
        if aggregate_frame.num_hits == 0:
            ErrorMessage("Aggregation", "No hit pixels were found during the aggregation of the selected folder.")
        else:
            main_window.aggregate = True
            self.activate_frame(aggregate_frame)

    def activate_frame(self, frame):
        self.frame = frame
        self.display_trace.render(self.frame)
        self.settings_view.frame_table.set_attributes(self.frame, pypix.attribute_table)
        if not main_window.aggregate: self.frame.calculate_clusters()

    def activate_cluster(self, cluster):
        self.cluster = cluster
        self.trace_zoom_display.render(self.cluster, zoom=True)
        self.settings_view.cluster_table.set_attributes(self.cluster, pypix.attribute_table)


class FileTreeCtrl(wx.TreeCtrl):

    def __init__(self, parent, size):
        wx.TreeCtrl.__init__(self, parent, size=size)
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
        if data.node_type == folder.FRAME:
            frame = pypix.Frame.from_file(data.path)
            main_window.activate_frame(frame)
            main_window.aggregate_button.Disable()
            main_window.aggregate = False
        elif data.node_type == folder.DIR:
            main_window.frame = None
            main_window.aggregate_button.Enable()



class GraphPanel(wx.Panel):

    def __init__(self, parent, size = wx.DefaultSize, zoom = False):
        wx.Panel.__init__(self, parent, size = size)
        self.fig = matplotlib.figure.Figure()
        self.canvas = FigureCanvas(self, -1, self.fig)

        centre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        centre_sizer.Add(self.canvas, 1, wx.ALIGN_CENTRE | wx.EXPAND)
        self.SetSizer(centre_sizer)
        self.axes = None

    def render(self, x_axis, y_axis):
        if self.axes:
            self.axes.clear()
        self.axes = self.fig.add_subplot(111)
        if y_axis == "Histogram":
            self.axes.set_xlabel(x_axis)
            self.axes.set_ylabel("Frequency")
            x_function = pypix.plottable_table[x_axis]
            x_values = [x_function(cluster) for cluster in main_window.frame.clusters]
            self.axes.hist(x_values, 10, histtype='stepfilled')
        else:
            self.axes.set_xlabel(x_axis)
            self.axes.set_ylabel(y_axis)
            x_function = pypix.plottable_table[x_axis]
            y_function = pypix.plottable_table[y_axis]
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

class RenderPanel(wx.Panel):

    def __init__(self, parent, size = wx.DefaultSize, zoom = False):
        wx.Panel.__init__(self, parent, size = size)
        self.fig = matplotlib.figure.Figure()
        self.canvas = FigureCanvas(self, -1, self.fig)
        if zoom:
            self.axes = self.fig.add_subplot(111)
            for tick in self.axes.xaxis.get_major_ticks():
                tick.label1On = False
            for tick in self.axes.yaxis.get_major_ticks():
                tick.label1On = False
        else:
            self.axes = self.fig.add_axes([0,0,1,1])
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.fig.canvas.mpl_connect("button_press_event", self.on_mouse)
        # self.Bind(wx.EVT_SIZE, self.on_size)

        centre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        centre_sizer.Add(self.canvas, 1, wx.ALIGN_CENTRE | wx.EXPAND)
        self.SetSizer(centre_sizer)

    def on_size(self, evt):
        min_dim = min(self.GetSize())
        self.canvas.SetSize((min_dim, min_dim))

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


class TraceRender(RenderPanel):

    def render(self, pixelgrid, zoom = False):
        if zoom:
            data = pixelgrid.render_energy_zoomed()
            aspect = None
        else:
            data = pixelgrid.render_energy()
            aspect = "auto"
        self.axes.imshow(data, origin="lower", interpolation="nearest", cmap="hot", aspect=aspect)
        self.canvas.draw()
        # Delete older images, unfortunately may cause older image to display on resize
        if len(self.axes.images) > 1:
            self.axes.images =  self.axes.images[:-1]


class ViewPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        v_sizer = wx.BoxSizer(wx.VERTICAL)

        cluster_table_label = wx.StaticText(self, label="Cluster Info")
        self.cluster_table = AttributeTable(self)
        frame_table_label = wx.StaticText(self, label="Frame Info")
        self.frame_table = AttributeTable(self)

        v_sizer.Add(cluster_table_label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(self.cluster_table, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 5)
        v_sizer.Add(frame_table_label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        v_sizer.Add(self.frame_table, 0, wx.ALIGN_CENTRE)

        self.SetSizer(v_sizer)

class PlotPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        v_sizer = wx.BoxSizer(wx.VERTICAL)

        dimensions = [dim for dim in pypix.plottable_table]

        x_label = wx.StaticText(self, label= ("Plot x:"))
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

        self.SetSizer(v_sizer)

    def on_plot(self, evt):
        if self.x_axis_menu.GetValue() == self.y_axis_menu.GetValue():
            ErrorMessage("Plot", "Cannot plot the same attribute against itself.")
            return
        if not main_window.frame:
            ErrorMessage("Plot", "No frame to plot. Please select a frame or aggregate a folder.")
            return
        main_window.display_graph.render(self.x_axis_menu.GetValue() , self.y_axis_menu.GetValue())


class AttributeTable(wx.ListCtrl):
    
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT, size=(250,150))
        self.InsertColumn(0,"Attribute")
        self.InsertColumn(1,"Value")
        self.SetColumnWidth(0,100)
        self.SetColumnWidth(1,130)

    def set_attributes(self, obj, attributes):
        self.DeleteAllItems()
        # Don't use enumerate as not every for loop will result in a table row
        index = 0
        for attribute in attributes:
            if isinstance(obj, attributes[attribute][0]):
                self.InsertStringItem(index,attribute)
                value = attributes[attribute][1](obj)
                if isinstance(value, float):
                    value = "%.2f" % value
                if isinstance(value, tuple):
                    new_value = "("
                    for i in value:
                        if isinstance(i,float):
                            new_value += "%.2f, " % i
                        else:
                            new_value += str(i) + ", "
                    value = new_value[:-2]  + ")"
                self.SetStringItem(index,1,str(value))
                index += 1


app = wx.App()

main_window = MainWindow(None, "Crayfish")

app.MainLoop()
