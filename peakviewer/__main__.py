#!/usr/bin/env python3
#
#  __main__.py
"""
CLI entry point for the Peak Viewer.
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
import click

__all__ = ["main"]


@click.argument(
		"filename",
		default=None,
		required=False,
		type=click.Path(file_okay=True, dir_okay=False, exists=True),
		)
@click.command
def main(filename: Optional[str] = None) -> None:
	"""
	GunShotMatch Peak Viewer.
	"""  # noqa: D403

	# this package
	from peakviewer.app import PeakViewerApp

	app = PeakViewerApp(filename)
	app.MainLoop()


if __name__ == "__main__":
	main()
