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
from distutils.command.install_lib import install_lib
import os
import subprocess

from libgkonap.gkpath import wersja

DATA_FILES = [('/usr/share/pixmaps', ['libgkonap/gfx/gkonap.xpm']),
              ('/usr/share/pixmaps/gkonap', ['libgkonap/gfx/icon.svg']),
              ('/usr/share/menu', ['gkonap']),
              ('/usr/share/applications', ['gkonap.desktop'])]
PKG_DATA = ['glade/*', 'gfx/*']


class Install_lib(install_lib):
    def run(self):
        install_lib.run(self)
        
        install_dir =  self.install_dir
        install_dir = install_dir + 'libgkonap/'
        path_gkonap = install_dir + 'gkonap.py'
        path_konap = install_dir + 'konap.py'
        if os.path.exists(path_gkonap):
            cmd = 'ln -s %s /usr/bin/gkonap' % path_gkonap
            links_symbolic = subprocess.Popen(cmd, shell=True, stdout=None)
            links_symbolic.wait()
            cmd_1 = "chmod ugo+x %s" % path_gkonap
            chmod = subprocess.Popen(cmd_1, shell=True, stdout=None)
            chmod.wait()
        else:
            raise RuntimeError()
        
        if os.path.exists(path_konap):
            cmd = 'ln -s %s /usr/bin/konap' % path_konap
            links_symbolic = subprocess.Popen(cmd, shell=True, stdout=None)
            links_symbolic.wait()
            cmd_1 = "chmod ugo+x %s" % path_konap
            chmod = subprocess.Popen(cmd_1, shell=True, stdout=None)
            chmod.wait()
        else:
            raise RuntimeError()
            
setup(name = "gKonap",
      version = wersja,
      description = "gKonap - subtitle converter and subtitle downloader",
      author = "Daniel Dereziński",
      author_email = "daniel.derezinski@gmail.com",
      maintainer = "Daniel Dereziński",
      maintainer_email = "daniel.derezinski@gmail.com",
      data_files = DATA_FILES,
      packages = ['libgkonap'],
      package_data = {'libgkonap':PKG_DATA},
      cmdclass={'install_lib': Install_lib}
      )