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

# 3rd party
import wx  # type: ignore[import-not-found]

# this package
from peakviewer.versions import get_formatted_versions

__all__ = ("AboutDialog", )


class AboutDialog(wx.MessageDialog):
	"""
	Dialog to display the version of Peak Viewer and its key dependencies.
	"""

	def __init__(self, parent: wx.Frame):

		message = get_formatted_versions()

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
