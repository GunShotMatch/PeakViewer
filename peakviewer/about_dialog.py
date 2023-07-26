#!/usr/bin/env python3
#
#  about_dialog.py
"""
About dialog for the Peak Viewer.
"""
#
#  Copyright © 2023 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import importlib.metadata
import sys

# 3rd party
import wx  # type: ignore[import]
from domdf_python_tools.stringlist import StringList

__all__ = ["AboutDialog"]


class AboutDialog(wx.MessageDialog):
	"""
	Dialog to display the version of Peak Viewer and its key dependencies.
	"""

	def __init__(self, parent: wx.Frame):

		# this package
		import peakviewer

		message = StringList()

		our_version = peakviewer.__version__
		message.append(f"Version: {our_version}")
		mpl_version = importlib.metadata.version("matplotlib")
		message.append(f"Matplotlib: {mpl_version}")
		wx_version = importlib.metadata.version("wxpython")
		message.append(f"wxPython: {wx_version}")
		# 3rd party
		from domdf_python_tools.words import LF
		message.append(f"Python: {sys.version.replace(LF, ' ')}")
		# stdlib
		import platform
		message.append(' '.join(platform.system_alias(platform.system(), platform.release(), platform.version())))

		name = "GunShotMatch Peak Viewer"
		super().__init__(parent, name, name, wx.OK | wx.HELP | wx.ICON_INFORMATION)
		self.ExtendedMessage = str(message)
		self.SetHelpLabel("Copy")

	def ShowModal(self) -> int:
		"""
		Override ShowModal to intercept 'Copy' button (masquerading as 'Help').

		When 'Copy' is pressed, copy the version information to the clipboard.
		"""

		ret = super().ShowModal()
		if ret == wx.ID_HELP:
			if wx.TheClipboard.Open():
				wx.TheClipboard.SetData(wx.TextDataObject(self.ExtendedMessage))
				wx.TheClipboard.Close()

		return ret
