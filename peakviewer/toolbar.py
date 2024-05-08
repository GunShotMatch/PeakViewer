#!/usr/bin/env python3
#
#  toolbar.py
"""
Main toolbar for the Peak Viewer.
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
from typing import Tuple

# 3rd party
import wx  # type: ignore[import]

__all__ = ("ToolbarPropertiesPanel", "create_toolbar")

ID_ACCEPT = wx.NewIdRef()
ID_REJECT = wx.NewIdRef()


class ToolbarPropertiesPanel(wx.StaticText):
	"""
	Toolbar static text panel for displaying peak information.
	"""

	# """
	# Toolbar static text panel for displaying project and peak information.
	# """

	# #: The name of the project.
	# project_name: str = ''

	#: The retention time of the currently displayed peak, in minutes.
	retention_time: float = 0

	#: The number currently displayed peak. Zero indexed.
	peak_number: int = 0

	#: The maximum peak number in the project.
	max_peak_number: int = 0

	#: The average match factor for the top compound across the aligned peaks.
	match_factor: float = 0

	def __init__(self, parent: wx.Frame):
		super().__init__(parent, wx.ID_ANY, '', size=(90, -1), style=wx.ALIGN_RIGHT)
		self.redraw()

	def redraw(self) -> None:
		"""
		Update the text with current values.
		"""

		# label_text = f" {self.project_name}   \n {self.retention_time:0.3f} min   \n {self.peak_number+1}/{self.max_peak_number}   "
		# self.SetLabelText(label_text)

		label_text = f" {self.retention_time:0.3f} min   \n {self.peak_number+1}/{self.max_peak_number}   \n {self.match_factor:0.1f}   "
		self.SetLabelText(label_text)


def create_toolbar(
		parent: wx.Frame,
		icon_size: int = 16,
		) -> Tuple[wx.ToolBar, ToolbarPropertiesPanel, wx.StaticText]:
	"""
	Create the main toolbar.
	"""

	toolbar = wx.ToolBar(
			parent,
			-1,
			# style=wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_BOTTOM | wx.TB_TEXT,
			style=wx.TB_HORIZONTAL | wx.TB_BOTTOM | wx.TB_TEXT,
			)

	# toolbar.AddTool(
	# 		wx.ID_EXIT,
	# 		"Quit",
	# 		bitmap=wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR, (icon_size, icon_size)),
	# 		bmpDisabled=wx.NullBitmap,
	# 		kind=wx.ITEM_NORMAL,
	# 		shortHelp="Exit PeakViewer",
	# 		longHelp="Exit PeakViewer",
	# 		)
	# toolbar.AddSeparator()

	# toolbar.AddControl(wx.StaticText(toolbar, wx.ID_ANY, "  Project:   \n  Retention Time:   \n  Peak No.:   "))
	toolbar.AddControl(
			wx.StaticText(
					toolbar,
					wx.ID_ANY,
					"  Retention Time:   \n  Peak No.:   \n  Avg. Match Factor: ",
					)
			)
	toolbar.AddSeparator()
	toolbar_properties_panel = ToolbarPropertiesPanel(toolbar)
	toolbar.AddControl(toolbar_properties_panel)
	toolbar.AddSeparator()
	toolbar_name_panel = wx.StaticText(toolbar, wx.ID_ANY, '')
	toolbar.AddControl(toolbar_name_panel)
	toolbar.AddStretchableSpace()
	toolbar.AddSeparator()

	toolbar.AddTool(
			wx.ID_BACKWARD,
			"&Previous",
			bitmap=wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR, (icon_size, icon_size)),
			bmpDisabled=wx.NullBitmap,
			kind=wx.ITEM_NORMAL,
			shortHelp="Go to the previous peak",
			longHelp="Go to the previous peak",
			).Enable(False)

	toolbar.AddTool(
			wx.ID_FORWARD,
			"&Next",
			bitmap=wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, (icon_size, icon_size)),
			bmpDisabled=wx.NullBitmap,
			kind=wx.ITEM_NORMAL,
			shortHelp="Go to the next peak",
			longHelp="Go to the next peak",
			).Enable(False)
	toolbar.AddSeparator()

	toolbar.AddTool(
			ID_ACCEPT,
			"&Accept",
			bitmap=wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR, (icon_size, icon_size)),
			bmpDisabled=wx.NullBitmap,
			kind=wx.ITEM_NORMAL,
			shortHelp="Accept this peak",
			longHelp="Accept this peak",
			).Enable(False)

	toolbar.AddTool(
			ID_REJECT,
			"&Reject",
			bitmap=wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR, (icon_size, icon_size)),
			bmpDisabled=wx.NullBitmap,
			kind=wx.ITEM_NORMAL,
			shortHelp="Reject this peak",
			longHelp="Reject this peak",
			).Enable(False)

	toolbar.Realize()

	return toolbar, toolbar_properties_panel, toolbar_name_panel
