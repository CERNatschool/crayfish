"""
As display_error_message is called by many different files, it is defined in its
own separate file to make importing easier.
"""
import wx

def display_error_message(title, message):
    """
    Displays a modal error message dialog to the user.

    Args:
        title: The dialog title

        message: The dialog message
    """
    msg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_WARNING)
    msg.ShowModal()
    msg.Destroy()
