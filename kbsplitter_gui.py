#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import os
import glob
import threading
import kbsplitter
import json

class ConfigViewWindow(Gtk.Window):
    def __init__(self, config_path):
        super().__init__(title=f"Configuration - {os.path.basename(config_path)}")
        self.set_default_size(500, 600)
        
        # Main container
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled)
        
        # Create a vertical box for the mappings
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        scrolled.add(vbox)
        
        # Read and display the config
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        xbox_key, keyboard_key = line.split('=')
                        # Create a row for each mapping
                        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
                        xbox_label = Gtk.Label(label=xbox_key)
                        xbox_label.set_size_request(150, -1)
                        keyboard_label = Gtk.Label(label=keyboard_key)
                        
                        hbox.pack_start(xbox_label, False, False, 0)
                        hbox.pack_start(Gtk.Label(label="→"), False, False, 0)
                        hbox.pack_start(keyboard_label, False, False, 0)
                        
                        vbox.pack_start(hbox, False, False, 0)
        
        self.show_all()

class DeviceSelectDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Select Keyboard Device", transient_for=parent, flags=0)
        self.set_default_size(400, 300)
        
        # Add buttons
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        # Create list store and view for devices
        self.store = Gtk.ListStore(str, str)  # device path, device name
        self.tree = Gtk.TreeView(model=self.store)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Available Keyboards", renderer, text=1)
        self.tree.append_column(column)
        
        # Add to scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.tree)
        
        # Add to dialog's content area
        self.get_content_area().add(scrolled)
        
        # Populate devices
        self.populate_devices()
        
        self.show_all()
    
    def populate_devices(self):
        # Use the existing printKeyboards logic but capture the output
        for f in glob.glob('/dev/input/event*'):
            try:
                with open(f, 'rb') as fd:
                    dev = kbsplitter.libevdev.Device(fd)
                    # Check if it's a keyboard using the same logic as in kb2xbox.py
                    passed = True
                    for c in kbsplitter.CHECKS:
                        if not dev.has(c):
                            passed = False
                            break
                    if passed:
                        self.store.append([f, f"{dev.name} ({f})"])
            except (PermissionError, OSError):
                continue
    
    def get_selected_device(self):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            return model[treeiter][0]
        return None

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Keyboard to Xbox Controller")
        self.set_border_width(10)
        self.set_default_size(600, 400)

        # Main vertical box
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        # Config list
        self.create_config_list()
        
        # Buttons box
        self.button_box = Gtk.Box(spacing=6)
        self.vbox.pack_start(self.button_box, False, True, 0)

        # Run button
        self.run_button = Gtk.Button(label="Run Controller")
        self.run_button.connect("clicked", self.on_run_clicked)
        self.button_box.pack_start(self.run_button, True, True, 0)

        # View Config button
        self.view_button = Gtk.Button(label="View Configuration")
        self.view_button.connect("clicked", self.on_view_clicked)
        self.button_box.pack_start(self.view_button, True, True, 0)

        # Status label
        self.status_label = Gtk.Label()
        self.vbox.pack_start(self.status_label, False, True, 0)

        self.controller = None
        self.running = False

    def create_config_list(self):
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.vbox.pack_start(scrolled, True, True, 0)

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

        scrolled.add(self.config_tree)

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
    win = MainWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main() 