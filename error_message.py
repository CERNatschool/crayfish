import wx

def display_error_message(title, message):
    msg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_WARNING)
    msg.ShowModal()
    msg.Destroy()
