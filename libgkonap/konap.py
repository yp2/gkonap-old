#!/usr/bin/env python
#-*- coding: utf-8 -*-

#       konap.py
#       
#       Copyright 2008 Daniel Dereziński <daniel.derezinski@gmial.com>
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

#        Zasługi dla:
#        Konrad Kasiel  <konirad@o2.pl> - za poprawki dla konap. 

import kaa.metadata
import os
import os.path
import sys
import re
import commands
from optparse import OptionParser
import locale
import time
import datetime
import ctypes
import gkpath

__nazwa__ = 'konap'

wersja = gkpath.wersja
opis = u""

##Nazwa procesu
libc = ctypes.CDLL('libc.so.6')
libc.prctl(15, __nazwa__+'\0', 0, 0, 0)

_ext_napisy = ['.txt', '.sub', '.srt','.ass']
_u_ext_napisy = [ele.upper() for ele in _ext_napisy]
ext_napisy = _ext_napisy + _u_ext_napisy

_ext_video = ['.avi', '.3gp', '.asf', '.asx', '.divx', '.mkv', '.mov', '.mp4', '.mpeg', '.mpg', '.ogm', '.qt', '.rm', '.rmvb', '.wmv', '.xvid']
_u_ext_video = [ele.upper() for ele in _ext_video]
ext_video = _ext_video + _u_ext_video

#znak nowej lini
nlinia = '\n'

wyjscie_error = []
wyjscie_ok = []
zapisz_op={}

def pliki(sciezka, recursive):
    u"Zmienna scieżka przekształcany jest na liste zawierająca ścieżki to plików nadających się do edycji."
    try:    
        if os.path.exists(sciezka) == False:
            print u"Błędna ścieżka do pliku/katalogu"
            wyjscie_error.append(u"Błędna ścieżka do pliku/katalogu")
        else:
            #~ Tworzenie listy plików z napisamy w wypadku gdy scieżka to scieżka do pliku z napisami.
            #~ 
            if os.path.isdir(sciezka) == False:
                if os.path.splitext(sciezka)[1] in ext_napisy:
                    listaplikow = [sciezka]
                    #~ Tworzenie listy plików video w przypadku gdy ścieżka to ścieżka do pliku z napisami.
                    #~ 
                    _split = os.path.splitext(sciezka)
                    scka_fps = _split[0]
                    #to ma sens bo nie wiadomo jaki to plik media
                    lista_fps = [scka_fps+ele for ele in ext_video]
                    lista_fps = [ele for ele in lista_fps if os.path.exists(ele)]
                else:
                    print u"Nie obsługiwany format pliku"
                    wyjscie_error.append(u"Nie obsługiwany format pliku")
            else:
                #~ Tworzenie listy plików z napisami gdy ścieżka to scieżka do katalogu, w którym mogą znajdować się pliki z napisami
                #~ oraz brak sprawdzania podkatalogów.
                
                if recursive == False:
                    listaplikow = os.listdir(sciezka)
                    listaplikow = [os.path.join(sciezka, plik) for plik in listaplikow if os.path.splitext(plik)[1] in ext_napisy]
                    #~ Tworzenie listy plików video gdy ścieżka to scieżka do katalogu, w którym mogą znajdować się pliki z napisami
                    #~ oraz brak sprawdzania podkatalogów.
                    lista_fps = os.listdir(sciezka)
                    lista_fps = [os.path.join(sciezka, plik) for plik in lista_fps if os.path.splitext(plik)[1] in ext_video]
                    if len(listaplikow) == 0:
                        print u"Nie obsługiwany format pliku."
                        wyjscie_error.append(u"Nie obsługiwany format pliku.")
                else:
                    #~ Tworzenie listy plików z napisami gdy ścieżka to scieżka do katalogu, w którym mogą znajdować się pliki z napisami
                    #~ oraz ze sprawdzania podkatalogów.
                    lista_kat = []
                    for root, dir, file in os.walk(sciezka):
                        for name in file:
                            lista_kat.append(os.path.join(root, name))
                    listaplikow = [os.path.join(sciezka, plik) for plik in lista_kat if os.path.splitext(plik)[1] in ext_napisy]
                    #~ Tworzenie listy plików video gdy ścieżka to scieżka do katalogu, w którym mogą znajdować się pliki z napisami
                    #~ oraz ze sprawdzania podkatalogów.
                    lista_fps = [os.path.join(sciezka, plik) for plik in lista_kat if os.path.splitext(plik)[1] in ext_video]
                    if len(listaplikow) == 0:
                        print u"Nie obsługiwany format pliku."
                        wyjscie_error.append(u"Nie obsługiwany format pliku.")
    except:
        print u"Błąd"        
        
    
    def framerates(lista_fps):
        u"Toworzenie słownika w ilością fps dla poszczególnych plików video. Schemat: klucz - sciezka do pliku video bez rozszeżenia; wartość - fps"
        sl_framerates = {}                
        for n in range(len(lista_fps)):
            fps = kaa.metadata.parse(lista_fps[n])
            try:
                fps_liczba = fps.video[0].fps
                sl_framerates[os.path.splitext(lista_fps[n])[0]] = fps_liczba
            except:
                pass
                
        try:
            return sl_framerates
        except:
            pass
    
    try:
        
        return listaplikow, framerates(lista_fps)
    except:
        pass


def format_we(sck_plik_we):
    u"""Funkcja zwraca format pliku wejściowego:
    0 - MicroDVD ({000})
    1 - MPL2 ([000])
    2 - SubRip (pierwsz linia to zawsze - 1)
    3 - TMPlayer (00:00:00:)
    
    Bada pierwszą linię pliku i porównuje ze wzorcami
    """
    mdvd = re.compile(r'^\{\d*\}')
    mpl = re.compile(r'^\[\d*\]')
    srt = re.compile(r'^\d{1}$')
    tmpl = re.compile(r'^\d{1,2}:\d{2}:\d{2}:')
    
    formaty = [mdvd, mpl, srt, tmpl]
            
    linia = open(sck_plik_we, 'rU').readline()
    for f in range(len(formaty)):
        try:
            if formaty[f].search(linia) == None:
                pass
            else:
                format_plik_we=f
                print f
        except:
            print u'Nie obsługiwany format pliku napisów w pliku %s' % sck_plik_we
            wyjscie_error.append(u'Nie obsługiwany format pliku napisów w pliku %s' % sck_plik_we)
    try:
        return format_plik_we
    except:
        pass

def obrobka(linia_podzial, format_we_ko):    
    u"""Wstępna obróbka otrzymanego podziału. Usunięcie znaków nowych lini, dodanie odpowiednich dla 
    formatu znaków nowych lini""" 
    
    if format_we_ko==2:
        #czyszczenie SubRip
        for x in range(len(linia_podzial)):
            try:
                #~ usunięcie zbędnych znaków nowej lini oraz numeru lini z formatu SubRip
                if re.search('(\n{2}\d*\n)', linia_podzial[x])==None:
                    pass
                else:
                    linia_podzial[x] = re.split('(\n{2}\d*\n)', linia_podzial[x])[0]
            except:
                pass
                
            try:
                #~ zasąpienie znaku nowej linii znakiem '|'
                linia_podzial[x]= re.sub(r'\n', '|', linia_podzial[x])
            except:
                pass
    
    elif format_we_ko != 2:
        #obróbka dla innych formatów - usunięcie końcowego znaku \n dla zgodności z wynikie srt
        for x in range(len(linia_podzial)):
            try:
                linia_podzial[x]= re.sub(r'\n', '', linia_podzial[x])
            except:
                pass
    
    #~ wynikiem są 3 słowniki czas_start, czas_stop, napis_tekst. Klucz to kolejny numer lini(zaczynamy do 0)
    #~ wartość to odpowiednia wartość dla czas_start, czas_stop, napis_tekst. Najpierw towrzymy 3 słowniki
    if format_we_ko == 3:
        czas_start={}
        czas_stop={}
        napis_tekst={}
        # Dzielone przez 2 dla foramtu tmpl
        for x in range(int(len(linia_podzial)/2)):
            czas_start[x] = linia_podzial[0]
            napis_tekst[x] = linia_podzial[1]
            linia_podzial = linia_podzial[2:]
        for x in range(len(czas_start)):
            try:
                start = czas_start[x]
                stop = czas_start[x+1]
                _czas_start = re.split(":", start)
                _czas_start = _czas_start[:3]
                _czas_start = [int(ele) for ele in _czas_start]
                csh, csm, css = _czas_start
                tdstart = tdelta(csh, csm, css)
                
                _czas_stop = re.split(":", stop)
                _czas_stop = _czas_stop[:3]
                _czas_stop = [int(ele) for ele in _czas_stop]
                csth, cstm, csts = _czas_stop
                tdstop = tdelta(csth, cstm, csts)
                if tdstop - tdstart > 4:
                    td=datetime.timedelta(seconds=4).seconds
                    cz_stop=tdstart+td
                    sec=int(cz_stop)
                    min=sec/60
                    hur=min/60
                    sec = sec - min*60
                    min = min - hur*60
                    hur = hur
                    czas=[str(hur), str(min), str(sec)]
                    for z in range(len(czas)):
                        if len(czas[z]) == 1:
                            czas[z] = "0%s" % czas[z]
                        else:
                            pass
                    czas.append("")
                    czas_stop[x] = ':'.join(czas)
                else:
                    czas_stop[x] = czas_start[x+1]
            except:
                cz_tmpl = re.split(':', czas_start[x])
                cz_tmpl = cz_tmpl[:3]
                cz_tmpl = [int(ele) for ele in _czas_stop]
                csh, csm, css = cz_tmpl
                tdstart = tdelta(csh, csm, css)
                td = datetime.timedelta(seconds=4).seconds
                tdstop = tdstart + td
                sec=int(tdstop)
                min=sec/60
                hur=min/60
                sec = sec - min*60
                min = min - hur*60
                hur = hur
                czas=[str(hur), str(min), str(sec)]
                for z in range(len(czas)):
                    if len(czas[z]) == 1:
                        czas[z] = "0%s" % czas[z]
                    else:
                        pass
                czas.append("")
                czas_stop[x] = ':'.join(czas)
    
    elif format_we_ko != 3:
        czas_start={}
        czas_stop={}
        napis_tekst={}
        # Reszta dzielona przez 3
        for x in range(int(len(linia_podzial)/3)):
            
            czas_start[x] = linia_podzial[0]
            czas_stop[x] = linia_podzial[1]
            napis_tekst[x] = linia_podzial[2]            
            linia_podzial = linia_podzial[3:]
    
    # zamiana znaków kursywy na odczytywane przez xbmc
    if zapisz_op['znaczniki_XBMC'] == True:
        
        kursywa = re.compile(r'\{y:i\}|/', re.I)
        #wrażenie re dotyczy {y:i} oraz drugiego oznaczenia dla kursywy - /
        xbmc_kursywa = ['<i>', '</i>']
        bold = re.compile(r'\{y:b\}', re.I)
        xbmc_bold = ['<b>', '</b>']
        
        reszta = re.compile(r'\{.*\}', re.I)
        xbmc_reszta = ''
        
        for x in range(len(napis_tekst)):
            #rozbicie na poszczególne linie po znaku nowej lini
            tmp_line = re.split(r'\|', napis_tekst[x])
            
            for z in range(len(tmp_line)):
                #wyszukanie poszczególnych znaczników i zamiana ich na właściwe
                # dla XBMC
                if re.match(kursywa, tmp_line[z]):
                    #kursywa
                    tmp_line[z]=re.sub(kursywa, xbmc_kursywa[0], tmp_line[z])
                    tmp_line[z]=tmp_line[z] + xbmc_kursywa[1]
                
                if re.match(bold, tmp_line[z]):    
                    #bold
                    tmp_line[z]=re.sub(bold, xbmc_bold[0], tmp_line[z])
                    tmp_line[z]=tmp_line[z] + xbmc_bold[1]
                
                #usunięcie zbędnych tagów
                tmp_line[z]=re.sub(reszta, xbmc_reszta, tmp_line[z])
                    
                
            #połączenie linii tmp_line w linie z napis_tekst
            napis_tekst[x]= '|'.join(tmp_line)
        
    else:
        pass
    return czas_start, czas_stop, napis_tekst 

def tdelta(h,m,s):
    return datetime.timedelta(hours=h, minutes=m, seconds=s).seconds

def konwersja(sck_plik_we, wzor_podzial_lini, format_we_ko, fps_video, format_wy):
    u"""
    """
    #~ otwieramy plik i wczytujemy calość linii
    
    try:
        o_plik = open(sck_plik_we, 'rU').readlines()
    except:
        print u'Nie mogę otowrzyć pliku %s' % sck_plik_we
        wyjscie_error.append(u'Nie mogę otowrzyć pliku %s' % sck_plik_we)
    #~ łączymy otwarty plik w jeden ciąg znaków do późniejszej obróbki
    linia = [''.join(o_plik)]

    #~ dzielimi otrzymany ciąg zanaków danym wzorcem danym dla każdego formatu            
    linia_podzial = wzor_podzial_lini.split(linia[0])
    linia_podzial = linia_podzial[1:]
    
    czas_start = obrobka(linia_podzial, format_we_ko)[0]
    czas_stop = obrobka(linia_podzial, format_we_ko)[1]
    napis_tekst = obrobka(linia_podzial, format_we_ko)[2]
    
    
    c=Czas()
        
    if format_wy == 'mdvd':
        ###
        #
        #format wyjściowy mdvd
        #
        ###
        if format_we_ko == 1:
            #
            #format wejściwy mpl
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.mpl_mdvd(_czas_stop, fps_video)
                try:
                    _czas_start_1 = c.mpl_mdvd(czas_start[z+1], fps_video)
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy = str("{%d}{%d}%s" % (c.mpl_mdvd(_czas_start, fps_video), d_czas_stop, napis_tekst[z]+nlinia))
#------------------------------------------------------------------------------ 
                w_plik.write(linia_wy)
            w_plik.close()
        elif format_we_ko == 2:
            #
            #format wejsciowy srt
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.srt_mdvd(_czas_stop, fps_video)
                try:
                    _czas_start_1 = c.srt_mdvd(czas_start[z+1], fps_video)
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy = str("{%d}{%d}%s" % (c.srt_mdvd(_czas_start, fps_video), d_czas_stop, napis_tekst[z]+nlinia))
#------------------------------------------------------------------------------ 
                w_plik.write(linia_wy)
            w_plik.close()
        elif format_we_ko == 3:
            #
            #foramt wejsciowy tmpl
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.tmpl_mdvd(_czas_stop, fps_video)
                try:
                    _czas_start_1 = c.tmpl_mdvd(czas_start[z+1], fps_video)
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy = str("{%d}{%d}%s" % (c.tmpl_mdvd(_czas_start, fps_video), d_czas_stop, napis_tekst[z]+nlinia))
#------------------------------------------------------------------------------ 
                w_plik.write(linia_wy)
            w_plik.close()
            
            
    elif format_wy == 'mpl':
        ###        
        #
        #format wyjściowy mpl
        #        
        ###
        if format_we_ko == 0:
            #
            #format wejściowy mdvd
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.mdvd_mpl(_czas_stop, fps_video)
                try:
                    _czas_start_1 = c.mdvd_mpl(czas_start[z+1], fps_video)
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy = str("[%d][%d]%s" % (c.mdvd_mpl(_czas_start, fps_video), d_czas_stop, napis_tekst[z]+nlinia))
#------------------------------------------------------------------------------ 
                w_plik.write(linia_wy)
            w_plik.close()
        elif format_we_ko == 2:
            #
            #format wejściowy srt
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.srt_mpl(_czas_stop)
                try:
                    _czas_start_1 = c.srt_mpl(czas_start[z+1])
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy = str("[%d][%d]%s" % (c.srt_mpl(_czas_start), d_czas_stop, napis_tekst[z]+nlinia))
#------------------------------------------------------------------------------ 
                w_plik.write(linia_wy)
            w_plik.close()
        elif format_we_ko == 3:
            #
            #format wejściowy tmpl
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.tmpl_mpl(_czas_stop)
                try:
                    _czas_start_1 = c.tmpl_mpl(czas_start[z+1])
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy = str("[%d][%d]%s" % (c.tmpl_mpl(_czas_start), d_czas_stop, napis_tekst[z]+nlinia))
#------------------------------------------------------------------------------ 
                w_plik.write(linia_wy)
            w_plik.close()


    
    elif format_wy == 'srt':
        ###
        #
        #format wyjściowy srt
        #
        ###
        if format_we_ko == 0:
            #
            #format wejściowy mdvd
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.mdvd_srt(_czas_stop, fps_video)
                try:
                    _czas_start_1 = c.mdvd_srt(czas_start[z+1], fps_video)
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy_czas = str('%s:%s:%s,%s' % c.mdvd_srt(_czas_start, fps_video) + ' --> ' + '%s:%s:%s,%s' % d_czas_stop)
#------------------------------------------------------------------------------ 
                linia_wy_napis = re.sub(r'\|', nlinia, napis_tekst[z])
                w_plik.write(str(int(z)+1)+nlinia)
                w_plik.write(linia_wy_czas+nlinia)
                w_plik.write(linia_wy_napis+nlinia)
                w_plik.write(nlinia)
            w_plik.close()
        elif format_we_ko == 1:
            #
            #format wejściowy mpl2
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                _cz_stop = c.mpl_srt(_czas_stop)
                try:
                    _czas_start_1 = c.mpl_srt(czas_start[z+1])
                except:
                    _czas_start_1 = False
                
                d_czas_stop = por_czas(_cz_stop, _czas_start_1, format_wy)
                
                linia_wy_czas = str('%s:%s:%s,%s' % c.mpl_srt(_czas_start) + ' --> ' + '%s:%s:%s,%s' % d_czas_stop)
#------------------------------------------------------------------------------ 
                linia_wy_napis = re.sub(r'\|', nlinia, napis_tekst[z])
                w_plik.write(str(int(z)+1)+nlinia)
                w_plik.write(linia_wy_czas+nlinia)
                w_plik.write(linia_wy_napis+nlinia)
                w_plik.write(nlinia)
            w_plik.close()
        elif format_we_ko == 3:
            #
            #format wejściowy tmpl
            #
            w_plik=open(zapisz(sck_plik_we, zapisz_op, format_wy), 'w')
            for z in range(len(czas_start)):
#------------------------------------------------------------------------------ 
                czas_napraw = naprawa(czas_start, czas_stop, z, format_we_ko)
                _czas_start = czas_napraw[0]
                _czas_stop = czas_napraw[1]
                
                #tu czasy się nie nakładają 
                d_czas_stop = c.tmpl_srt(_czas_stop)
                                                
                linia_wy_czas = str(c.tmpl_srt(_czas_start) + ',000 --> ' + d_czas_stop + ',000')
#------------------------------------------------------------------------------ 
                linia_wy_napis = re.sub(r'\|', nlinia, napis_tekst[z])
                w_plik.write(str(int(z)+1)+nlinia)
                w_plik.write(linia_wy_czas+nlinia)
                w_plik.write(linia_wy_napis+nlinia)
                w_plik.write(nlinia)
            w_plik.close()

def por_czas(czas_stop, czas_start_1, format_wyjsciowy):
    """Funkcja porównóje czasy stop i start + 1 krok po konwersji, tak aby nie zachodziły na siebie."""
        
        
    if format_wyjsciowy == 'mdvd':
        if czas_start_1 == False:
            _cz_stop = czas_stop
            return _cz_stop
        else:
            if czas_stop > czas_start_1:
                _cz_stop = czas_start_1
                return _cz_stop
            else:
                _cz_stop = czas_stop
                return _cz_stop
        
    
    if format_wyjsciowy == 'mpl':
        if czas_start_1 == False:
            _cz_stop = czas_stop
            return _cz_stop
        else:
            if czas_stop > czas_start_1:
                _cz_stop = czas_start_1
                return _cz_stop
            else:
                _cz_stop = czas_stop
                return _cz_stop
    
    if format_wyjsciowy == 'srt':
        if czas_start_1 == False:
            _cz_stop = czas_stop
            return _cz_stop
        else:
            g_cz_stop = int(czas_stop[0])
            m_cz_stop = int(czas_stop[1])
            s_cz_stop = int(czas_stop[2])
            tm_cz_stop = int(czas_stop[3])*1000
            
            g_cz_start_1 = int(czas_start_1[0])
            m_cz_start_1 = int(czas_start_1[1])
            s_cz_start_1 = int(czas_start_1[2])
            tm_cz_start_1 = int(czas_start_1[3])*1000
            
            tdelta_czas_stop = datetime.timedelta(hours=g_cz_stop, minutes=m_cz_stop, seconds=s_cz_stop, microseconds=tm_cz_stop)
            tdelta_czas_start_1 = datetime.timedelta(hours=g_cz_start_1, minutes=m_cz_start_1, seconds=s_cz_start_1, microseconds=tm_cz_start_1)
            
            if tdelta_czas_stop > tdelta_czas_start_1:
                _cz_stop = czas_start_1
                return _cz_stop
            else:
                _cz_stop = czas_stop
                return _cz_stop
        
def naprawa(cz_start, cz_stop, krok, format_wejscowy):
    """Funckja naprawiająca błędy związane z brakiem niektórych czasów. Dla róznych formatów.
    Funkcja zwraca dane czasy dla danego kroku.
    cz_start - czas start (cała lista)
    cz_stop - czas stop (cała lista)
    krok - krok iteracji z petli for
    format_wejsciowy - format z jakiego przeporwadzana jest konwersja:
    0 - MicroDVD
    1 - MPL2 
    2 - SubRip 
    3 - TMPlayer;
    Funkcja nie działa dla formatu wejsciowego srt oraz tmpl.  
    """
    #FIXME: Funkcja nie działa poprawnie dla srt i prawdopodbnie dla tmpl (nie testowane)
    # poprwić należało by dla formatu srt tworzenie słowników czasów teraz
    # program pomija całkowicie te linie które mają uszkodzone znaczniki czasu
    # pisanie tego dla tmpl mija się z celem. 
    
    ilosc_znakow_czas = {0:3,
                         1:3,
                         2:12,
                         3:8}
    wartosc_zero = {0:"{0}",
                    1:"[0]",
                    2:"00:00:00,000",
                    3:"00:00:00:"}
    #dodajemy do końcowego czasu ostarniego napisu 10 sekund
    wartosc_ostatnia = {0:240,
                       1:100,
                       2:10,
                       3:10}

    if len(cz_start[krok]) < ilosc_znakow_czas[format_wejscowy]:
        try:
            cz_start_popr = cz_stop[krok-1]
        except:
            #prawdopodbnie jest to pierwszy napis więc dajemy wartość 0
            #TODO: zaawansowana zmiana czasów co ja mam tu na myśli :)
            cz_start_popr = wartosc_zero[format_wejscowy]
    else:
        cz_start_popr = cz_start[krok]
    
    if len(cz_stop[krok]) < ilosc_znakow_czas[format_wejscowy]:
        try:            
            cz_stop_popr = cz_start[krok+1]
        except:
            #bład poza skalą prawdopodbnie ostatni napis
            if format_wejscowy == 0:
                tmp = re.search(r'{(\d*)}', cz_start[krok]).groups()[0]
                _tmp = str(int(tmp) + wartosc_ostatnia[format_wejscowy])
                cz_stop_popr =  '{%s}' % _tmp
            elif format_wejscowy == 1:
                tmp = re.search(r'\[(\d*)\]', cz_start[krok]).groups()[0]
                _tmp = str(int(tmp) + wartosc_ostatnia[format_wejscowy])
                cz_stop_popr =  '[%s]' % _tmp
            
#            elif format_wejscowy == 2:
#                godziny = re.findall(r'(\d{2}):', cz_start[krok])[0]
#                minuty = re.findall(r'(\d{2}):', cz_start[krok])[1]
#                sekundy = str(int(re.findall(r':(\d{2}),', cz_start[krok]).groups()[0]) + wartosc_ostatnia[format_wejscowy])
#                tysieczne = re.findall(r',(\d{3})', cz_start[krok])[0]
#                wynik = czas_prze(godziny, minuty, sekundy)
#                cz_stop_popr = '%s:%s:%s,%s' % (wynik[0], wynik[1], wynik[2], tysieczne)
                
#            elif format_wejscowy == 3:
#                czas_split = re.findall(r'(\d{1,2})', cz_start[krok])
#                godziny = czas_split[0]
#                minuty = czas_split[1] 
#                sekundy = str(int(czas_split[-1]) + wartosc_ostatnia[format_wejscowy])
#                             
#                cz_stop_popr = '%s:%s:%s:' % (czas_prze(godziny, minuty, sekundy))
    else:
        cz_stop_popr = cz_stop[krok]
    
    return cz_start_popr, cz_stop_popr

def czas_prze(godz, minu, sek):
    """Funkcja sprawdza czy po dodaniu czasu do sekund nie przeskoczyły minuty i godziny."""
    if int(sek) > 60:
        n_min = int(minu) + 1
    else:
        n_min = int(minu)
    
    if n_min > 60:
        n_godz = int(godz) + 1
    else:
        n_godz = int(godz)
    
    return tuple(str(n_godz), str(n_min), str(sek))
        
    
def zapisz(sck_plik_we, zapisz_op, format_wy): 

    format = {"mdvd" : "MicroDVD",
              "mpl" : "MPL2",
              "srt" : "SubRIP"}

    nazwa_pliku = os.path.splitext(sck_plik_we)
    
    if zapisz_op["nadpisz"] == True:
        w_plik = sck_plik_we
        return zmiana_roz(sck_plik_we, w_plik, format_wy, True)
    else:
        if zapisz_op["znacznik"] == False and zapisz_op["roz"] == "None":
            w_plik = "%s w formacie %s%s" % (nazwa_pliku[0], format[format_wy], nazwa_pliku[1])
            return zmiana_roz(sck_plik_we, w_plik, format_wy)
        if zapisz_op["znacznik"] == False and zapisz_op["roz"] != "None":
            roz = ".%s" % zapisz_op["roz"]
            w_plik = "%s w formacie %s%s" % (nazwa_pliku[0], format[format_wy], roz)
            return w_plik
        if zapisz_op["znacznik"] == True and zapisz_op["roz"] == "None":
            w_plik = sck_plik_we
            return zmiana_roz(sck_plik_we, w_plik, format_wy)
        if zapisz_op["znacznik"] == True and zapisz_op["roz"] != "None":
            n_pliku = nazwa_pliku[0]+".%s" % zapisz_op["roz"]
            w_plik = n_pliku
            return w_plik

def zmiana_roz(plik_org, plik_mod, format_wy, kasuj=False):
    "Funkcja zmienia rozszeżenie pliku na właściwy dla danego formatu na podstawie słowinika"
    
    format_roz = {"mdvd" : ".txt",
                    "mpl" : ".txt",
                    "srt" : ".srt"}

    w_plik = os.path.splitext(plik_mod)[0] + format_roz[format_wy]
    #kasuje tylko wtedy gdy nadpisujemy plik 
    if kasuj == True:
        kasowanie_pliku_roz(plik_org, w_plik)
    return w_plik
    
def kasowanie_pliku_roz(plik_1, plik_2):
    """Funkcja porównuje rozszeżenia dwu plików. Jeżeli plik_1 (plik orginalny)
    mam inne rozszeżenie niź plik_2 (plik wyjściowy konwersji) funkcja skasuje 
    stary plik pozostaiwając tylko nowy"""
#TODO: zmiana ścieżek dla plików podannych konwersji dla gkonap tak aby program przejmował nową ścieżkę

    if os.path.splitext(plik_1)[1] != os.path.splitext(plik_2)[1]:
        os.remove(plik_1)
    
class Czas:
    
    def mpl_mdvd(self, czas_ko, fps_video):
        u"mpl na mdvd"
        wz_czas = re.compile(r'(\d+)')
        czas_we = float(int(wz_czas.search(czas_ko).groups()[0]))/10
        czas_wy = int(float(czas_we)*float(fps_video))
        return czas_wy
    
    def srt_mdvd(self, czas_ko, fps_video):
        u"srt na mdvd"
        czas_we = float(re.split(":", re.split(',', czas_ko)[0])[0])*3600 + float(re.split(":", re.split(',', czas_ko)[0])[1])*60 + float(re.split(":", re.split(',', czas_ko)[0])[2]) + float(re.split(":", re.split(',', czas_ko)[1])[0])/1000
        czas_wy = int(float(czas_we)*float(fps_video))
        return czas_wy
        
    def tmpl_mdvd(self, czas_ko, fps_video):
        u"tmpl na mdvd"
        czas_we = int(re.split(':', czas_ko)[0])*3600 + int(re.split(':', czas_ko)[1])*60 + int(re.split(':', czas_ko)[2])
        czas_wy = int(float(czas_we)*float(fps_video))
        return czas_wy

    def mdvd_mpl(self, czas_ko, fps_video):
        u"mdvd na mpl"
        wz_czas = re.compile(r'(\d+)')    
        czas_we = float(wz_czas.search(czas_ko).groups()[0])
        czas_wy = float(czas_we)/float(fps_video)
        return int(float(czas_wy)*10)
    
    def srt_mpl(self, czas_ko):
        u"srt na mpl"
        czas_we = float(re.split(":", re.split(',', czas_ko)[0])[0])*3600 + float(re.split(":", re.split(',', czas_ko)[0])[1])*60 + float(re.split(":", re.split(',', czas_ko)[0])[2]) + float(re.split(":", re.split(',', czas_ko)[1])[0])/1000
        czas_wy = int(float(czas_we)*10)
        return czas_wy
    
    def tmpl_mpl(self, czas_ko):
        u"tmpl na mpl"
        czas_we = int(re.split(':', czas_ko)[0])*3600 + int(re.split(':', czas_ko)[1])*60 + int(re.split(':', czas_ko)[2])
        czas_wy = int(czas_we)*10
        return czas_wy
    
    def mdvd_srt(self, czas_ko, fps_video):
        u"mdvd na srt"
        wz_czas = re.compile(r'(\d+)')
        _sec_tys = re.split(r'\.', str(float(wz_czas.search(czas_ko).groups()[0])/float(fps_video)))
        sec = int(_sec_tys[0])
        tys_sec = _sec_tys[1]        

        if len(tys_sec) > 3:
            tys_sec = tys_sec[:3]
        elif len(tys_sec) == 2:
            tys_sec = '%s0' % tys_sec
        elif len(tys_sec) == 1:
            tys_sec = '%s00' % tys_sec
        elif len(tys_sec) == 0:
            tys_sec = '000'
                    
        min = int(sec/60)
        god = int(min/60)
        
        sec = sec - min*60
        min = min - god*60
        god = god    
        
        czas_wy = [str(god), str(min), str(sec)]
        
        for i in range(len(czas_wy)):
            if len(czas_wy[i]) == 1:
                czas_wy[i] = '0%s' % (czas_wy[i])
        
        #tutaj nic nie dodawać!!!!
        #tak ma być
        
        czas_wy.append(tys_sec)
        
        return tuple(czas_wy)    

    def mpl_srt(self, czas_ko):
        u"mpl na srt"
        wz_czas = re.compile(r'(\d+)')
        _sec_tys = re.split(r'\.' ,str(float(wz_czas.search(czas_ko).groups()[0])/10))
        sec = int(_sec_tys[0])        
        tys_sec = _sec_tys[1]
        
        if len(tys_sec) > 3:
            tys_sec = tys_sec[:3]
        elif len(tys_sec) == 2:
            tys_sec = '%s0' % tys_sec
        elif len(tys_sec) == 1:
            tys_sec = '%s00' % tys_sec
        elif len(tys_sec) == 0:
            tys_sec = '000'
            
        
        min = int(sec/60)
        god = int(min/60)
        
        sec = sec - min*60
        min = min - god*60
        god = god    
        
        czas_wy = [str(god), str(min), str(sec)]
        for i in range(len(czas_wy)):
            if len(czas_wy[i]) == 1:
                czas_wy[i] = '0%s' % (czas_wy[i])
        
        czas_wy.append(tys_sec)
        
        return tuple(czas_wy)
    
    def tmpl_srt(self, czas_ko):
        u"tmpl na srt"
        czas_wy = czas_ko[:8] 
        
        return czas_wy
        
def slow_fps(sl_framerates, plik_we, fps_domyslne):
    
    def error():
        print u"Brak framerate'u dla pliku %s uzywam domyślnego %.2f klatki na sekundę" % (plik_we, fps_domyslne)
        wyjscie_error.append(u"Brak framerate'u dla pliku %s uzywam domyślnego %.2f klatki na sekundę\n" % (plik_we, fps_domyslne))
        dom_fps = fps_domyslne
        return dom_fps

    if sl_framerates.has_key(os.path.splitext(plik_we)[0]) and sl_framerates[os.path.splitext(plik_we)[0]] != None:
            return sl_framerates[os.path.splitext(plik_we)[0]]
    else:
        return error()
        

def edycja(listaplikow, sl_framerates, format, fps_domyslne):
    u"edycja"
    wzor_podzial_lini_mdvd = re.compile(r'(\{\d*\})(\{\d*\})')
    wzor_podzial_lini_mpl = re.compile(r'(\[\d*\])(\[\d*\])')
    wzor_podzial_lini_srt = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n')
    wzor_podzial_lini_tmpl = re.compile(r'(\d{1,2}:\d{2}:\d{2}:)')
    
    for plik_we in listaplikow:
        
        if format == 'mdvd':
            if format_we(plik_we)==0:
                print u'Format napisów już w postaci MicroDVD - %s' % plik_we
                wyjscie_error.append(u'Format napisów już w postaci MicroDVD %s\n' % plik_we)
            else:
                wyjscie_ok.append(plik_we)
                print "Zakończono konwersję pliku %s na format %s" % (plik_we, format)
                if format_we(plik_we)==1:
                    #MPL2
                    konwersja(plik_we, wzor_podzial_lini_mpl, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
                
                elif format_we(plik_we)==2:
                    #SubRIP
                    konwersja(plik_we, wzor_podzial_lini_srt, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
                    
                elif format_we(plik_we)==3:
                    #TMplayer
                    konwersja(plik_we, wzor_podzial_lini_tmpl, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)

        elif format == 'mpl':
            if format_we(plik_we)==1:
                print u'Format napisów już w postaci MPL2 - %s' % plik_we
                wyjscie_error.append(u'Format napisów już w postaci MPL2 %s\n' % plik_we)
            else:
                wyjscie_ok.append(plik_we)
                print "Zakończono konwersję pliku %s na format %s" % (plik_we, format)
                if format_we(plik_we)==0:
                    #MicroDVD
                    konwersja(plik_we, wzor_podzial_lini_mdvd, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
                
                elif format_we(plik_we)==2:
                    #SubRIP
                    konwersja(plik_we, wzor_podzial_lini_srt, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
                    
                elif format_we(plik_we)==3:
                    #TMplayer
                    konwersja(plik_we, wzor_podzial_lini_tmpl, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
        
        elif format == 'srt':
            if format_we(plik_we)==2:
                print u'Format napisów już w postaci SubRIP - %s' % plik_we
                wyjscie_error.append(u'Format napisów już w postaci SubRIP %s\n' % plik_we)
            else:
                wyjscie_ok.append(plik_we)
                print "Zakończono konwersję pliku %s na format %s" % (plik_we, format)
                if format_we(plik_we)==0:
                    #MicroDVD
                    konwersja(plik_we, wzor_podzial_lini_mdvd, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
                
                elif format_we(plik_we)==1:
                    #MPL2
                    konwersja(plik_we, wzor_podzial_lini_mpl, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)
                    
                elif format_we(plik_we)==3:
                    #TMplayer
                    konwersja(plik_we, wzor_podzial_lini_tmpl, format_we(plik_we), slow_fps(sl_framerates, plik_we, fps_domyslne), format)

            
def main():
    u""
    
    #~ Pobieramy arbumenty oraz opcje z lini komend. Użycie optparse. Opcje - options, argumenty -args
    
    parser = OptionParser(usage=u"%prog [opcje] [siceżka_do_katalogu]"+opis, version=u"%prog "+wersja)
    
    parser.add_option("-R", u"--recursive", action="store_true", dest="recursive", default=False, help=u"uwzględnij pliki w podkatalogach")
    
    parser.add_option("-f", u"--format", action="store", dest="format", default="mdvd", choices=['mdvd', 'srt', 'mpl','ass'], help=u"wyjściowy format napisów: MicroDVD - mdvd (domyślny), MPL2 - mpl, SubRip - srt. Np. -f srt (aby uzyskać plik napisów w foramcie SubRip).")
    
    parser.add_option("-F", u"--framerate", action="store", dest="framerate", default="24", type="string", help=u"domyślna ilość klatek na sekundę elementów dla, których nie udało się rozpoznać framerate'u. Domyślnie - 24 klataki/sekundę")
    
    parser.add_option("-n", u"--nadpisz", action="store_true", dest="nadpisz", default=False, help=u"nadpisuje element wejściowy wynikiem pracy programu. Nie aktywne stają się opcje -z(znacznik), -r(rozszeżenie).")
    
    parser.add_option("-z", u"--znacznik", action="store_true", dest="znacznik", default=False, help=u"brak dopisywania do pliku znacznika [foo - w formacie xxxx] do nazwy pliku.")
    
    parser.add_option("-r", u"--rozszeżenie", action="store", dest="roz", help=u"określa rozszeżenie dla pliku (bez kropki) będącego wynikiem pracy programu. Jeżeli żadne rozszeżenie nie zostanie sprecyzowane, użytę zostanie rozszeżenie z pliku wejściowego.")
    
    parser.add_option("-x", u"--xbmc", action="store_true", dest="xbmc", default=False, help=u"zmienia znaki formatowania wyświetlanych napisów na znaki formatowania zgodne z XBMC.")
 
    
    (options, args) = parser.parse_args()
    
    # Sprawdzamy czy argumentem dla porgramu jest pojedynczy katalog.
    # Jeżeli nie zmiennej sciezka przypisany zostaje args
    
    loc = os.path.expandvars("$LANG")
    locale.setlocale(locale.LC_ALL, loc)
    
    recursive = options.recursive
    format = str(options.format)
    fps_domyslne = locale.atof(options.framerate)
    nadpisz = options.nadpisz
    znacznik = options.znacznik
    roz = str(options.roz)
    xbmc= options.xbmc
    
    zapisz_op["nadpisz"] = nadpisz
    zapisz_op["znacznik"] = znacznik
    zapisz_op["roz"] = roz
    zapisz_op["znaczniki_XBMC"] = xbmc
    
    if len(args) == 1:
        pass
        #sciezka = args
    elif len(args) == 0:
        parser.error(u"Program wymaga sciezki do pliku/katalogu.")
    else:
        parser.error(u"Program wymaga tylko jednej sciezki do pliku/katalogu")
    
    pliki_def = pliki(args[0], recursive)

    try:
        edycja(pliki_def[0], pliki_def[1], format, fps_domyslne)
    except:
        print 'Błąd główna pętla'
        
if __name__ == '__main__':
    main()
