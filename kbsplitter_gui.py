#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import os
import glob
import threading
import kbsplitter
import json

class ConfigViewWindow(Adw.Window):
    def __init__(self, config_path):
        super().__init__(title=f"Configuration - {os.path.basename(config_path)}")
        self.set_default_size(500, 600)
        
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        self.main_box.append(scrolled)
        
        # Create a vertical box for the mappings
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        scrolled.set_child(vbox)
        
        # Read and display the config
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        xbox_key, keyboard_key = line.split('=')
                        # Create a row for each mapping
                        row = Adw.ActionRow()
                        row.set_title(xbox_key)
                        row.set_subtitle(keyboard_key if keyboard_key else "Not mapped")
                        vbox.append(row)

class DeviceSelectDialog(Adw.Window):
    def __init__(self, parent):
        super().__init__(title="Select Keyboard Device")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(400, 300)
        
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda x: self.close())
        header.pack_start(cancel_button)
        
        # Select button
        select_button = Gtk.Button(label="Select")
        select_button.add_css_class("suggested-action")
        select_button.connect("clicked", self.on_select)
        header.pack_end(select_button)
        
        # Create list box for devices
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.add_css_class("boxed-list")
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.list_box)
        self.main_box.append(scrolled)
        
        # Populate devices
        self.populate_devices()
    
    def populate_devices(self):
        for f in glob.glob('/dev/input/event*'):
            try:
                with open(f, 'rb') as fd:
                    dev = kbsplitter.libevdev.Device(fd)
                    # Check if it's a keyboard
                    passed = True
                    for c in kbsplitter.CHECKS:
                        if not dev.has(c):
                            passed = False
                            break
                    if passed:
                        row = Adw.ActionRow()
                        row.set_title(dev.name)
                        row.set_subtitle(f)
                        self.list_box.append(row)
            except (PermissionError, OSError):
                continue
    
    def get_selected_device(self):
        row = self.list_box.get_selected_row()
        if row:
            return row.get_subtitle()
        return None

    def on_select(self, button):
        if self.get_selected_device():
            self.response = Gtk.ResponseType.OK
        self.close()

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Keyboard to Xbox Controller")
        self.set_default_size(600, 400)

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Config list
        self.create_config_list()
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_start(10)
        button_box.set_margin_end(10)
        button_box.set_margin_bottom(10)
        self.main_box.append(button_box)

        # Run button
        self.run_button = Gtk.Button(label="Run Controller")
        self.run_button.connect("clicked", self.on_run_clicked)
        self.run_button.add_css_class("suggested-action")
        button_box.append(self.run_button)

        # View Config button
        self.view_button = Gtk.Button(label="View Configuration")
        self.view_button.connect("clicked", self.on_view_clicked)
        button_box.append(self.view_button)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.add_css_class("status")
        self.main_box.append(self.status_label)

        self.controller = None
        self.running = False

    def create_config_list(self):
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box.append(scrolled)

        # Create list store
        self.config_store = Gtk.ListStore(str, str)  # filename, full path
        
        # Find config files
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        for config_file in glob.glob(os.path.join(config_dir, "*.cfg")):
            filename = os.path.basename(config_file)
            self.config_store.append([filename, config_file])

        # Create tree view
        self.config_tree = Gtk.TreeView(model=self.config_store)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Available Configurations", renderer, text=0)
        self.config_tree.append_column(column)

        scrolled.set_child(self.config_tree)

    def get_selected_config(self):
        selection = self.config_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            return model[treeiter][1]  # Return full path
        return None

    def on_view_clicked(self, button):
        config_path = self.get_selected_config()
        if config_path:
            config_window = ConfigViewWindow(config_path)
            config_window.show()
        else:
            self.status_label.set_text("Please select a configuration first")

    def on_run_clicked(self, button):
        if self.running:
            self.running = False
            self.run_button.set_label("Run Controller")
            self.status_label.set_text("Controller stopped")
            return

        config_path = self.get_selected_config()
        if not config_path:
            self.status_label.set_text("Please select a configuration first")
            return

        dialog = DeviceSelectDialog(self)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            device_path = dialog.get_selected_device()
            dialog.destroy()
            
            if device_path:
                self.running = True
                self.run_button.set_label("Stop Controller")
                self.status_label.set_text(f"Running with config: {os.path.basename(config_path)}")
                
                # Start controller in separate thread
                thread = threading.Thread(
                    target=self.run_controller,
                    args=(device_path, config_path),
                    daemon=True
                )
                thread.start()
        else:
            dialog.destroy()

    def run_controller(self, device_path, config_path):
        try:
            # Prepare keyboard device
            fd = open(device_path, 'rb')
            while kbsplitter.anyKeyPressed(fd):
                time.sleep(0.01)
            devkb = kbsplitter.libevdev.Device(fd)

            # Create controller
            controller = kbsplitter.XBoxController(config_path, devkb)
            controller.create()

            devkb.grab()
            
            while self.running:
                for e in devkb.events():
                    if not self.running:
                        break
                    controller.fire(e)

            devkb.ungrab()
            fd.close()
            
        except Exception as e:
            GLib.idle_add(
                self.status_label.set_text,
                f"Error: {str(e)}"
            )
            self.running = False
            GLib.idle_add(
                self.run_button.set_label,
                "Run Controller"
            )

def main():
    app = Adw.Application(application_id="org.kbsplitter")
    app.connect('activate', on_activate)
    app.run(None)

def on_activate(app):
    win = MainWindow(app)
    win.present()

if __name__ == "__main__":
    main() 