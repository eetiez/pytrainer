# -*- coding: iso-8859-1 -*-

#Copyright (C) Fiz Vazquez vud1@sindominio.net

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from SimpleGladeApp import SimpleGladeApp
import gtk
import gobject
import os, glob, sys
import StringIO
import logging
from lxml import etree

from pytrainer.gui.warning import Warning

class WindowImportdata(SimpleGladeApp):
	def __init__(self, data_path = None, parent=None, config=None):
		self.data_path = data_path
		self.glade_path=data_path+"glade/importdata.glade"
		self.root = "win_importdata"
		self.domain = None
		self.parent = parent
		self.configuration = config
		self.store = None
		#SimpleGladeApp.__init__(self, data_path+glade_path, root, domain)

	def run(self):
		SimpleGladeApp.__init__(self, self.glade_path, self.root, self.domain)
		
	def new(self):
		self.defaulttab = self.configuration.getValue("pytraining","import_default_tab")
		if self.defaulttab == "":
			self.defaulttab = 0
		else:
			self.defaulttab = int(self.defaulttab)
		self.notebookMainTabs.set_current_page(self.defaulttab)

	def updateStatusbar(self, statusbar, text, context_id = None):
		if context_id is None:
			context_id = statusbar.get_context_id(text)
		statusbar.push(context_id, text)
		return context_id

	def init_gpsdevice_tab(self):
		return

	def init_file_tab(self):
		self.buttonClearFile.set_sensitive(0)
		self.buttonImport.set_sensitive(0)
		return

	def init_options_tab(self):
		#Set correct radiobutton based on saved preference
		if self.defaulttab == 1:
			self.radiobuttonFile.set_active(1)
		else:
			self.radiobuttonTabGPSDevice.set_active(1)
		return


	def validateFile(self, import_filename):
		"""
			Iterate through all supported types of file by reading processing files from import directory
			Each processing file understands one type of file

			If a processing file is found that recognises the selected file:
				 returns the instantiated class
			otherwise:
				 returns None
		"""
		logging.debug('>>')
		self.updateStatusbar(self.statusbarImportFile, "Checking file type for: " + import_filename)
		#Get import files_* files
		fileList = glob.glob(self.data_path+"import/file_*.py")
		for processingFile in fileList:
			directory, filename = os.path.split(processingFile)
			filename = filename.rstrip('.py') 
			classname = filename.lstrip('file_')
			#Import module
			sys.path.insert(0, self.data_path+"import")
			module = __import__(filename)
			processMain = getattr(module, classname)
			#Instantiate module
			processClass = processMain(self.parent, self.data_path)
			isValid = processClass.testFile(import_filename) 
			if isValid:
				logging.debug('<<')
				return processClass
			else:
				processClass = None
		logging.debug('<<')
		return processClass

		
		self.updateStatusbar(self.statusbarImportFile, "Unknown file type")
		logging.debug('<<')
		return None

	def build_tree_view(self):
		store = gtk.ListStore(gobject.TYPE_STRING,
								gobject.TYPE_BOOLEAN, 
								gobject.TYPE_STRING, 
								gobject.TYPE_STRING, 
								gobject.TYPE_STRING, 
								gobject.TYPE_STRING, 								 
								gobject.TYPE_STRING )
		column_names=["id", _(""),_("Start Time"), _("Distance"),_("Duration"),_("Sport"), _("Notes")]
		for column_index, column_name in enumerate(column_names):
			if column_index == 1: 
				#Add checkbox column
				self.renderer1 = gtk.CellRendererToggle()
				self.renderer1.set_property('activatable', True)
				self.renderer1.connect( 'toggled', self.treeviewImportEvents_toggled_checkbox, store )	
				column = gtk.TreeViewColumn(column_name, self.renderer1 )
				column.add_attribute( self.renderer1, "active", column_index)
				column.connect('clicked', self.treeviewImportEvents_header_checkbox, store)
			else:
				#Add other columns
				column = gtk.TreeViewColumn(column_name, gtk.CellRendererText(), text=column_index)
			#if column_name == "id":
			#	column.set_visible(False)
			column.set_resizable(True)
			#column.set_sort_column_id(0)
			self.treeviewImportEvents.append_column(column)
		self.treeviewImportEvents.set_headers_clickable(True)
		self.treeviewImportEvents.set_model(store)
		return store

	def treeviewImportEvents_toggled_checkbox( self, cell, path, store ):
		"""
			Sets the state of the checkbox to true or false.
		"""
		store[path][1] = not store[path][1]
		self.buttonImport.set_sensitive(0)
		for item in store:
			if item[1]:
				#Only enable import button if at least one activity is selected
				self.buttonImport.set_sensitive(1)
		return	

	def treeviewImportEvents_setCheckboxes(self, state):
		"""
			Sets or unsets all checkboxes
		"""
		if self.store is None:
			return
		for item in self.store:
			item[1] = state
		if state:
			self.buttonImport.set_sensitive(1)
		else:
			self.buttonImport.set_sensitive(0)			

	def saveOptions(self):
		"""
			Save options selected in options tab
		"""
		#Default tab option
		if self.radiobuttonTabGPSDevice.get_active():
			self.defaulttab = "0"
		elif self.radiobuttonFile.get_active():
			self.defaulttab = "1"
		self.configuration.setValue("pytraining","import_default_tab",self.defaulttab)	
		#option


	############################
	## Window signal handlers ##
	############################

	def treeviewImportEvents_header_checkbox(self, column, store):
		"""
			Handler for click on checkbox column
		"""
		if store is None:
			return
		for item in store:
			if item[1]:
				self.treeviewImportEvents_setCheckboxes(False)
				return
		self.treeviewImportEvents_setCheckboxes(True)

	def on_win_importdata_delete_event(self, widget, window):
		self.win_importdata.hide()
		
	def on_notebookMainTabs_switch_page(self, notebook, page, new_page):
		if new_page == 0:
			#Switched to 'Import from GPS Device' tab
			self.init_gpsdevice_tab()
		elif new_page == 1:
			#Switched to 'Import from File' tab
			self.init_file_tab()
		elif new_page ==2:
			#Switched to 'Options' tab
			self.init_options_tab()
		else:
			#Switched to unknown tab
			pass

	def on_filechooserbuttonSelectFile_file_set(self, widget):
		self.buttonClearFile.set_sensitive(1) #Enable clear button
		self.buttonImport.set_sensitive(0) #Disable import button
		self.updateStatusbar(self.statusbarImportFile, "" ) #Clear status bar
		#Build treeview
		if self.store is None:
			self.store = self.build_tree_view()
		else:
			self.store.clear()
		#Validate file
		processClass = self.validateFile(self.filechooserbuttonSelectFile.get_filename())
		if processClass is not None:
			self.updateStatusbar(self.statusbarImportFile, _("Found file of type: %s") % processClass.getFileType() )
			#Get activities in file
			activitiesSummary = processClass.getActivitiesSummary()			
			for activity in activitiesSummary:
				if not activity[1]:
					#Activity selected, so enable import button
					self.buttonImport.set_sensitive(1)
					note = ""
				else:
					note = _("Found in database")
				#Add activity details to TreeView store to display
				iter = self.store.append()
				self.store.set(
					iter,
					0, activity[0],
					1, not activity[1],
					2, activity[2],
					3, activity[3],
					4, activity[4],
					5, activity[5],
					6, note,
					)
		else:
			#Selected file not understood by any of the process files
			self.updateStatusbar(self.statusbarImportFile, _("Unknown file type") )
			#Display warning
			msg = _("File selected is of unknown or unsupported file type")
			warning = Warning(self.data_path)
			warning.set_text(msg)
			warning.run()

	def on_buttonClearFile_clicked(self, widget):	
		self.filechooserbuttonSelectFile.unselect_all() 
		self.updateStatusbar(self.statusbarImportFile, _("No file selected") )
		self.store.clear()

	def on_buttonSave_clicked(self, widget):
		self.updateStatusbar(self.statusbarOptions, "Saving options")
		self.saveOptions()
		self.updateStatusbar(self.statusbarOptions, "Options saved")

	def on_buttonReset_clicked(self, widget):
		#GPS Device is default
		self.defaulttab = 0
		#self.saveOptions()
		#Redisplay tab
		self.init_options_tab()
		self.updateStatusbar(self.statusbarOptions, "")

	def on_buttonImport_clicked(self, widget):
		self.updateStatusbar(self.statusbarImportFile, "buttonImport clicked")
		


