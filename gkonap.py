#!/usr/bin/env python
#-*- coding: utf-8 -*-

#
# Copyright (c) 2008, Daniel Dereziński
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
# 
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
# http://www.fsf.org/licensing/licenses/lgpl.txt
#

# Moduł odpowiedzialny za ściąganie napisów powstał na podstawie skryptu napisanego przez: 
#  - gim, 
#  - krzynio, 
#  - dosiu, 
#  - hash.
# Oryginalny skrypt można pobrać ze strony:
#
# http://hacking.apcoh.com/2008/01/napi_06.html
#
# Gratsy dla nich!!! 

#        Zasługi dla:
#        Konrad Kasiel  <konirad@o2.pl> - za poprawki dla konap. 

import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import konap
import os.path
import locale
import sys
import md5
import urllib
import time
import re
import webbrowser
import ctypes
import gkpath

__nazwa__ = u"gkonap"
__wersja__ = gkpath.wersja
__autor__ = [u"Daniel 'yp2' Dereziński <daniel.derezinski@gmail.com>"]
__copyright__ = u"Copyleft 2008 Daniel 'yp2' Dereziński"
__website__ = u"http://yp2.pendragon.com.pl/projekty/gkonap/"
__opis__ = u"Program do konwersji formatów napisów dla filmów. \
Obsługuje następujące formaty: MicroDVD, MPL2, SubRip oraz TMPlayer tylko jako format wejściowy. \
Program posiada obsługę serwisu Napiprojekt do ściągania napisów do filmów."

##Nazwa procesu
libc = ctypes.CDLL('libc.so.6')
libc.prctl(15, __nazwa__+'\0', 0, 0, 0)

class Gui:
    
    def __init__(self):
        
        self.ext_video = ['.avi', '.rmvb', '.divx', '.rm', '.mpg', '.mpeg', '.mp4', \
                          '.wmv', '.asf', '.mkv', '.ogm']
        self.ext_napisy = ['.txt', '.sub', '.srt']
        
        self.domyslny_katalog = gkpath.domyslny_katalog
        self.config_file = gkpath.config_file
        self.icon = gkpath.icon
        self.gladefile = gkpath.gladefile
        self.wtr = gtk.glade.XML(self.gladefile)
        
        #Handlers
        gui_han = {"on_GuiKonap_destroy" : self.quit,
                   "on_bnt_Wykonaj_clicked" : self.wykonaj,
                   "on_bnt_Sciezka_Plik_clicked": self.sciezka_p,
                   "on_bnt_Sciezka_Katalog_clicked" : self.sciezka_k,
                   "on_cbnt_Nadpisz_toggled" : self.nadpisz,
                   "on_wideo_plik_clicked" : self.sciezka_wideo_p,
                   "on_wideo_katalog_clicked" : self.sciezka_wideo_k,
                   "on_bnt_Zamknij1_clicked" : self.quit,
                   "on_bnt_Wykonaj1_clicked" : self.wykonaj_sciag_napisy,
                   "on_Opcje_activate" : self.rozmiar_gl_okno,
                   "on_bnt_About_clicked": self.about_dialog}
        
        self.wtr.signal_autoconnect(gui_han)       
        
        #Buttons
        
        self.GuiKonap = self.wtr.get_widget("GuiKonap")        
        self.cbnt_Rekur = self.wtr.get_widget("cbnt_Rekur")
        self.cbx_Format = self.wtr.get_widget("cbx_Format")
        self.sciezka_wy = self.wtr.get_widget("Sciezka_wy")
        self.cbxe_Fps = self.wtr.get_widget("cbxe_Fps_wejscie")
        self.cbnt_Nadpisz = self.wtr.get_widget("cbnt_Nadpisz")
        self.cbnt_Znacznik = self.wtr.get_widget("cbnt_Znacznik")
        self.en_Roz = self.wtr.get_widget("en_Roz")
        self.statusbar = self.wtr.get_widget("statusbar")
        self.cbnt_XBMC = self.wtr.get_widget("cbnt_XBMC")
        
        self.last_used_dir_napisy = ''
        self.last_used_dir_wideo = ''
        self.wczytaj_opcje()
        
        self.textbufor = gtk.TextBuffer(table=None)
        self.sciezka_wy.set_buffer(self.textbufor)
        self.GuiKonap.set_icon_from_file(self.icon)
        
        self.opcje={}        
        self.napisy_wy_ok=[]
        self.napisy_wy_er=[]
        self.napisy_wy_istn=[]
        self.opcje['sciezka'] = []
        self.opcje['sciezka_wideo'] = []
        self.okno_rozmiar = self.GuiKonap.get_child_requisition()
        
        #status bar
        self.stb_id = self.statusbar.get_context_id("gkonap")
        self.statusb_zm_info("Gotowy.")
        
        self.init_gkonap()
    
    def statusb_zm_info(self, mes):    
        self.statusbar.push(self.stb_id, mes)
        
    def stausb_us_info(self):
        self.statusbar.pop(self.stb_id)
        
    def rozmiar_gl_okno(self, widget):
        okno = self.GuiKonap
        okno.set_size_request(-1, -1)
        if okno.get_child_requisition() > self.okno_rozmiar:
            #większe
            w, h = self.okno_rozmiar
            okno.set_size_request(w,h)
            okno.resize(w, h)
        else:
            pass
        
    def wyjscie(self):
        okno = gtk.glade.XML(self.gladefile, "Info")
        
        info = okno.get_widget("Info")
        info.set_icon_from_file(self.icon)
        info.set_property('skip-taskbar-hint', True)
        
        text_konap_b = gtk.TextBuffer(table=None)
        text_konap = okno.get_widget("Info_wyjscie")
        text_konap.set_buffer(text_konap_b)
              
        if len(konap.wyjscie_error) != 0 and len(konap.wyjscie_ok) != 0:
            text_konap_b.set_text("Wykonano konwersję plików:\n%s \n - na format %s\n\nInfo\n%s" % ("\n".join([os.path.split(ele)[1] for ele in konap.wyjscie_ok]), self.cbx_Format.get_active_text(), "\n".join(konap.wyjscie_error)))
        
        elif len(konap.wyjscie_error) != 0 and len(konap.wyjscie_ok) == 0:
            text_konap_b.set_text("Info:\n%s" % "\n".join(konap.wyjscie_error))
        
        elif len(konap.wyjscie_error) == 0 and len(konap.wyjscie_ok) != 0:
            text_konap_b.set_text("Wykonano konwersję plików:\n%s \n - na format %s\n\n" % ("\n".join([os.path.split(ele)[1] for ele in konap.wyjscie_ok]), self.cbx_Format.get_active_text()))
        
        elif len(self.napisy_wy_ok) != 0 and len(self.napisy_wy_er) != 0 and len(self.napisy_wy_istn) == 0:
            text_konap_b.set_text("Pobrano napisy do filmu/filmów:\n%s\n\nBrak napisów do filmu/filmów:\n%s" % ("\n".join(self.napisy_wy_ok), "\n".join(self.napisy_wy_er)))
        
        elif len(self.napisy_wy_ok) != 0 and len(self.napisy_wy_er) == 0 and len(self.napisy_wy_istn) == 0:
            text_konap_b.set_text("Pobrano napisy do filmu/filmów:\n%s" % "\n".join(self.napisy_wy_ok))
        
        elif len(self.napisy_wy_ok) == 0 and len(self.napisy_wy_er) != 0 and len(self.napisy_wy_istn) == 0:
            text_konap_b.set_text("Brak napisów do filmu/filmów:\n%s" % "\n".join(self.napisy_wy_er))
        
        elif len(self.napisy_wy_ok) != 0 and len(self.napisy_wy_er) != 0 and len(self.napisy_wy_istn) != 0:
            text_konap_b.set_text("Pobrano napisy do filmu/filmów:\n%s\n\nBrak napisów do filmu/filmów:\n%s\n\nNapisy istnieją dla filmu/filmów:\n%s" % ("\n".join(self.napisy_wy_ok), "\n".join(self.napisy_wy_er), "\n".join(self.napisy_wy_istn)))
        
        elif len(self.napisy_wy_ok) != 0 and len(self.napisy_wy_er) == 0 and len(self.napisy_wy_istn) != 0:
            text_konap_b.set_text("Pobrano napisy do filmu/filmów:\n%s\n\nNapisy istnieją dla filmu/filmów:\n%s" % ("\n".join(self.napisy_wy_ok), "\n".join(self.napisy_wy_istn)))
        
        elif len(self.napisy_wy_ok) == 0 and len(self.napisy_wy_er) != 0 and len(self.napisy_wy_istn) != 0:
            text_konap_b.set_text("Brak napisów do filmu/filmów:\n%s\n\nNapisy istnieją dla filmu/filmów:\n%s" % ("\n".join(self.napisy_wy_er), "\n".join(self.napisy_wy_istn)))
        
        elif len(self.napisy_wy_istn) != 0:
            text_konap_b.set_text("Napisy istnieją dla filmu/filmów:\n%s" % "\n".join(self.napisy_wy_istn))
            
        response = info.run()
        if response == gtk.RESPONSE_OK:
            info.destroy()
        else:
            info.destroy()
            
    def info_gkonap(self,list,rodzaj):
        #funkcja pomocnicza dla wyświetlania inforamcji dla user'a
        #list - lista zawierająca ścieżki dla programu
        #rodzja - p - pliki, k - katalogi
        if rodzaj == 'p':
            nazwy_plikow = [os.path.split(ele)[1] for ele in list]
            nazwy_plikow = "\n".join(nazwy_plikow)
            self.textbufor.set_text("Wybrano plik/pliki:\n%s" % (nazwy_plikow))
            self.sciezka_wy.get_buffer()
        elif rodzaj == 'k':
            nazwy_kat = [os.path.split(ele)[1] for ele in list]
            nazwy_kat = "\n".join(nazwy_kat)
            self.textbufor.set_text("Wybrano katalog:\n%s " % (nazwy_kat))
            self.sciezka_wy.get_buffer()
    
    def about_dialog(self, widget):
        wtr = gtk.glade.XML(self.gladefile, "About")
        dialog = wtr.get_widget("About")
        dialog.set_name(__nazwa__)
        dialog.set_version(__wersja__)
        dialog.set_icon_from_file(self.icon)
        dialog.set_website(__website__)
        dialog.set_website_label("Strona projektu")
        dialog.set_comments(__opis__)
        dialog.set_authors(__autor__)
        dialog.set_copyright(__copyright__)
        
        response = dialog.run()
        if response == gtk.RESPONSE_CLOSE:
            dialog.destroy()
        else:
            dialog.destroy()
       
    def sciezka_wideo_p(self, widget):
        konap.wyjscie_error[:] = []
        konap.wyjscie_ok[:] = []
        self.napisy_wy_er[:] = []
        self.napisy_wy_ok[:] = []
        self.napisy_wy_istn[:] = []
        dialog = gtk.FileChooserDialog("Otwórz...",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(self.icon)
        if self.last_used_dir_wideo == '':
            dialog.set_current_folder(os.path.expandvars(self.domyslny_katalog))
        else:
            dialog.set_current_folder(os.path.expandvars(self.last_used_dir_wideo))
            
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_select_multiple(True)
        
        filter = gtk.FileFilter()
        filter.set_name("Wszystkie plik")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("Wideo")
        filter.add_pattern("*.avi")
        filter.add_pattern("*.rmvb")
        filter.add_pattern("*.divx")
        filter.add_pattern("*.rm")
        filter.add_pattern("*.mpg")
        filter.add_pattern("*.mp4")
        filter.add_pattern("*.wmv")
        filter.add_pattern("*.asf")
        filter.add_pattern("*.mkv")
        filter.add_pattern("*.ogm")
        dialog.add_filter(filter)
        dialog.set_filter(filter)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.opcje["sciezka_wideo"][:] = []
            plik = dialog.get_filenames()
            self.last_used_dir_wideo = os.path.split(plik[0])[0]
            plik = [ele for ele in plik if os.path.splitext(ele)[1] in self.ext_video]
            for ele in plik:
                spr_napisy=self.spr_napisy(ele)
                if len(spr_napisy) != 0:
                    #napisy dla pliku istnieją pomiń plik
                    self.napisy_wy_istn.append(os.path.split(ele)[1])
                elif len(spr_napisy) == 0:
                    #napisów nie ma plik ok dodaj do listy
                    self.opcje["sciezka_wideo"].append(ele)
            if len(self.napisy_wy_istn) != 0:
                self.wyjscie()
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
        
        
    def sciezka_wideo_k(self, widget):
        dialog = gtk.FileChooserDialog("Wybierz katalog...",
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(self.icon)
        if self.last_used_dir_wideo == '':
            dialog.set_current_folder(os.path.expandvars(self.domyslny_katalog))
        else:
            dialog.set_current_folder(os.path.expandvars(self.last_used_dir_wideo))
        dialog.set_property('skip-taskbar-hint', True)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            plik = [dialog.get_filename()]
            self.last_used_dir_wideo = plik[0]
            self.opcje["sciezka_wideo"][:] = []
            self.opcje["sciezka_wideo"] = plik
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
    
    def sciezka_p(self, widget):
        dialog = gtk.FileChooserDialog("Otwórz...",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(self.icon)
        if self.last_used_dir_napisy == '':
            dialog.set_current_folder(os.path.expandvars(self.domyslny_katalog))
        else:
            dialog.set_current_folder(os.path.expandvars(self.last_used_dir_napisy))
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_select_multiple(True)
        
        filter = gtk.FileFilter()
        filter.set_name("Wszystkie plik")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("Napisy")
        filter.add_pattern("*.txt")
        filter.add_pattern("*.sub")
        filter.add_pattern("*.srt")
        dialog.add_filter(filter)
        dialog.set_filter(filter)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.opcje["sciezka"][:] = []
            plik = dialog.get_filenames()
            self.last_used_dir_napisy = os.path.split(plik[0])[0]
            self.info_gkonap(plik, 'p')
            self.opcje["sciezka"] = plik
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
        
    def sciezka_k(self, widget):
        dialog = gtk.FileChooserDialog("Wybierz katalog...",
                               None,
                               gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(self.icon)
        if self.last_used_dir_napisy == '':
            dialog.set_current_folder(os.path.expandvars(self.domyslny_katalog))
        else:
            dialog.set_current_folder(os.path.expandvars(self.last_used_dir_napisy))
        dialog.set_property('skip-taskbar-hint', True)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            plik = [dialog.get_filename()]
            self.last_used_dir_napisy = plik[0]
            self.opcje["sciezka"][:] = []
            self.opcje["sciezka"] = plik
            self.info_gkonap(plik, 'k')
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
    
    def wykonaj_sciag_napisy(self, widget):
        konap.wyjscie_error[:] = []
        konap.wyjscie_ok[:] = []
        self.napisy_wy_er[:] = []
        self.napisy_wy_ok[:] = []
        self.napisy_wy_istn[:] = []
        
        sciezka = self.opcje["sciezka_wideo"]
        if len(sciezka) == 0:
            #pusta scieżka wyswietl komunikat
            self.dialog_error("Podaj ścieżką do pliku lub katalogu.")
        elif len(sciezka) == 1 and os.path.isdir(sciezka[0]):
            #scieżka to katalog
            self.sck_jeden_arg_kat(sciezka[0])
        else:
            #wiele sciezek lub jedna to plik/pliki
            self.napiprojekt(sciezka)
            self.wyjscie()
    
    def wykonaj(self, widget):
        self.rekur()
        self.format()
        self.fps_domyslne()
        self.nadpisz(widget)
        self.znacznik()
        self.rozs()
        self.znaczniki_XBMC()
        konap.wyjscie_error[:] = []
        konap.wyjscie_ok[:] = []
        self.napisy_wy_er[:] = []
        self.napisy_wy_ok[:] = []
        self.napisy_wy_istn[:] = []
        
        
        if self.opcje.has_key('sciezka') == True:
            for ele in self.opcje['sciezka']:
                try:
                    knpl = konap.pliki(ele, self.opcje["rekur"])
                    konap.edycja(knpl[0], knpl[1], self.opcje["format"], self.opcje["fps"])
                except:
                    self.dialog_error("Błąd krytyczny - konap konwersja. \n%s%s" % ("\n".join(konap.wyjscie_error), self.gkonap_error))
                    sys.exit(2)
                if os.path.isdir(ele) == False:
                    self.statusb_zm_info("Konwersja napisów %s" % os.path.split(ele)[1])
                else:
                    self.statusb_zm_info("Konwersja napsiów w katalogu %s" % os.path.split(ele)[1])
                while gtk.events_pending():
                    gtk.main_iteration()
            
            self.statusb_zm_info("Gotowy.")
            
            if len(self.opcje["sciezka"]) == 0:
                self.dialog_error("Podaj ścieżką do pliku lub katalogu.")
            else:
                self.wyjscie()
            
        else:
            self.dialog_error("Podaj ścieżką do pliku lub katalogu.")
        
    def dialog_ok(self, mes):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, mes)
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_icon_from_file(self.icon)
        res = dialog.run()
        if res == gtk.RESPONSE_OK:
            dialog.destroy()
        else:
            dialog.destroy()
    
    def dialog_info(self, mes):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, message_format=mes)
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_icon_from_file(self.icon)
        res = dialog.run()
        if res == gtk.RESPONSE_DELETE_EVENT:
            dialog.destroy()
        else:
            dialog.destroy()
    
    def dialog_yes_no(self, mes):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, mes)
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_property('use-markup', True)
        dialog.set_icon_from_file(self.icon)
        res = dialog.run()
        if res == gtk.RESPONSE_YES:
            dialog.destroy()
            return True
        elif res == gtk.RESPONSE_NO:
            dialog.destroy()
            return False
        else:
            dialog.destroy()
    
    def dialog_error(self, mes):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, mes)
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_icon_from_file(self.icon)
        res = dialog.run()
        if res == gtk.RESPONSE_OK:
            dialog.destroy()
        else:
            dialog.destroy()
    
    def dialog_nap_k_s(self):
        dialog=gtk.Dialog("Ściągnij lub ...")
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_icon_from_file(self.icon)
        child=dialog.get_children()[0]
        butt_box=child.get_children()[1]
        butt_box.set_layout(gtk.BUTTONBOX_CENTER)
        lab=gtk.Label("<big><b>Wybierz</b></big>:\nściągnąć napisy do filmu/filmów \nczy\ndodać pliki z napisami do konwersji.")
        lab.set_justify(gtk.JUSTIFY_CENTER)
        lab.set_property('use-markup', True)
        lab.show()
        dialog.add_button("Ściągnij", gtk.RESPONSE_YES)
        dialog.add_button("Konwersja", gtk.RESPONSE_NO)
        child.pack_start(lab)
        
        res = dialog.run()
        if res == gtk.RESPONSE_YES:
            dialog.destroy()
            return True
        elif res == gtk.RESPONSE_NO:
            dialog.destroy()
            return False
        else:
            dialog.destroy()
    
    def fps_domyslne(self):
        try:
            self.opcje["fps"] = locale.atof(self.cbxe_Fps.get_active_text())
            self.gkonap_error = ""
        except:
            self.gkonap_error = "\nPodano błędną wartość dla framerate'u.\nPodaj właściwą wartość."
            
            
    def rekur(self):
        if self.cbnt_Rekur.get_active() == True:
            re = True
            self.opcje["rekur"] = re
        else:
            re = False
            self.opcje["rekur"] = re
    
    def format(self):
        if self.cbx_Format.get_active() == 0:
            self.opcje["format"] = "mdvd"
        elif self.cbx_Format.get_active() == 1:
            self.opcje["format"] = "mpl"
        elif self.cbx_Format.get_active() == 2:
            self.opcje["format"] = "srt"
    
    def nadpisz(self, widget):
        konap.zapisz_op["nadpisz"] = self.cbnt_Nadpisz.get_active()
        if self.cbnt_Nadpisz.get_active()==True:
            self.cbnt_Znacznik.set_sensitive(False)
            self.en_Roz.set_sensitive(False)
        else:
            self.cbnt_Znacznik.set_sensitive(True)
            self.en_Roz.set_sensitive(True)
        
    def znacznik(self):
        konap.zapisz_op["znacznik"] = self.cbnt_Znacznik.get_active()
    
    def znaczniki_XBMC(self):
        konap.zapisz_op["znaczniki_XBMC"] = self.cbnt_XBMC.get_active()
      
    def rozs(self):
        if self.en_Roz.get_text() == '':
            konap.zapisz_op["roz"] = "None"
        else:
            konap.zapisz_op["roz"] = self.en_Roz.get_text()
            
#    Start:
#        -sprawdzamy czy mamy podaną jakąś ścieżkę dla programu -- tak dalej -- nie odpal normalnie
#        -sprawdzamy czy ścieżka to ścieżka do katalogu czy pliku
#        -- obsługa wielu plików
#        --plik
#            -sprawdzamy typ pliku
#            -jeżeli to napisy to dodajemy do gkonap jako plik to konwersji
#            -jeżeli to plik video sprawdzamy czy istnieją już napisy do tego pliku
#                -- napisy już istnieją -- komunikat pobrać jeszcze raz (nazwa pliku)? -- tak --pobierz napisy --nie --nic nic nie rób odpal normalnie
#                -- napisy nie istnieją -- komunikat pobrać napisy do filmu (nazwa pliku) -- tak -- pobierz napisy --nie nic nie rób odpal normalnie
#        --katalog
#            -sprawdzamy czy istnieją pliki wideo w katalogu 
#                -- tak -- sprawdź czy są już napisy do filmów -- tak nic nie rób -- nie ma do któryś plików -- komunikat pobrać napisy do pliku/ów (nazwa) -- tak pobierz -- nie odpal przekaż ścieżkę do konwersji
#                -- nie -- przekaż ścieżkę do konwersji
        
    def init_gkonap(self):
        if len(sys.argv) == 1:
            #sprawdz ilość argumentów dla programu jeżeli 1 to nie rób nic inaczej
            #sprawdzaj dalej zależności
            pass
        elif len(sys.argv) == 2:
            #tylko jeden argumnet sprawdzaj dalej
            self.sck_jeden_arg()
        elif len(sys.argv) > 2:
            #więcej niź jedna ścieżka do plików
            self.sck_wiele_arg()

    def napiprojekt(self, list):
        pobrane_napisy = []
        self.napisy_wy_ok[:] = []
        self.napisy_wy_er[:] = []
         
        def f(z):
            idx = [ 0xe, 0x3,  0x6, 0x8, 0x2 ]
            mul = [   2,   2,    5,   4,   3 ]
            add = [   0, 0xd, 0x10, 0xb, 0x5 ]
        
            b = []
            for i in xrange(len(idx)):
                a = add[i]
                m = mul[i]
                i = idx[i]
        
                t = a + int(z[i], 16)
                v = int(z[t:t+2], 16)
                b.append( ("%x" % (v*m))[-1] )

            return ''.join(b)
        
        def remove():
            path=os.getcwd() + "/napisy.7z"
            try:
                os.remove(path)
            except:
                pass
        
        for sciezka in list:
            d = md5.new()
            d.update(open(sciezka).read(10485760))
        
            str = "http://napiprojekt.pl/unit_napisy/dl.php?l=PL&f="+d.hexdigest()+"&t="+f(d.hexdigest())+"&v=other&kolejka=false&nick=&pass=&napios="+os.name
        
            open("napisy.7z","w").write(urllib.urlopen(str).read())
            nazwa=os.path.splitext(sciezka)[0]+'.txt_napi'
        
            if (os.system("/usr/bin/7z x -y -so -piBlm8NTigvru0Jr0 napisy.7z 2>/dev/null >\""+nazwa+"\"")):
                self.napisy_wy_er.append(os.path.split(sciezka)[1])
                os.remove(nazwa) 
                remove()       
            else:
                self.napisy_wy_ok.append(os.path.split(sciezka)[1])
                _nazwa = os.path.splitext(nazwa)[0] + '.txt'
                os.rename(nazwa, _nazwa)
                pobrane_napisy.append(_nazwa)
                remove()
            
            self.statusb_zm_info("Ściągam napisy do %s" % os.path.split(sciezka)[1])
            while gtk.events_pending():
                gtk.main_iteration()
        
        self.statusb_zm_info("Gotowy.")
        
        if len(pobrane_napisy) != 0:
            self.opcje["sciezka"] = pobrane_napisy
            self.info_gkonap(pobrane_napisy, 'p')
        else:
            pass
        
    def spr_napisy(self, sciezka):
        sciezka_napisy = os.path.splitext(sciezka)[0]
        sciezka_napisy_list = [sciezka_napisy+ele for ele in self.ext_napisy]
        sciezka_napisy_out = [ele for ele in sciezka_napisy_list if os.path.exists(ele)]
        return sciezka_napisy_out
    
    def sck_jeden_arg_kat(self, sciezka):
        ls_pliki_wideo=[]
        napisy = []
        self.napisy_wy_istn[:] = []
        
        dialog = self.dialog_yes_no("Wraz z podkatalogami?")
        
        if dialog == True:
            katalogi=[]
            #rekursywnie
            for root, dir, file in os.walk(sciezka):
                for name in file:
                    katalogi.append(os.path.join(root, name))
            katalogi=[os.path.join(sciezka, plik) for plik in katalogi if os.path.splitext(plik)[1] in self.ext_video]
            for ele in katalogi:
                napisy_lista=self.spr_napisy(ele)
                if len(napisy_lista) != 0:
                    #napisy są nic nie rób
                    self.napisy_wy_istn.append(os.path.split(ele)[1])
                    napisy.extend(napisy_lista)
                elif len(napisy_lista) == 0:
                    #brak napisów dodaj pliki do listy z do ściągnięcia
                    ls_pliki_wideo.append(ele)
                else:
                    pass 
                    
        elif dialog == False:
            #bez podkatalogów
            ls_katalog=os.listdir(sciezka)
            ls_katalog=[os.path.join(sciezka, plik) for plik in ls_katalog if os.path.splitext(plik)[1] in self.ext_video]
            for ele in ls_katalog:
                #sprawdzamy czy są napisy
                napisy_lista=self.spr_napisy(ele)
                if len(napisy_lista) != 0:
                    #napisy są nic nie rób
                    self.napisy_wy_istn.append(os.path.split(ele)[1])
                    napisy.extend(napisy_lista)
                elif len(napisy_lista) == 0:
                    #brak napisów dodaj pliki do listy z do ściągnięcia
                    ls_pliki_wideo.append(ele)
                else:
                    pass
        else:
            pass

        #ściągamy napisy
        if len(ls_pliki_wideo) != 0:
            self.napiprojekt(ls_pliki_wideo)
            self.wyjscie()
        else:
            self.wyjscie()
            self.opcje["sciezka"] = napisy
            self.info_gkonap(napisy, 'p')
            
    
    def sck_jeden_arg(self):
        sciezka = sys.argv[1]
        if os.path.isdir(sciezka) == True and os.path.exists(sciezka) == True:
            #katalog
            dialog = self.dialog_nap_k_s()
            if dialog == True:
                #ściągnij
                self.sck_jeden_arg_kat(sciezka)
            elif dialog == False:
                #konwerjsa
                self.opcje["sciezka"] = [sciezka]
                self.info_gkonap([sciezka], 'k')
            else:
                pass
            
        elif os.path.isdir(sciezka) == False and os.path.exists(sciezka) == True:
            #plik
            ext_plik = os.path.splitext(sciezka)[1]
            if ext_plik in self.ext_napisy:
                #plik to napisy
                self.opcje["sciezka"] = [sciezka]
                self.info_gkonap([sciezka], 'p')
            elif ext_plik in self.ext_video:
                #plik to video
                #sprawdz czy już istnieją napisy
                napisy_list = self.spr_napisy(sciezka)
                if len(napisy_list) != 0:
                    dialog = self.dialog_yes_no("Napisy istnieją dla:\n<b>%s</b>.\nPobrać jeszcze raz z serwisu napiprojekt?" % os.path.split(sciezka)[1])
                    if dialog == False:
                        #nie pobieraj napisów i przekaż scieżkę z napisami do porgramu
                        self.opcje["sciezka"] = napisy_list
                        self.info_gkonap(napisy_list, "p")
                    elif dialog == True:
                        time.sleep(2)
                        self.napiprojekt([sciezka])
                        self.wyjscie()
                        #pobierz napisy
                else:
                    dialog = self.dialog_yes_no("Pobrać napisy do filmu:\n<b>%s</b>\nz wykorzystaniem napiprojekt?" % os.path.split(sciezka)[1])
                    if dialog == True:
                        self.napiprojekt([sciezka])
                        self.wyjscie()
                    else:
                        pass
            else:
                self.dialog_error("Nie obsługiwany format pliku")
        else:
            self.dialog_error("Błędna ścieżka do pliku/katalogu")

    def sck_wiele_arg(self):
        arg = sys.argv[1:]
        self.napisy_wy_istn[:] = []
        wideo_pliki = []
        napisy =[]
        self.napisy_wy_istn[:] = []
        
        if os.path.isdir(arg[0]) == True:
            sciezka = arg[0]
            dialog = self.dialog_nap_k_s()
            if dialog == True:
                #ściągnij
                self.sck_jeden_arg_kat(sciezka)
            elif dialog == False:
                #konwerjsa
                self.opcje["sciezka"] = [sciezka]
                self.info_gkonap([sciezka], 'k')
            else:
                pass
        else:
            if os.path.splitext(arg[0])[1] in self.ext_napisy:
                #traktujemy jako napisy
                lista_napisy = [ele for ele in arg if os.path.splitext(ele)[1] in self.ext_napisy]
                self.opcje["sciezka"] = lista_napisy
                self.info_gkonap(lista_napisy, "p")
                            
            elif os.path.splitext(arg[0])[1] in self.ext_video:
                #traktujemy jako video
                lista_plikow_wideo = [ele for ele in arg if os.path.splitext(ele)[1] in self.ext_video]
                for ele in lista_plikow_wideo:
                    spr_napisy=self.spr_napisy(ele)
                    if len(spr_napisy) != 0:
                        #napisy istnieją
                        self.napisy_wy_istn.append(os.path.split(ele)[1])
                        napisy.extend(spr_napisy)
                    elif len(spr_napisy) == 0:
                        #nie ma napisów
                        wideo_pliki.append(ele)
                #ściągamy napisy
                if len(wideo_pliki) != 0:
                    self.napiprojekt(wideo_pliki)
                    self.wyjscie()
                else:
                    self.wyjscie()
                    self.opcje["sciezka"] = napisy
                    self.info_gkonap(napisy, 'p')
            else:
                pass
        
    def zapisz_opcje(self):
        opcje = {}
        opcje['sck_napisy'] = self.last_used_dir_napisy
        opcje['sck_wideo'] = self.last_used_dir_wideo
        opcje['format'] = self.cbx_Format.get_active()
        try:
            _activ = self.cbxe_Fps.get_active()
            if _activ in [0,1,2,3]:
                opcje['fps'] = _activ
            else:
                opcje['fps'] = 1
        except:
            opcje['fps'] = 1
        opcje['nadpisz'] = self.cbnt_Nadpisz.get_active()
        opcje['rekur'] = self.cbnt_Rekur.get_active()
        opcje['znacznik'] = self.cbnt_Znacznik.get_active()
        opcje['rozs'] = self.en_Roz.get_text()
        opcje['znaczniki_XBMC'] = self.cbnt_XBMC.get_active()
        
        opcje_ele = ['sck_napisy', 'sck_wideo',  'format', 'fps', 'nadpisz', 'rekur', 'znacznik', 'rozs', 'znaczniki_XBMC']
        
        
        if os.path.exists(os.path.expandvars(self.config_file)) == True:
            pass
        else:
            if os.path.isdir(os.path.split(os.path.expandvars(self.config_file))[0]) == False:
                os.makedirs(os.path.split(os.path.expandvars(self.config_file))[0])
            
        config_file = open(os.path.expandvars(self.config_file), 'w')
        for ele in opcje_ele:
            config_file.write("%s=%s\n" %(ele, str(opcje[ele])))
    
    def wczytaj_opcje(self):
        
        def str_bool(str):
            if str == "True":
                return True
            else:
                return False
            
        if os.path.exists(os.path.expandvars(self.config_file)) == False:
            #brak pliku z opcjami użyj domyślnych
            self.cbxe_Fps.set_active(1)
            self.cbx_Format.set_active(0)
            self.cbnt_Nadpisz.set_active(True)
        else:
            config_file =  open(os.path.expandvars(self.config_file), 'r').readlines()
            config_file = [re.sub('\n', '', ele) for ele in config_file ]
            config_file = [re.split('=', ele)[1] for ele in config_file]
            try:
                self.last_used_dir_napisy = config_file[0]
                self.last_used_dir_wideo = config_file[1]
                self.cbx_Format.set_active(int(config_file[2]))
                self.cbxe_Fps.set_active(int(config_file[3]))
                self.cbnt_Nadpisz.set_active(str_bool(config_file[4]))
                self.cbnt_Rekur.set_active(str_bool(config_file[5]))
                self.cbnt_Znacznik.set_active(str_bool(config_file[6]))
                self.en_Roz.set_text(config_file[7])
                self.cbnt_XBMC.set_active(str_bool(config_file[8]))
            except:
                self.last_used_dir_napisy = ''
                self.last_used_dir_wideo = ''
                self.cbx_Format.set_active(int(0))
                self.cbxe_Fps.set_active(int(1))
                self.cbnt_Nadpisz.set_active(True)
                self.cbnt_Rekur.set_active(False)
                self.cbnt_Znacznik.set_active(False)
                self.en_Roz.set_text('')
                self.cbnt_XBMC.set_active(False)
                            
    def quit(self, widget):
        gtk.main_quit()
        self.zapisz_opcje()    
    
    def main(self):
        gtk.main() 

#hadler dla linków http dla gtk.AboutDialog
def url_handler(dialog, link, data=None):
    webbrowser.open(link)

gtk.about_dialog_set_url_hook(url_handler)



if __name__ == "__main__":
    gkn = Gui()
    gkn.main()
