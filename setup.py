#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
#       setup
#       
#       Copyright 2012 Daniel Dereziński <daniel.derezinski@gmial.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA

from distutils.core import setup
from distutils.command.install import install
import os
import subprocess

from gkpath import wersja

class Install(install):
    def run(self):
        super(Install, self).run()
        


DATA_FILES = [('/usr/share/pixmaps', ['gfx/gkonap.xmp']),
              ('/usr/share/menu', ['gkonap']),
              ('/usr/share/applications', ['gkonap.desktop']),
              'gfx/icon.svg',
              'gkonap.glade']

setup(name = "gKonap",
      version = wersja,
      description = "gKonap - subtitle converter and subtitle downloader",
      author = "Daniel Dereziński",
      author_email = "daniel.derezinski@gmail.com",
      maintainer = "Daniel Dereziński",
      maintainer_email = "daniel.derezinski@gmail.com",
      data_files = DATA_FILES,
      py_modules = ['gkonap', 'konap', 'gkpath', ]
      )