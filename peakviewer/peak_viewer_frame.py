#!/usr/bin/env python3
#
#  peak_viewer_frame.py
"""
wxPython frame for displaying peaks from a :class:`~.Project`, with controls.
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
import importlib.resources
import os
import textwrap
from typing import Any, Optional

# 3rd party
import wx  # type: ignore[import]
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from libgunshotmatch import gzip_util
from libgunshotmatch.project import Project

# this package
from peakviewer.about_dialog import AboutDialog
from peakviewer.peak_canvas_panel import PeakCanvasPanel
from peakviewer.toolbar import ID_ACCEPT, ID_REJECT, ToolbarPropertiesPanel, create_toolbar

__all__ = ["PeakViewerFrame", "ProjectDropTarget", "UnsupportedProject"]


class UnsupportedProject(ValueError):
	"""
	Exception raised when a project is missing certain attributes (such as the consolidated peak list).
	"""


class PeakViewerFrame(wx.Frame):
	"""
	Main frame for Peak Viewer. Contains the toolbar, menubar and peak canvas panel.
	"""

	#: The index of the currently displayed peak.
	peak_idx: int = 0

	#: The currently open project, or :py:obj:`None` if no project is open.
	project: Optional[Project] = None

	#: The last directory a file was opened from.
	last_directory: str = ''

	#: The panel for displaying the peaks.
	panel: PeakCanvasPanel

	#: The toolbar panel displaying project/peak information.
	toolbar_properties_panel: ToolbarPropertiesPanel

	#: The toolbar panel displaying the compound name for the peak.
	toolbar_name_panel: wx.StaticText

	def __init__(self, title: str):
		wx.Frame.__init__(self, None, -1, title, size=(620, 620))

		self.SetMinSize((680, 620))
		self.set_icon()

		self.panel = PeakCanvasPanel(self, n_repeats=5)
		self.panel.SetDropTarget(ProjectDropTarget(self))

		self.create_menubar()

		toolbar, self.toolbar_properties_panel, self.toolbar_name_panel = create_toolbar(self, icon_size=32)
		self.SetToolBar(toolbar)

		self.bind_events()

	def set_icon(self) -> None:
		"""
		Set the icon for the frame.
		"""

		icon = wx.NullIcon
		with importlib.resources.path("peakviewer.icons", "GunShotMatch logo256.png") as icon_path:
			icon.CopyFromBitmap(wx.Bitmap(os.fspath(icon_path), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)

	def create_menubar(self) -> None:
		"""
		Create the menubar.
		"""

		menubar = wx.MenuBar()

		file_menu = wx.Menu()
		file_menu.Append(wx.ID_OPEN, "&Open Project\tCtrl+O")
		file_menu.Append(wx.ID_SAVE, "&Save Project\tCtrl+S").Enable(False)
		file_menu.AppendSeparator()
		file_menu.Append(wx.ID_EXIT, "&Quit")
		# file_menu.FindItemById(wx.ID_SAVE).Enable(False)

		menubar.Append(file_menu, "&File")

		peak_menu = wx.Menu()
		peak_menu.Append(wx.ID_FORWARD, "&Next").Enable(False)
		peak_menu.Append(wx.ID_BACKWARD, "&Previous").Enable(False)
		peak_menu.Append(wx.ID_FIRST, "Go to %First").Enable(False)
		peak_menu.Append(wx.ID_LAST, "Go to %Last").Enable(False)
		peak_menu.AppendSeparator()
		peak_menu.Append(ID_ACCEPT, "&Accept\tCtrl+A").Enable(False)
		peak_menu.Append(ID_REJECT, "&Reject\tCtrl+R").Enable(False)
		menubar.Append(peak_menu, "&Peak")

		help_menu = wx.Menu()
		help_menu.Append(wx.ID_ABOUT, "&About")
		menubar.Append(help_menu, "&Help")

		self.SetMenuBar(menubar)

	def bind_events(self) -> None:
		"""
		Bind event handlers.
		"""

		self.Bind(wx.EVT_MENU, self.on_open_project, id=wx.ID_OPEN)
		self.Bind(wx.EVT_MENU, self.on_save_project, id=wx.ID_SAVE)
		self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
		self.Bind(wx.EVT_MENU, self.on_accept, id=ID_ACCEPT)
		self.Bind(wx.EVT_MENU, self.on_reject, id=ID_REJECT)
		self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
		self.Bind(wx.EVT_MENU, self.on_next_peak, id=wx.ID_FORWARD)
		self.Bind(wx.EVT_MENU, self.on_previous_peak, id=wx.ID_BACKWARD)
		self.Bind(wx.EVT_MENU, self.on_goto_first, id=wx.ID_FIRST)
		self.Bind(wx.EVT_MENU, self.on_goto_last, id=wx.ID_LAST)

		self.Bind(wx.EVT_CHAR_HOOK, self.on_keypress)

	def on_keypress(self, event: wx.KeyEvent) -> None:
		"""
		Handle a keypress and respond to the left and right arrow keys.
		"""

		keycode = event.GetKeyCode()
		if keycode == wx.WXK_LEFT:
			if self.peak_idx != 0:
				self.peak_idx -= 1
				self.draw_peak()
		elif keycode == wx.WXK_RIGHT:
			if self.project is not None:
				self._advance()
		else:
			event.Skip()

	def draw_peak(self) -> None:
		"""
		Draw a set of aligned peaks.
		"""

		if self.project is None:
			raise ValueError("No project loaded")

		if self.project.consolidated_peaks is None:
			raise ValueError("Project.consolidated_peaks is unset")

		# for ax in self.panel.axes:
		# 	ax.clear()

		if self.peak_idx == len(self.project.consolidated_peaks) - 1:
			self.GetToolBar().EnableTool(wx.ID_FORWARD, False)
			self.GetMenuBar().FindItemById(wx.ID_FORWARD).Enable(False)
			self.GetMenuBar().FindItemById(wx.ID_LAST).Enable(False)
		else:
			self.GetToolBar().EnableTool(wx.ID_FORWARD, True)
			self.GetMenuBar().FindItemById(wx.ID_FORWARD).Enable(True)
			self.GetMenuBar().FindItemById(wx.ID_LAST).Enable(True)

		if self.peak_idx == 0:
			self.GetToolBar().EnableTool(wx.ID_BACKWARD, False)
			self.GetMenuBar().FindItemById(wx.ID_BACKWARD).Enable(False)
			self.GetMenuBar().FindItemById(wx.ID_FIRST).Enable(False)
		else:
			self.GetToolBar().EnableTool(wx.ID_BACKWARD, True)
			self.GetMenuBar().FindItemById(wx.ID_BACKWARD).Enable(True)
			self.GetMenuBar().FindItemById(wx.ID_FIRST).Enable(True)

		peak = self.project.consolidated_peaks[self.peak_idx]
		print(peak)

		print(peak.rt_list)

		if peak.meta.get("acceptable_shape", True):
			self.panel.rejected_peak_stamp.set_alpha(0)
		else:
			self.panel.rejected_peak_stamp.set_alpha(0.75)

		self.toolbar_properties_panel.peak_number = self.peak_idx
		self.toolbar_properties_panel.retention_time = peak.rt / 60
		self.toolbar_properties_panel.redraw()

		self.toolbar_name_panel.SetLabelText('\n'.join(textwrap.wrap(peak.hits[0].name, width=25)))

		self.panel.draw_peak(self.project, peak.meta["peak_number"])

	def load_project(self, filename: PathLike) -> None:
		"""
		Load a project from the given file.

		:param filename:
		"""

		wait = wx.BusyInfo(f"Loading project from file {filename}", parent=self)
		wx.Yield()

		try:

			project = Project.from_file(filename)

			# Validation of loaded datafile
			if project.consolidated_peaks is None:
				raise UnsupportedProject("Project.consolidated_peaks is unset")

			for (name, repeat) in project.datafile_data.items():
				if repeat.qualified_peaks is None:
					raise UnsupportedProject(f"Repeat.qualified_peaks is unset for {name!r}")
				if repeat.datafile.intensity_matrix is None:
					raise UnsupportedProject(f"Datafile.intensity_matrix is unset for {name!r}")

			self.project = project
			self.SetTitle(f"Peak Viewer – {project.name}")
			self.panel.reset(len(project.datafile_data))
			self.peak_idx = 0
			self.draw_peak()
			self.toolbar_properties_panel.project_name = project.name
			self.toolbar_properties_panel.max_peak_number = len(project.consolidated_peaks)
			self.toolbar_properties_panel.redraw()

			menubar = self.GetMenuBar()
			menubar.GetMenu(menubar.FindMenu("File")).FindItemById(wx.ID_SAVE).Enable(True)
			peak_menu = menubar.GetMenu(menubar.FindMenu("Peak"))
			peak_menu.FindItemById(ID_ACCEPT).Enable(True)
			peak_menu.FindItemById(ID_REJECT).Enable(True)
			peak_menu.FindItemById(wx.ID_FORWARD).Enable(True)
			peak_menu.FindItemById(wx.ID_LAST).Enable(True)

			toolbar = self.GetToolBar()
			# toolbar.EnableTool(wx.ID_BACKWARD, True)
			toolbar.EnableTool(wx.ID_FORWARD, True)
			toolbar.EnableTool(ID_ACCEPT, True)
			toolbar.EnableTool(ID_REJECT, True)
			toolbar.Realize()

		except OSError:
			wx.LogError("Cannot open file '%s'." % filename)
		except UnsupportedProject as e:
			wx.MessageBox(str(e), "Unsupported Project File", style=wx.ICON_ERROR | wx.OK)
		finally:
			del wait

	def on_open_project(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Open Project' and menuentry.
		"""

		with wx.FileDialog(
				self,
				"Open Project file",
				wildcard="GunShotMatch Project files (*.gsmp)|*.gsmp",
				style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
				) as fileDialog:

			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return

			pathname = fileDialog.GetPath()
			self.last_directory = os.path.split(pathname)[0]
			self.load_project(pathname)

	def on_save_project(self, event: wx.CommandEvent) -> None:
		"""
		Handler for the "Save" button.
		"""

		if self.project is None:
			raise ValueError("No project loaded")

		with wx.FileDialog(
				self,
				"Save Project",
				wildcard="GunShotMatch Project files (*.gsmp)|*.gsmp",
				style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
				defaultDir=self.last_directory,
				defaultFile=f"{self.project.name}.gsmp"
				) as fileDialog:
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return

			pathname = fileDialog.GetPath()
			wait = wx.BusyInfo(f"Saving {pathname}", parent=self)
			wx.Yield()
			gzip_util.write_gzip_json(pathname, self.project.to_dict(), indent=0)
			del wait

	def on_quit(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Quit' button and menuentry.
		"""

		self.Close()

	def on_accept(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Accept Peak' button and menuentry.
		"""

		if self.project is None:
			raise ValueError("No project loaded")

		if self.project.consolidated_peaks is None:
			raise ValueError("Project.consolidated_peaks is unset")

		cp = self.project.consolidated_peaks[self.peak_idx]
		print("Accepted peak", cp)
		if not cp.meta.get("acceptable_shape", False):
			cp.meta["acceptable_shape"] = True
			self.panel.rejected_peak_stamp.set_alpha(0)
			self.panel.refresh()

		self._advance()

	def on_reject(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Reject Peak' button and menuentry.
		"""

		if self.project is None:
			raise ValueError("No project loaded")

		if self.project.consolidated_peaks is None:
			raise ValueError("Project.consolidated_peaks is unset")

		cp = self.project.consolidated_peaks[self.peak_idx]
		print("Rejected peak", cp)
		if cp.meta.get("acceptable_shape", True):
			cp.meta["acceptable_shape"] = False
			self.panel.rejected_peak_stamp.set_alpha(0.75)
			self.panel.refresh()

		self._advance()

	def _advance(self) -> None:

		if self.project is None:
			raise ValueError("No project loaded")

		if self.project.consolidated_peaks is None:
			raise ValueError("Project.consolidated_peaks is unset")

		if self.peak_idx == len(self.project.consolidated_peaks) - 1:
			return

		self.peak_idx += 1
		self.draw_peak()

	def on_next_peak(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Next Peak' button and menuentry.
		"""

		self._advance()

	def on_previous_peak(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Previous Peak' button and menuentry.
		"""

		self.peak_idx -= 1
		self.draw_peak()

	def on_goto_first(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Go to First Peak' menuentry.
		"""

		self.peak_idx = 0
		self.draw_peak()

	def on_goto_last(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'Go to Last Peak' menuentry.
		"""

		if self.project is None:
			raise ValueError("No project loaded")

		if self.project.consolidated_peaks is None:
			raise ValueError("Project.consolidated_peaks is unset")

		self.peak_idx = len(self.project.consolidated_peaks) - 1
		self.draw_peak()

	def on_about(self, event: wx.CommandEvent) -> None:
		"""
		Handler for 'About' menuentry.
		"""

		msg = AboutDialog(self)
		msg.ShowModal()


class ProjectDropTarget(wx.TextDropTarget):
	"""
	Drop target for the chart panel to accept a dragged project file.
	"""

	def __init__(self, parent: PeakViewerFrame):

		wx.TextDropTarget.__init__(self)
		self.parent: PeakViewerFrame = parent

	def OnDropText(self, x: Any, y: Any, data: str) -> bool:  # noqa: D102

		if data.startswith("file://"):
			filename = PathPlus.from_uri(data)
		else:
			filename = PathPlus(data)
		self.parent.load_project(filename)
		return True
