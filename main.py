import wx

class MainWindow(wx.Frame):
    
    def __init__(self, parent, title):
        # Initialise window using parent class
        wx.Frame.__init__(self, parent, title=title)
        
        self.init_menu_bar()
        self.init_window()
        self.Show()


    def init_menu_bar(self):
        menu_bar = wx.MenuBar()
        
        file_menu = wx.Menu()
        
        menu_quit = file_menu.Append(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.menu_quit, menu_quit)
        
        menu_open = file_menu.Append(wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.menu_open, menu_open)
        
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

    def init_window(self):
        window_panel = wx.Panel(self)

    def menu_quit(self, event):
        self.quit()

    def menu_open(self, event):
        dialog =  wx.DirDialog(self, message = "Select containing folder")
        if dialog.ShowModal() == wx.ID_OK:
            self.top_folder = dialog.GetPath()

    def quit(self):
        self.Close()



app = wx.App()

main_window = MainWindow(None, "Crayfish")

app.MainLoop()
