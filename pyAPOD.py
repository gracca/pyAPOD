#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#-----------------------------------------------------------------------#
# pyAPOD.py                                                             #
#                                                                       #
# Copyright (C) 2013 Germán A. Racca - <gracca[AT]gmail[DOT]com>        #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#-----------------------------------------------------------------------#

__author__ = "Germán A. Racca"
__copyright__ = "Copyright (C) 2013, Germán A. Racca"
__email__ = "gracca@gmail.com"
__license__ = "GPLv3+"
__version__ = "0.1"
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
RESET = '\033[0m'


import os
import urllib2
import datetime
import ConfigParser

from BeautifulSoup import BeautifulSoup
from gi.repository import Gtk, GdkPixbuf


#############
## C L A S S
#######################
class APOD(Gtk.Window):
    """Gtk+ 3 interface for pyAPOD"""

    def __init__(self):
        """Initialize the window"""
        Gtk.Window.__init__(self, title='Astronomy Picture of the Day')
        self.set_default_size(400, 450)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)

        # create a grid
        #---------------
        self.grid = Gtk.Grid(column_homogeneous=True,
                             column_spacing=10,
                             row_spacing=10)
        self.add(self.grid)

        # create a window with scroll bars
        #----------------------------------
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER,
                                       Gtk.PolicyType.AUTOMATIC)
        self.grid.add(self.scrolledwindow)

        # read settings from config file
        #--------------------------------
        apod_settings = SettingsAPOD()
        days_numb, icon_size = apod_settings.get_settings()
        print "[ " + BLUE + "settings" + RESET + " ]" + \
              " icon size =", icon_size
        print "[ " + BLUE + "settings" + RESET + " ]" + \
              " number of days =", days_numb

        # get cache directory to store images
        #-------------------------------------
        cache_dir = self.get_cache_dir()

        # get apod data for last 'days_numb' days
        #-----------------------------------------
        apod_data = self.get_apod_data(days_numb)

        # create a list store: icon, title, date, picture
        #-------------------------------------------------
        self.get_liststore(apod_data, cache_dir, icon_size)

        # create the tree view
        #----------------------
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_hexpand(True)
        self.treeview.set_vexpand(True)
        self.treeview.set_headers_visible(False)
        self.treeview.set_tooltip_column(2)

        # create the columns for the tree view
        #--------------------------------------
        renderer_pixbuf = Gtk.CellRendererPixbuf()  # column for icon
        renderer_pixbuf.set_padding(3, 6)
        column_pixbuf = Gtk.TreeViewColumn('', renderer_pixbuf, pixbuf=0)
        column_pixbuf.set_alignment(0.5)
        self.treeview.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText(weight=600)  # column for title
        renderer_text.set_fixed_size(200, -1)
        renderer_text.set_padding(3, 6)
        column_text = Gtk.TreeViewColumn('', renderer_text, text=1)
        column_text.set_alignment(0.5)
        self.treeview.append_column(column_text)

        self.scrolledwindow.add_with_viewport(self.treeview)

        # create the buttons
        #--------------------
        self.buttonbox = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        self.buttonbox.set_layout(Gtk.ButtonBoxStyle.END)

        self.button_about = Gtk.Button(stock=Gtk.STOCK_ABOUT)
        self.button_about.connect('clicked', self.on_button_about_clicked)
        self.buttonbox.add(self.button_about)
        self.buttonbox.set_child_secondary(self.button_about,
                                           is_secondary=True)

        self.button_prefs = Gtk.Button(stock=Gtk.STOCK_PREFERENCES)
        self.button_prefs.connect('clicked', self.on_button_prefs_clicked)
        self.buttonbox.add(self.button_prefs)
        self.buttonbox.set_child_secondary(self.button_prefs,
                                           is_secondary=True)

        self.button_open = Gtk.Button(stock=Gtk.STOCK_OPEN)
        self.button_open.connect('clicked', self.on_button_open_clicked,
                                 cache_dir)
        self.buttonbox.add(self.button_open)

        self.grid.attach(self.buttonbox, 0, 1, 1, 1)

    # functions to fetch APOD data
    #------------------------------
    def get_apod_data(self, num):
        """List of APOD data for a number of dates"""
        date = datetime.date.today()
        apod_data = []
        i = 0
        while i < num:
            apod_list = self.get_apod_list(date)  # get data for that date
            if apod_list is not False:
                apod_data.append(apod_list)
                i = i + 1
                date = date - datetime.timedelta(days=1)
            else:
                date = date - datetime.timedelta(days=1)  # try the day before
        return apod_data

    def get_apod_list(self, date):
        """Fetch APOD data for a given date"""
        icon = "calendar/S_" + date.strftime('%y%m%d') + ".jpg"
        page = "ap" + date.strftime('%y%m%d') + ".html"
        base_url = "http://apod.nasa.gov/apod/"
        apod_url = base_url + page

        # fetch the web page
        try:
            apod_htm = urllib2.urlopen(apod_url).read()
        except urllib2.HTTPError:
            return False

        # get the soup and tags
        soup = BeautifulSoup(apod_htm)
        tag_a = soup.findAll('a')
        tag_b = soup.findAll('b')
        tag_p = soup.findAll('p')

        # extract title and picture
        apod_tit = tag_b[0].string.strip()
        apod_pic = tag_a[1]['href']
        apod_inf = str(tag_p[2])
        apod_img = base_url + apod_pic
        apod_ico = base_url + icon

        # fromat date
        apod_dat = date.strftime('%Y %h %d')

        return [apod_dat, apod_img, apod_ico, apod_tit, apod_inf]

    # function to get cache directory
    #---------------------------------
    def get_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        home = os.environ.get('HOME')
        cache = os.path.join('.cache', 'pyAPOD')
        if os.path.isdir(os.path.join(home, cache)):
            return os.path.join(home, cache)
        else:
            os.makedirs(os.path.join(home, cache))
            return os.path.join(home, cache)

    # function to create a liststore
    #--------------------------------
    def get_liststore(self, apod_data, cache_dir, icon_size):
        """Create the liststore: icon, title, date, picture"""
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, str)
        for item in apod_data:
            dat = item[0]
            img = item[1]
            ico = item[2]
            tit = item[3]
            inf = item[4]
            ico_name = ico.split('/')[-1]
            tmp_name = os.path.join(cache_dir, ico_name)
            # see if icon is already downloaded
            if os.path.isfile(tmp_name):
                print "[ " + GREEN + "found icon" + RESET + " ]", tmp_name
                pass
            else:
                icon = urllib2.urlopen(ico).read()
                open(tmp_name, 'wb').write(icon)
            pxbf = GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp_name,
                                                           icon_size,
                                                           icon_size,
                                                           True)
            self.liststore.append([pxbf, tit, dat, img, inf])

    # callback for button Open
    #--------------------------
    def on_button_open_clicked(self, widget, cache_dir):
        """Download and show selected picture"""
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()

        if treeiter is not None:
            tit, dat, img, inf = model[treeiter][1:]
            img_name = img.split('/')[-1]
            tmp_name = os.path.join(cache_dir, img_name)

            # see if image is already downloaded
            if os.path.isfile(tmp_name):
                print "[ " + GREEN + "found image" + RESET + " ]", tmp_name
                picture = ViewAPOD(tit, dat, img_name, tmp_name, inf)
            else:
                try:  # if not, download it
                    pic = urllib2.urlopen(img).read()
                    open(tmp_name, 'wb').write(pic)
                    picture = ViewAPOD(tit, dat, img_name, tmp_name, inf)
                except urllib2.HTTPError:  # if error, show error dialog
                    error = self.show_error_dialog(dat)

    # callback for error dialog
    #---------------------------
    def show_error_dialog(self, dat):
        """Show error dialog"""
        msg1 = "There is no APOD image for " + dat + "."
        date = datetime.datetime.strptime(dat, '%Y %b %d').strftime('%y%m%d')
        page = "http://apod.nasa.gov/apod/ap" + date + ".html"
        msg2 = ("Please see <a href='" + page + "'>" + page +
               "</a> for more information.")
        error_dialog = Gtk.MessageDialog(self,
                                         0,
                                         Gtk.MessageType.ERROR,
                                         Gtk.ButtonsType.CLOSE,
                                         msg1)
        error_dialog.format_secondary_markup(msg2)
        error_dialog.run()
        error_dialog.destroy()

    # callback for button Prefs
    #---------------------------
    def on_button_prefs_clicked(self, widget):
        """Show preferences dialog and update config file"""
        dialog = PrefsAPOD(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # get new values
            days_numb_new = dialog.spin_days.get_value_as_int()
            icon_size_new = dialog.spin_size.get_value_as_int()
            print "[ " + BLUE + "settings" + RESET + " ]" + \
                  " icon size =", icon_size_new
            print "[ " + BLUE + "settings" + RESET + " ]" + \
                  " number of days =", days_numb_new
            # update config file
            apod_settings = SettingsAPOD()
            apod_settings.write_settings(days_numb_new, icon_size_new)
            # update liststore and reload treeview
            cache_dir = self.get_cache_dir()  # get cache dir again
            apod_data = self.get_apod_data(days_numb_new)  # get new data
            self.get_liststore(apod_data, cache_dir, icon_size_new)
            self.treeview.set_model(model=self.liststore)
        dialog.destroy()

    # callback for button About
    #---------------------------
    def on_button_about_clicked(self, widget):
        """Show about dialog"""
        about = Gtk.AboutDialog()
        lic = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
        about.set_program_name('pyAPOD')
        about.set_version('0.1')
        about.set_copyright('Copyright (C) 2013 Germán A. Racca')
        about.set_license(lic)
        about.set_website('http://gracca.github.io/pyAPOD')
        about.set_comments('View images from NASA APOD web site.')
        about.set_authors(['Germán A. Racca <gracca@gmail.com>'])
        about.set_documenters(['Germán A. Racca <gracca@gmail.com>'])
        about.connect('response', self.on_about_closed)
        about.show()

    # close about dialog
    #--------------------
    def on_about_closed(self, widget, parameter):
        """Destroy about dialog"""
        widget.destroy()


#############
## C L A S S
###########################
class SettingsAPOD:
    """Manage settings file"""

    def __init__(self):
        """Initialize config file"""
        home = os.environ.get('HOME')
        self.conf_path = os.path.join(home, '.pyAPOD.cfg')
        self.conf_file = ConfigParser.SafeConfigParser()
        self.conf_file.read(self.conf_path)

    def get_settings(self):
        """Read or create the config file"""
        if os.path.isfile(self.conf_path):
            # read config file
            days_numb = self.conf_file.get('pyapod_settings', 'days')
            icon_size = self.conf_file.get('pyapod_settings', 'size')
        else:
            # write a default config file
            days_numb = '7'
            icon_size = '50'
            self.conf_file.add_section('pyapod_settings')
            self.conf_file.set('pyapod_settings', 'days', days_numb)
            self.conf_file.set('pyapod_settings', 'size', icon_size)
            self.conf_file.write(open(self.conf_path, 'w'))
        return int(days_numb), int(icon_size)

    def write_settings(self, days_numb_new, icon_size_new):
        """Write data to config file"""
        self.conf_file.set('pyapod_settings', 'days', str(days_numb_new))
        self.conf_file.set('pyapod_settings', 'size', str(icon_size_new))
        self.conf_file.write(open(self.conf_path, 'w'))
        return


#############
## C L A S S
###########################
class ViewAPOD(Gtk.Window):
    """View and save selected APOD image"""

    def __init__(self, tit, dat, img_name, tmp_name, inf):
        """Initialize the window"""
        Gtk.Window.__init__(self)
        self.img_name = img_name
        self.tmp_name = tmp_name
        name = "APOD from " + dat + " - " + tit
        self.set_title(name)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)

        self.grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.add(self.grid)

        # create the image
        self.image = Gtk.Image()

        # create and add the pixbuf
        self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp_name,
                                                              500,
                                                              500,
                                                              True)
        self.image.set_from_pixbuf(self.pixbuf)
        self.grid.add(self.image)

        # create the buttons: Info and Save
        self.buttonbox = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        self.buttonbox.set_layout(Gtk.ButtonBoxStyle.END)
        self.grid.attach(self.buttonbox, 0, 1, 1, 1)

        self.button_info = Gtk.Button(stock=Gtk.STOCK_INFO)
        self.button_info.connect('clicked', self.on_button_info_clicked,
                                 tit, dat, inf)
        self.buttonbox.add(self.button_info)
        self.buttonbox.set_child_secondary(self.button_info,
                                           is_secondary=True)

        self.button_save = Gtk.Button(stock=Gtk.STOCK_SAVE)
        self.button_save.connect('clicked', self.on_button_save_clicked,
                                 img_name, tmp_name)
        self.buttonbox.add(self.button_save)
        self.buttonbox.set_child_secondary(self.button_save,
                                           is_secondary=True)

        self.button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        self.button_close.connect('clicked', self.on_button_close_clicked)
        self.buttonbox.add(self.button_close)

        self.show_all()

    # callback for button Info
    def on_button_info_clicked(self, widget, tit, dat, inf):
        """Show info about current picture"""
        info = InfoAPOD(tit, dat, inf)

    # callback for button Save
    def on_button_save_clicked(self, widget, img_name, tmp_name):
        """Save current picture"""
        save_dialog = Gtk.FileChooserDialog('Save As', self,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_CANCEL,
                                            Gtk.ResponseType.CANCEL,
                                            Gtk.STOCK_SAVE,
                                            Gtk.ResponseType.ACCEPT))
        save_dialog.set_do_overwrite_confirmation(True)
        save_dialog.set_modal(True)
        save_dialog.set_current_name(img_name)

        response = save_dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            pic = urllib2.urlopen('file://' + tmp_name).read()
            fname = save_dialog.get_filename()
            open(fname, 'wb').write(pic)
        save_dialog.destroy()

    # callback for button Close
    def on_button_close_clicked(self, widget):
        """Destroy window ViewAPOD"""
        self.destroy()


#############
## C L A S S
###########################
class InfoAPOD(Gtk.Window):
    """View info about selected APOD image"""

    def __init__(self, tit, dat, inf):
        """Initialize the window"""
        Gtk.Window.__init__(self)
        self.set_default_size(500, 300)
        name = "APOD from " + dat + " - " + tit
        self.set_title(name)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(3)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        # create a scrolled window
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_vexpand(True)
        self.scrolledwindow.set_hexpand(True)
        self.grid.add(self.scrolledwindow)

        # show the info as a label
        self.label = Gtk.Label()
        text = inf.replace('<p>', '').replace('</p>', '')
        text = text.replace('\n\n', '').replace('\n', ' ')
        text = text.replace('Explanation:', '\n')
        self.label.set_markup(text)
        self.label.set_valign(Gtk.Align.START)
        self.label.set_justify(Gtk.Justification.LEFT)
        self.label.set_line_wrap(True)
        self.scrolledwindow.add_with_viewport(self.label)

        # create a button Close
        self.buttonbox = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        self.buttonbox.set_layout(Gtk.ButtonBoxStyle.END)
        self.grid.attach(self.buttonbox, 0, 1, 1, 1)

        self.button_close = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        self.button_close.connect('clicked', self.on_button_close_clicked)
        self.buttonbox.add(self.button_close)

        self.show_all()

    # callback for button Close
    def on_button_close_clicked(self, widget):
        """Destroy window InfoAPOD"""
        self.destroy()


#############
## C L A S S
###########################
class PrefsAPOD(Gtk.Dialog):
    """Preferences dialog for APOD"""

    def __init__(self, parent):
        """Initialize the window"""
        Gtk.Dialog.__init__(self, 'Configure APOD dates', parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_modal(True)

        # get settings
        apod_settings = SettingsAPOD()
        days, size = apod_settings.get_settings()

        # grid
        self.grid = Gtk.Grid(column_spacing=5, row_spacing=5)

        # label
        self.label_days = Gtk.Label('Select number of days:')
        self.label_days.set_alignment(0, 0)
        self.grid.attach(self.label_days, 0, 0, 1, 1)

        # adjustment
        adjust_days = Gtk.Adjustment(1, 1, 100, 1, 10, 0)

        # spin button
        self.spin_days = Gtk.SpinButton()
        self.spin_days.set_adjustment(adjust_days)
        self.spin_days.set_value(days)
        self.grid.attach(self.spin_days, 1, 0, 1, 1)

        # label
        self.label_size = Gtk.Label('Select icon size (pixels):')
        self.label_size.set_alignment(0, 0)
        self.grid.attach(self.label_size, 0, 1, 1, 1)

        # adjustment
        adjust_size = Gtk.Adjustment(20, 20, 100, 5, 10, 0)

        # spin button
        self.spin_size = Gtk.SpinButton()
        self.spin_size.set_adjustment(adjust_size)
        self.spin_size.set_value(size)
        self.grid.attach(self.spin_size, 1, 1, 1, 1)

        box = self.get_content_area()
        box.add(self.grid)
        self.show_all()


def main():
    """Show the window"""
    win = APOD()
    win.connect('delete-event', Gtk.main_quit)
    win.show_all()
    Gtk.main()
    return 0

if __name__ == '__main__':
    main()
