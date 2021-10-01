import sublime
import sublime_plugin

import os
import json
from threading import Thread, Event
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def plugin_unloaded():
	# Shut down all listening servers when the plugin reloads
	for window in sublime.windows():
		window.run_command("simple_server", {"cmd": "stop"})

def readValue(source, key, default = None):
	if key in source:
		return source[key]
	return default

class ManagedServer(ThreadingHTTPServer):
	def __init__(self, *args, **kargs):
		super().__init__(*args, **kargs)
		self.connections = []

class ManagedRequestHandler(SimpleHTTPRequestHandler):
	def handle_one_request(self):
		self.server.connections.append(self.connection)
		super().handle_one_request()
	def finish(self):
		super().finish()
		self.server.connections.remove(self.connection)

class ServerThread(Thread):
	def __init__(self, directory, port):
		super().__init__(self)
		self.quit_event = Event()
		handler = partial(ManagedRequestHandler, directory = directory)
		server = ManagedServer(("", port), handler)
		server.timeout = 0.1
		self.server = server

	def run(self):
		while self.quit_event.is_set() == False:
			self.server.handle_request()
		self.server.server_close()
		for conn in self.server.connections:
			conn.shutdown(1)
			conn.close()
		print("Simple Server: stopped")

status_name = "simple_server_status"
def status_message(port, folder):
	return f"🌐 Simple Server on {port} from {folder}"

class ViewTracker(sublime_plugin.EventListener):
	parents = {}
	windows = {}
	def on_activated(self, view):
		# Some views aren't attached to windows because they don't represent
		# files.
		if view.window() is None:
			return

		wid = view.window().id()
		if wid in self.windows and self.windows[wid] != False:
			view.set_status(
				status_name,
				status_message(*self.windows[wid])
			)
			return
		view.erase_status(status_name)

class SimpleServer(sublime_plugin.WindowCommand):
	def __init__(self, window):
		super().__init__(window)
		project_file = self.window.project_file_name()

		if project_file == None:
			self.root = None
			return

		self.root = os.path.dirname(self.window.project_file_name())
		self.thread = None
		ViewTracker.windows[window.id()] = False

	def is_enabled(self, *args):
		return self.root != None

	def start(self, **args):
		if self.thread != None:
			return

		settingsPath = os.path.join(self.root, "simple-server.json")

		f = open(settingsPath)
		settings = json.load(f)
		f.close()

		directory = readValue(settings, "root", ".")
		port = readValue(settings, "port", 1337)
		self.auto_show_panel = readValue(settings, "show_panel", True)

		targetPath = os.path.join(self.root, directory)
		thread = ServerThread(targetPath, port)
		thread.daemon = True
		thread.start()
		self.thread = thread

		args = (port, directory)
		ViewTracker.windows[self.window.id()] = args
		self.window.active_view().set_status(
			status_name,
			status_message(*args)
		)

	def stop(self, **args):
		if self.thread == None:
			return
		self.thread.quit_event.set()
		self.thread.join()
		self.thread = None
		ViewTracker.windows[self.window.id()] = False
		self.window.active_view().erase_status(status_name)

	def run(self, **args):
		if hasattr(self, args["cmd"]) == False:
			return

		getattr(self, args["cmd"])(**args)
