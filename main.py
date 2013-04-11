import wx

import folder

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

        self.file_tree = wx.TreeCtrl(window_panel, size=(200, -1))
        file_sizer.Add(self.file_tree, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT)

        ext_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ext_label = wx.StaticText(window_panel, label="Extension:")
        self.ext_field = wx.ComboBox(window_panel, value=".lsc",choices=[".lcs", ".ascii"])
        ext_input_sizer.Add(ext_label, 0, wx.TOP, 5)
        ext_input_sizer.Add(self.ext_field, 0,)
        file_sizer.Add(ext_input_sizer, 0, wx.ALIGN_RIGHT)

        open_button = wx.Button(window_panel, wx.ID_OPEN, label="Open Folder")
        self.Bind(wx.EVT_BUTTON, self.on_open, open_button)
        file_sizer.Add(open_button, 0, wx.ALIGN_RIGHT)
        h_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 5)

        centre_sizer = wx.BoxSizer(wx.VERTICAL)
        display_notebook = wx.Notebook(window_panel, style = wx.NB_NOPAGETHEME)
        display_trace = wx.Panel(display_notebook)
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
        


    def on_quit(self, event):
        self.quit()

    def on_open(self, event):
        self.open_folder()

    def open_folder(self):
        dialog =  wx.DirDialog(self, message="Select containing folder")
        if dialog.ShowModal() == wx.ID_OK:
            self.top_folder = folder.Folder(dialog.GetPath())
            self.reload_file_tree()

    def reload_file_tree(self):
        self.top_folder.build_subtree()
        self.file_tree.DeleteAllItems()
        root = self.file_tree.AddRoot(self.top_folder.name)
        self.top_folder.add_children(self.file_tree, root)

    def quit(self):
        self.Close()



app = wx.App()

main_window = MainWindow(None, "Crayfish")

app.MainLoop()
