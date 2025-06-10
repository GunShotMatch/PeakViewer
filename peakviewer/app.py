#!/usr/bin/env python3
#
#  app.py
"""
wxPython app for the Peak Viewer.
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
from typing import Optional

# 3rd party
import wx  # type: ignore[import-not-found]

# this package
from peakviewer.peak_viewer_frame import PeakViewerFrame

__all__ = ["PeakViewerApp"]


class PeakViewerApp(wx.App):
	"""
	GunShotMatch Peak Viewer application.
	"""

	def __init__(self, filename: Optional[str], *args, **kwargs):
		self.filename = filename
		super().__init__(*args, **kwargs)

	def OnInit(self) -> bool:  # noqa: D102

		frame = PeakViewerFrame("Peak Viewer")
		self.SetTopWindow(frame)
		frame.Show(True)

		if self.filename:
			# Defer slightly to allow window to fully load
			wx.CallLater(100, frame.load_project, self.filename)

		return True
