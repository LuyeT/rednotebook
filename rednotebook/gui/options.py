# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
# 
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import logging

import gtk
import gobject

from widgets import UrlButton, CustomComboBoxEntry

class Option(gtk.HBox):
	def __init__(self, text, option_name, *widgets):
		gtk.HBox.__init__(self)
		
		self.text = text
		self.option_name = option_name
		
		self.set_spacing(5)
		
		self.label = gtk.Label(self.text)
		self.pack_start(self.label, False, False)
		for widget in widgets:
			self.pack_start(widget, False, False)
		
	def get_value(self):
		raise NotImplementedError
		
	def get_string_value(self):
		return str(self.get_value()).strip()


class TickOption(Option):
	def __init__(self, text, name):
		self.text = text
		self.check_button = gtk.CheckButton(self.text)
		self.check_button.set_active(Option.config.read(name, 0) == 1)
			
		Option.__init__(self, '', name, self.check_button)
		
	def get_value(self):
		return self.check_button.get_active()
		
	def get_string_value(self):
		'''
		We use 0 and 1 internally for bool options
		'''
		return int(self.get_value())
	
	
#class TextOption(Option):
#	def __init__(self, text, name):		
#		self.entry = gtk.Entry(20)
#		self.entry.set_text(Option.config.read(name, ''))
#		
#		LabelAndWidgetOption.__init__(self, text, name, self.entry)
#		
#	def get_value(self):
#		return self.entry.get_text()
	
	
#class TextAndButtonOption(TextOption):
#	def __init__(self, text, name, button):
#		TextOption.__init__(self, text, name)
		
#		self.widget.pack_end(button, False, False)
		
		
class ComboBoxOption(Option):
	def __init__(self, text, name, entries, *widgets):
		self.combo = CustomComboBoxEntry(gtk.ComboBoxEntry(gtk.ListStore(gobject.TYPE_STRING)))
		self.combo.set_entries(entries)
		
		Option.__init__(self, text, name, self.combo.comboBox, *widgets)
		
	def get_value(self):
		return self.combo.get_active_text()
	
	
class DateFormatOption(ComboBoxOption):
	def __init__(self, text, name):
		date_formats = ['%A, %x %X', '%A, %x, Day %j', '%H:%M', 'Week %W of Year %Y', \
						'%y-%m-%d', 'Day %j', '%A', '%B']
		
		date_url = 'http://docs.python.org/library/time.html#time.strftime'
		date_format_help_button = UrlButton('Help', date_url)
		
		self.preview = gtk.Label()
		
		ComboBoxOption.__init__(self, text, name, date_formats, self.preview, \
										date_format_help_button)
		
		# Set default format if not present
		format = Option.config.read(name, '%A, %x %X')
		self.combo.set_active_text(str(format))
		
		self.combo.connect('changed', self.on_format_changed)
		
		# Update the preview
		self.on_format_changed(None)
		
	def on_format_changed(self, widget):
		import time
		self.preview.set_text('Result: %s' % time.strftime(self.combo.get_active_text()))
		
class FontSizeOption(ComboBoxOption):
	def __init__(self, text, name):
		sizes = range(6, 15) + range(16, 29, 2) + [32, 36, 40, 48, 56, 64, 72]
		sizes = ['default'] + map(str, sizes)
		
		ComboBoxOption.__init__(self, text, name, sizes)
		
		# Set default size if not present
		size = Option.config.read(name, -1)
		
		if size == -1:
			self.combo.set_active_text('default')
		else:
			self.combo.set_active_text(str(size))
			
		self.combo.set_editable(False)
		self.combo.comboBox.set_wrap_width(3)
		
		self.combo.connect('changed', self.on_combo_changed)
		
	def on_combo_changed(self, widget):
		'''Live update'''
		size = self.get_string_value()
		Option.main_window.set_font_size(size)
		
	def get_string_value(self):
		'''We use 0 and 1 internally for size options'''
		size = self.combo.get_active_text()
		if size == 'default':
			return -1
		try:
			return int(size)
		except ValueError:
			return -1
		
		
#class SpinOption(LabelAndWidgetOption):
#	def __init__(self, text, name):
#		
#		adj = gtk.Adjustment(10.0, 6.0, 72.0, 1.0, 10.0, 0.0)
#		self.spin = gtk.SpinButton(adj)#, climb_rate=1.0)
#		self.spin.set_numeric(True)
#		self.spin.set_range(6,72)
#		self.spin.set_sensitive(True)
#		value = Option.config.read(name, -1)
#		if value >= 0:
#			self.spin.set_value(value)
#		
#		LabelAndWidgetOption.__init__(self, text, name, self.spin)
#		
#	def get_value(self):
#		print type(self.spin.get_value())
#		return self.spin.get_value()
#		
#	def get_string_value(self):
#		value = int(self.get_value())
#		return value
	

class OptionsDialog(object):
	def __init__(self, dialog):
		self.dialog = dialog
		self.categories = {}
		
	def __getattr__(self, attr):
		'''Wrap the dialog'''
		return getattr(self.dialog, attr)
	
	def add_option(self, category, option):
		self.categories[category].pack_start(option, False)
		option.show_all()
		
	def add_category(self, name, vbox):
		self.categories[name] = vbox
		
	def clear(self):
		for category, vbox in self.categories.items():
			for option in vbox.get_children():
				vbox.remove(option)
		

class OptionsManager(object):
	def __init__(self, main_window):
		self.main_window = main_window
		self.xml = main_window.wTree
		self.redNotebook = main_window.redNotebook
		self.config = self.redNotebook.config
		
		self.dialog = OptionsDialog(self.xml.get_widget('options_dialog'))
		self.dialog.add_category('general', self.xml.get_widget('general_vbox'))
		
	def on_options_dialog(self):
		self.dialog.clear()
		
		# Make the config globally available
		Option.config = self.config
		Option.main_window = self.main_window
		
		self.options = [
				TickOption('Check for new versions at startup', 'checkForNewVersion'),
				DateFormatOption('Date/Time format', 'dateTimeString'),
				FontSizeOption('Font Size', 'mainFontSize'),
				]
		
		self.add_all_options()
		
		response = self.dialog.run()
		
		if response == gtk.RESPONSE_OK:
			self.save_options()
		else:
			# Reset some options
			self.main_window.set_font_size(self.config.read('mainFontSize', -1))
			
		self.dialog.hide()
		
	def add_all_options(self):
		for option in self.options:
			self.dialog.add_option('general', option)
			
	def save_options(self):
		logging.debug('Saving Options')
		for option in self.options:
			value = option.get_string_value()
			logging.debug('Setting %s = %s' % (option.option_name, value))
			self.config[option.option_name] = value
			