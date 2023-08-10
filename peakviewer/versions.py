#!/usr/bin/env python3
#
#  versions.py
"""
Tool to get software versions.
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
import platform
import sys

# 3rd party
from domdf_python_tools.stringlist import StringList
from domdf_python_tools.words import LF

# this package
import peakviewer

__all__ = ("get_formatted_versions", )


def get_formatted_versions() -> StringList:
	"""
	Return the versions of this software and its dependencies, one per line.
	"""

	message = StringList()

	our_version = peakviewer.__version__
	message.append(f"Version: {our_version}")

	libgsm_version = importlib.metadata.version("libgunshotmatch")
	message.append(f"LibGunShotMatch: {libgsm_version}")

	mpl_version = importlib.metadata.version("matplotlib")
	message.append(f"Matplotlib: {mpl_version}")

	wx_version = importlib.metadata.version("wxpython")
	message.append(f"wxPython: {wx_version}")

	message.append(f"Python: {sys.version.replace(LF, ' ')}")

	message.append(' '.join(platform.system_alias(platform.system(), platform.release(), platform.version())))

	return message
