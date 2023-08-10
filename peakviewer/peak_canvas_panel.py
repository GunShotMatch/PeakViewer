#!/usr/bin/env python3
#
#  peak_canvas_panel.py
"""
wxPython panel for displaying peaks using matplotlib.
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
import sys
from typing import List, Optional

# 3rd party
import matplotlib  # type: ignore[import]
import wx  # type: ignore[import]
from libgunshotmatch.project import Project
from matplotlib.axes import Axes  # type: ignore[import]
from matplotlib.backend_bases import MouseButton, MouseEvent  # type: ignore[import]
from matplotlib.figure import Figure  # type: ignore[import]

matplotlib.use("WXAgg")

# 3rd party
from matplotlib.backends.backend_wxagg import (  # type: ignore[import]  # noqa: E402
		FigureCanvasWxAgg as FigureCanvas)
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx  # noqa: E402

__all__ = ["PeakCanvasPanel", "PeakCanvasToolbar", "XPanAxes"]


class XPanAxes(matplotlib.axes.Axes):
	"""
	Constrain pan to x-axis.
	"""

	name = "XPanAxes"

	def drag_pan(self, button: MouseButton, key: Optional[str], x: float, y: float) -> None:
		"""

		:param button: The pressed mouse button.
		:param key: The pressed key, if any.
		:param x: The mouse coordinates in display coords.
		:param y: The mouse coordinates in display coords.
		"""

		# pretend key=='x'
		Axes.drag_pan(self, button, 'x', x, y)


matplotlib.projections.register_projection(XPanAxes)


class PeakCanvasToolbar(NavigationToolbar2Wx):
	"""
	Modified Matplotlib toolbar for the peak canvas.
	"""

	_zoom_info: "matplotlib.backend_bases._ZoomInfo"

	toolitems = (
			("Home", "Reset original view", "home", "home"),
			("Back", "Back to previous view", "back", "back"),
			("Forward", "Forward to next view", "forward", "forward"),
			(None, None, None, None),
			("Pan", "Pan along x axis, Right button zooms", "move", "pan"),
			("Zoom", "Zoom along x axis", "zoom_to_rect", "zoom"),
			# ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
			# (None, None, None, None),
			# ('Save', 'Save the figure', 'filesave', 'save_figure'),
			# TODO: override to temporarily add peak info to title
			)

	def drag_zoom(self, event: MouseEvent) -> None:
		"""
		Handler for the zoom action.

		Constrains zoom to the x (time) axis.
		"""

		# print(self._zoom_info.cbar)
		self._zoom_info = self._zoom_info._replace(cbar="horizontal")
		return super().drag_zoom(event)


class PeakCanvasPanel(wx.Panel):
	"""
	Panel to display peaks with matplotlib.
	"""

	axes: List[Axes]

	def __init__(self, parent: wx.Frame, *, n_repeats: int):
		wx.Panel.__init__(self, parent)

		self.figure = Figure()
		self.axes = []
		self.reset(n_repeats)

		self.canvas = FigureCanvas(self, -1, self.figure)

		self.toolbar = PeakCanvasToolbar(self.canvas)
		self.toolbar.Realize()
		self.do_layout()

		self.no_project_stamp = self.figure.text(
				0.5,
				0.5,
				"No Project Opened",
				fontsize=32,
				color="Black",
				horizontalalignment="center",
				verticalalignment="center",
				)

		self.rejected_peak_stamp = self.figure.text(
				0.5,
				0.5,
				"REJECTED",
				rotation=40,
				fontsize=64,
				color="red",
				horizontalalignment="center",
				verticalalignment="center",
				alpha=0.75
				)
		self.rejected_peak_stamp.set_alpha(0)

	def reset(self, n_repeats: int) -> None:
		"""
		Create ``n_repeats`` new, empty axes.
		"""

		for ax in self.axes:
			ax.remove()
		self.axes = self.figure.subplots(n_repeats, 1, sharex=True, subplot_kw=dict(projection="XPanAxes"))

	def do_layout(self) -> None:
		"""
		Perform layout on the panel.
		"""

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
		sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
		self.SetSizer(sizer)
		self.Fit()

	def show_rejected_stamp(self, visible: bool = True) -> None:
		"""
		Show or hide the "REJECTED" stamp.

		:param visible:
		"""

		if visible:
			self.rejected_peak_stamp.set_alpha(0.75)
		else:
			self.rejected_peak_stamp.set_alpha(0)

		self.refresh()

	def show_no_project_stamp(self, visible: bool = True) -> None:
		"""
		Show or hide the "No Project Opened" stamp.

		:param visible:
		"""

		self.no_project_stamp.set_alpha(visible)
		self.refresh()

	def refresh(self) -> None:
		"""
		Refresh the panel and redraw the chart.
		"""

		self.canvas.draw()

	def draw_peak(self, project: Project, peak_idx: int) -> None:
		"""
		Draw a set of aligned peaks.

		:param project:
		:param peak_idx: The index of the peak (in `consolidated_peaks`) to display.
		"""

		for ax in self.axes:
			ax.clear()

		min_rt = sys.maxsize
		max_rt = 0
		for repeat_idx, (name, repeat) in enumerate(project.datafile_data.items()):
			assert repeat.qualified_peaks is not None  # TODO: validate when opening
			peak = repeat.qualified_peaks[peak_idx]
			print(name, peak)

			min_rt = min(min_rt, peak.rt - 20)
			max_rt = max(max_rt, peak.rt + 20)

		for repeat_idx, (name, repeat) in enumerate(project.datafile_data.items()):
			assert repeat.qualified_peaks is not None
			peak = repeat.qualified_peaks[peak_idx]
			assert repeat.datafile.intensity_matrix is not None  # TODO: validate when opening
			im = repeat.datafile.intensity_matrix
			tic = im.tic

			# Get subset of timelist within RT range
			time_list = []
			intensity_list = []
			for rt, intensity in zip(tic.time_list, tic.intensity_array):
				if min_rt <= rt <= max_rt:
					time_list.append(rt / 60)
					intensity_list.append(intensity)

			self.axes[repeat_idx].plot(time_list, intensity_list)
			# self.axes[repeat_idx].vlines([peak.rt], 0, peak.area, colors="red")
			self.axes[repeat_idx].vlines(
					[peak.rt / 60],
					0,
					intensity_list[time_list.index(peak.rt / 60)],
					colors="red",
					)
			self.axes[repeat_idx].text(
					peak.rt / 60,
					self.axes[repeat_idx].get_ylim()[1] * 0.2,
					f" {peak.rt/60:0.3f}",
					)

		self.figure.supylabel("Intensity")
		self.axes[0].autoscale()
		self.axes[-1].set_xlabel("Retention Time (mins)")
		for ax, repeat_name in zip(self.axes, project.datafile_data):
			ax.set_ylim(bottom=0)
			# xmin, xmax = ax.get_xlim()
			# ax.text(xmin + (xmax-xmin)*0.05, ax.get_ylim()[1] *0.8, repeat_name)
			ax.annotate(repeat_name, (0.01, 0.8), xycoords="axes fraction")
		self.axes[0].set_xlim(min_rt / 60, max_rt / 60)
		# self.figure.subplots_adjust(bottom=0, top=1, left=0, right=1, hspace=0, wspace=0)
		self.figure.subplots_adjust(top=0.95, right=0.95)
		self.refresh()

		# self.Layout()
		# self.Update()
		# self.Layout()
		# self.Update()
