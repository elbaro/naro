#!/usr/bin/env python3
# Naro
# https://github.com/elbaro

import traceback
import os
import subprocess
import gi
import signal
import json
gi.require_version('Gtk', '3.0')
gi.require_version('Gio', '2.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import AppIndicator3 as appindicator

VERSION = '2016.10.29'
APPINDICATOR_ID = 'naro.emppu.kr'
config_path = os.path.expanduser('~/.config/naro')
print(config_path)


class AboutWindow(Gtk.Dialog):
	def __init__(self):
		Gtk.Window.__init__(self, title='About')

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

		label = Gtk.Label()
		label.set_markup("<b>Naro</b>\n" + VERSION + "\n<a href='https://github.com/elbaro'>github</a> <a href='https://icons8.com/'>icon</a>")
		vbox.pack_start(label, True, True, 0)

		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		btn1 = Gtk.Button("Install")
		btn2 = Gtk.Button("Uninstall")
		btn3 = Gtk.Button("Default\nSettings")
		btn1.set_size_request(80,20)
		btn2.set_size_request(80,20)
		btn3.set_size_request(80,20)
		btn1.connect('clicked', lambda _: install())
		btn2.connect('clicked', lambda _: uninstall())
		btn3.connect('clicked', lambda _: reset_setting())

		hbox.pack_start(btn1, True, False, 0)
		hbox.pack_start(btn2, True, False, 0)
		hbox.pack_start(btn3, True, False, 0)
		vbox.pack_start(hbox, True, True, 0)

		self.get_content_area().pack_start(vbox, True, False, 0)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_default_size(300, 150)


def load_menu():
	try:
		with open(config_path) as config_file:
			config = json.load(config_file)

			def parse_menuitem(obj):
				if type(obj) is str:
					if obj == '':
						return Gtk.SeparatorMenuItem.new()
					return Gtk.MenuItem(obj)
				elif type(obj) is dict:
					item = Gtk.MenuItem(obj.get('name', ''))

					if obj.get('sub') is None:
						if obj.get('cmd') is not None:
							if obj.get('type') == 'hidden':
								if type(obj['cmd']) in [str, list]:
									args = obj['cmd']
								else:
									args = ''
							else:
								# 'ssh server.net'     -> 'gnome-terminal -x ssh server.net'
								# ['ssh','server.net'] -> 'gnome-terminal -x ssh server.net'
								if type(obj['cmd']) is str:
									args = 'gnome-terminal -x ' + obj['cmd']
								elif type(obj['cmd']) is list:
									args = ['gnome-terminal', '-x'] + obj['cmd']
								else:
									args = ''
							item.connect('activate', lambda _: subprocess.Popen(args, shell=True))
					else:
						item.set_submenu(parse_menu(obj['sub']))

					return item
				else:
					print('parse_menuitem: ',obj)
					return Gtk.MenuItem('error! not a json obj or str')

			def parse_menu(obj):
				menu = Gtk.Menu()
				if type(obj) is not list:
					menu.append(Gtk.MenuItem('error! not a json list'))
				else:
					for entry in obj:
						item = parse_menuitem(entry)
						menu.append(item)
				return menu

			return parse_menu(config)
	except (IOError, json.decoder.JSONDecodeError) as e:
		print('load_menu(): ', e)
		traceback.print_exc()

	return Gtk.Menu()


def create_menu():
	menu = load_menu()
	menu.append(Gtk.SeparatorMenuItem.new())

	item = Gtk.MenuItem('About')
	item.connect('activate', lambda _: AboutWindow().show_all())
	menu.append(item)

	item = Gtk.MenuItem('Setting')
	item.connect('activate', lambda _: subprocess.call(['xdg-open', config_path]))
	menu.append(item)

	item = Gtk.MenuItem('Exit')
	item.connect('activate', Gtk.main_quit)
	menu.append(item)

	menu.show_all()
	return menu


def install():
	desktop = """[Desktop Entry]
Type=Application
Name=Naro
GenericName=Shell Command Launcher
Categories=Utility;
Comment=Run your common shell commands from tray
Keywords=indicator;
Icon=psensor
TryExec=naro
Exec=naro
StartupNotify=false
"""
	desktop_path = os.path.expanduser('~/.config/autostart/naro.desktop')

	with open(desktop_path, 'w') as f:
		f.write(desktop)

	pwd = os.path.realpath(__file__)
	ICON = 'iVBORw0KGgoAAAANSUhEUgAAADQAAAA0CAYAAADFeBvrAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4AocEQciDSpfwAAAAURJREFUaN7t2dGRgjAUBdB7HQuwhO1gYwdsJUoH24kluJ1YAlCBlkAH148NyiAfG4Nuknn3k2EGzuTxQhLAYrEsFkk7SY3ySSNpNzbQQzYATgBcpmPRAvgi2Q+gJmPMDUVyu5L0XQAGAJykPQsZnfsoSVJJjW1VWqc2kIHenPX0Aklm9ncjKzkDGchAcSBJPzNrkX2ybW+c3FAP7/9XUKqoKFCKqGhQaqhFQCmhFgOlgpo+PHYeSm+1G1Fyx2JKLhXMUm07CCOpknQO2A09S6reNbEGj0wg5oZ6OejZMpPUPwG6vBQU8834kruEYGJK7mGj0fYUbIFnIAMZyED/CfIHyLnMQR9zF9vJZHuavTFBjH/XcVr6Q+NDIRVXD8f6LYDPzDEdSTd8QxWALmeMN/w2BZI9SQegzgzWAahJOpI9LBZLdK4+NaUqt1gyAwAAAABJRU5ErkJggg=='
	cmd = '/bin/cp %s /usr/local/bin/naro && chmod +x /usr/local/bin/naro && echo %s | base64 --decode > /usr/share/icons/Console-52-w.png' % (pwd, ICON)
	if subprocess.call(['pkexec','/bin/sh','-c', cmd]) == 0:
		msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Installation Completed")
	else:
		msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Installation Failed")
		msg.format_secondary_text('Copying to /usr/local/bin/naro failed')
	msg.run()
	msg.destroy()


def uninstall():
	desktop_path = os.path.expanduser('~/.config/autostart/naro.desktop')
	try:
		os.remove(desktop_path)
	except FileNotFoundError:
		pass

	ret = subprocess.call(['pkexec', '/bin/rm', '/usr/local/bin/naro'])
	if ret in [0, -1]:  # -1: File Not Found, -126: pkexec cancelled
		msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Uninstall Completed")
	else:
		msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Uninstall Failed")
		msg.format_secondary_text('Removing /usr/local/bin/naro failed')
		print(ret)
	msg.run()
	msg.destroy()


def reset_setting():
	default = """[
	{
		"name": "server1.com",
		"cmd": "ssh user@server1.com -p 1234"
	},
	{
		"name": "server2.com",
		"sub":
		[
			{
				"name": "ftp",
				"cmd": "ftp user@server2.com"
			},
			{
				"name": "telnet",
				"cmd": "telnet user@server2.com"
			}
		]
	},
	"---- this item does nothing ----",
	"",
	"^ this is a separator",
	{
		"type": "hidden",
		"name": "Sync from remote (silent)",
		"cmd": "scp -p 8888 user@remotehost:/home/user/file local/dir/file"
	},
	{
		"name": "Sync from remote (terminal)",
		"cmd": "scp -p 8888 user@remotehost:/home/user/file local/dir/file"
	}
]
"""
	with open(config_path, 'w') as f:
		f.write(default)

	msg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Setting reset")
	msg.run()
	msg.destroy()


def main():
	if not os.path.isfile('/usr/share/icons/Console-52-w.png'):
		install()
	indicator = appindicator.Indicator.new(APPINDICATOR_ID, '/usr/share/icons/Console-52-w.png', appindicator.IndicatorCategory.APPLICATION_STATUS)
	indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
	indicator.set_menu(create_menu())

	def config_changed(monitor, gio_file, other_file, event_type):
		if event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
			print('config changed')
			indicator.set_menu(create_menu())

	config_monitor = Gio.File.new_for_path(config_path).monitor_file(Gio.FileMonitorFlags.NONE)
	config_monitor.connect('changed', config_changed)
	Gtk.main()


if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	main()
