import os

import wx
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas



import folder
import pypix

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
        self.Bind(wx.EVT_MENU, self.on_quit, menu_quit)
        menu_open = file_menu.Append(wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_open, menu_open)

        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

    def init_window(self):
        window_panel = wx.Panel(self)
        window_panel.SetBackgroundColour("#5f6059")
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        file_sizer = wx.BoxSizer(wx.VERTICAL)

        self.file_tree = FileTreeCtrl(window_panel, size=(200, -1))
        file_sizer.Add(self.file_tree, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT)

        ext_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ext_label = wx.StaticText(window_panel, label="Extension:")
        self.ext_field = wx.ComboBox(window_panel, value="*.lsc",choices=["*.lsc", "*.ascii"])
        ext_input_sizer.Add(ext_label, 0, wx.TOP, 5)
        ext_input_sizer.Add(self.ext_field, 0,)
        file_sizer.Add(ext_input_sizer, 0, wx.ALIGN_RIGHT)

        open_button = wx.Button(window_panel, wx.ID_OPEN, label="Open Folder")
        self.Bind(wx.EVT_BUTTON, self.on_open, open_button)
        file_sizer.Add(open_button, 0, wx.ALIGN_RIGHT)
        h_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 5)

        centre_sizer = wx.BoxSizer(wx.VERTICAL)
        display_notebook = wx.Notebook(window_panel, style = wx.NB_NOPAGETHEME)
        display_trace = TraceRender(display_notebook)
        self.file_tree.renderer = display_trace
        display_notebook.AddPage(display_trace, "Trace")
        display_graph = wx.Panel(display_notebook)
        display_notebook.AddPage(display_graph, "Graph")
        centre_sizer.Add(display_notebook, 1, wx.EXPAND)
        h_sizer.Add(centre_sizer, 1, wx.EXPAND)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_notebook = wx.Notebook(window_panel, size = (300, -1), style=wx.NB_NOPAGETHEME)
        settings_view = wx.Panel(settings_notebook)
        settings_notebook.AddPage(settings_view, "View")
        settings_plot = wx.Panel(settings_notebook)
        settings_notebook.AddPage(settings_plot, "Plot")
        settings_classify = wx.Panel(settings_notebook)
        settings_notebook.AddPage(settings_classify, "Classify")
        settings_sizer.Add(settings_notebook, 1, wx.EXPAND)
        h_sizer.Add(settings_sizer, 0, wx.EXPAND)

        window_panel.SetSizer(h_sizer)


    def on_quit(self, evt):
        self.Close()

    def on_open(self, evt):
        dialog =  wx.DirDialog(self, message="Select containing folder")
        if dialog.ShowModal() == wx.ID_OK:
            self.file_tree.set_top_node(folder.FileNode(dialog.GetPath()))
            self.file_tree.extension = self.ext_field.GetValue()

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
        parent_file_node =  self.GetPyData(parent_tree_node)
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
        if self.GetPyData(item).node_type == folder.FRAME:
            frame = pypix.Frame.from_file(self.GetPyData(item).path)
            self.renderer.render(frame.render_energy())

class RenderPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.fig = matplotlib.figure.Figure()
        self.canvas = FigureCanvas(self, -1, self.fig)
        self.axes = self.fig.add_axes([0,0,1,1])
        #self.Bind(wx.EVT_SIZE, self.on_size)

        centre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        centre_sizer.Add(self.canvas, 1, wx.ALIGN_CENTRE | wx.EXPAND)
        self.SetSizer(centre_sizer)

    def on_size(self, evt):
        min_dim = min(self.GetSize())
        self.canvas.SetSize((min_dim, min_dim))

class TraceRender(RenderPanel):

    def render(self, data):
        self.axes.imshow(data, origin="lower", interpolation="nearest", cmap="hot", aspect="auto")
        self.canvas.draw()
        if len(self.axes.images) > 1:
            self.axes.images =  self.axes.images[:-1]

app = wx.App()

main_window = MainWindow(None, "Crayfish")

app.MainLoop()
