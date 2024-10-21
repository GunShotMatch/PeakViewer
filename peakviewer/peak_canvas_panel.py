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
# y-axis rescaling (including calculate_new_limit) from
# https://stackoverflow.com/questions/29461608/fixing-x-axis-scale-and-autoscale-y-axis
# By Daniel H. (https://stackoverflow.com/users/8006684/daniel-h)
# and TomNorway (https://stackoverflow.com/users/1018861/tomnorway)
# CC BY-SA 4.0
#

# stdlib
import math
from typing import TYPE_CHECKING, List, Optional, Tuple

# 3rd party
import matplotlib
import wx  # type: ignore[import]
from libgunshotmatch.project import Project
from libgunshotmatch_mpl.peakviewer import draw_peaks
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event, MouseButton
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

matplotlib.use("WXAgg")

# 3rd party
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg  # noqa: E402
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg  # noqa: E402

if TYPE_CHECKING:
	# 3rd party
	import numpy

__all__ = ("PeakCanvasPanel", "PeakCanvasToolbar", "XPanAxes")


class XPanAxes(Axes):
	"""
	Constrain pan to x-axis.
	"""

	name = "XPanAxes"

	def drag_pan(self, button: MouseButton, key: Optional[str], x: float, y: float) -> None:
		"""
		Handler for the pan action.

		Constrains pan to the x (time) axis.

		:param button: The pressed mouse button.
		:param key: The pressed key, if any. Ignored and always substituted with the ``x`` key.
		:param x: The mouse coordinates in display coords.
		:param y: The mouse coordinates in display coords.
		"""

		# pretend key=='x'
		Axes.drag_pan(self, button, 'x', x, y)

	def format_ydata(self, y: float) -> str:
		"""
		Format a y-axis value in scientific notation.
		"""

		return _format_scientific(y)

	def format_coord(self, x: float, y: float) -> str:
		"""
		Format the x and y coordinates.
		"""

		formatted_x = "???" if x is None else self.format_xdata(x)
		formatted_y = "???" if y is None else self.format_ydata(y)
		return f"T={formatted_x} mins y={formatted_y}     ​"


matplotlib.projections.register_projection(XPanAxes)


class PeakCanvasToolbar(NavigationToolbar2WxAgg):
	"""
	Modified Matplotlib toolbar for the peak canvas.
	"""

	_zoom_info: "matplotlib.backend_bases._ZoomInfo"  # type: ignore[name-defined]

	toolitems = (
			("Home", "Reset original view", "home", "home"),
			("Back", "Back to previous view", "back", "back"),
			("Forward", "Forward to next view", "forward", "forward"),
			(None, None, None, None),
			("Pan", "Pan along x axis, Right button zooms", "move", "pan"),
			("Zoom", "Zoom along x axis", "zoom_to_rect", "zoom"),
			("Subplots", "Configure subplots", "subplots", "configure_subplots"),
			)

	def drag_zoom(self, event: Event) -> None:
		"""
		Handler for the zoom action.

		Constrains zoom to the x (time) axis.
		"""

		# print(self._zoom_info)
		# print(self._zoom_info.cbar)
		self._zoom_info = self._zoom_info._replace(cbar="horizontal")
		ret = super().drag_zoom(event)
		return ret

	def set_message(self, s: str) -> None:
		"""
		Set the status message (mouse coordinates) in the taskbar.

		:param s: The message string.
		"""

		if self._coordinates:
			self._label_text.SetLabel(s)


def calculate_new_limit(fixed: "numpy.ndarray", dependent: "numpy.ndarray", limit: Tuple[float, float]) -> float:
	"""
	Calculates the min/max of the dependent axis given a fixed axis with limits.

	:param fixed:
	:param dependent:
	:param limit:
	"""

	if len(fixed) > 2:
		mask = (fixed > limit[0]) & (fixed < limit[1])
		window = dependent[mask]
		high = window.max()

	else:
		high = dependent[-1]
		if dependent[0] == 0.0 and high == 1.0:
			# This is a axhline in the autoscale direction
			high = 0
	return high


class PeakCanvasPanel(wx.Panel):
	"""
	Panel to display peaks with matplotlib.
	"""

	axes: List[Axes]

	# If True all y axes have the same scale, otherwise they scale to the largest value in each
	link_vertical_axes = False

	def __init__(self, parent: wx.Frame, *, n_repeats: int):
		wx.Panel.__init__(self, parent)

		self.figure = Figure(layout="constrained")
		self.axes: List[Axes] = []
		self.reset(n_repeats)

		self.figure.canvas.mpl_connect("draw_event", self.rescale_y_axis)

		self.canvas = FigureCanvasWxAgg(self, -1, self.figure)

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

	def rescale_y_axis(self, event: Event) -> None:
		"""
		Rescale the y-axis in response to a change in the x axis limits (pan or zoom).
		"""

		# Only redraw if there needs to be a change,
		# otherwise there'll be an infinite loop.
		should_redraw = False

		maxima = []

		for ax in self.axes:
			for artist in ax.lines:
				assert isinstance(artist, Line2D)
				x: "numpy.ndarray" = artist.get_xdata()  # type: ignore[assignment]
				y: "numpy.ndarray" = artist.get_ydata()  # type: ignore[assignment]
				try:
					high = calculate_new_limit(x, y, ax.get_xlim())
				except Exception:
					maxima.append(ax.get_ylim()[1])
					continue

				newhigh = high if high > 0 else 0
				current_ylim = ax.get_ylim()[1]
				new_ylim = newhigh * 1.2  # Add a little space above the line
				# print(new_ylim, current_ylim)
				maxima.append(new_ylim)

		if self.link_vertical_axes:
			if maxima:
				new_ylim = max(maxima)
				for ax in self.axes:
					current_ylim = ax.get_ylim()[1]
					if new_ylim != current_ylim:
						ax.set_ylim(0, new_ylim)
						should_redraw = True
		else:
			# ax: Axes
			for new_ylim, ax in zip(maxima, self.axes):
				current_ylim = ax.get_ylim()[1]
				if new_ylim != current_ylim:
					ax.set_ylim(0, new_ylim)
					should_redraw = True

		if should_redraw:
			self.refresh()

	def reset(self, n_repeats: int) -> None:
		"""
		Create ``n_repeats`` new, empty axes.

		:param n_repeats:
		"""

		for ax in self.axes:
			ax.remove()

		self.axes = self.figure.subplots(
			n_repeats,
			1,
			sharex=True,
			subplot_kw=dict(projection="XPanAxes"),
			)

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

	def draw_peak(self, project: Project, retention_times: List[float]) -> None:
		"""
		Draw a set of aligned peaks.

		:param project:
		:param peak_idx: The index of the peak (in `consolidated_peaks`) to display.
		"""

		for ax in self.axes:
			ax.clear()

		draw_peaks(project, retention_times, self.figure, self.axes)

		self.refresh()

		# self.Layout()
		# self.Update()
		# self.Layout()
		# self.Update()


_superscript_translate_map = {ord(str(num)): sup for num, sup in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹")}
_superscript_translate_map[ord('-')] = '⁻'
# print(_superscript_translate_map)


def _format_scientific(value: float) -> str:
	n = math.floor(math.log10(value))
	significand = value / 10**n
	if n <= 1:
		return f"{value:0.3f}"
	power = str(n).translate(_superscript_translate_map)
	return f'{significand:0.3f}×10{power}'
