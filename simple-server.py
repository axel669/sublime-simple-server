import sublime
import sublime_plugin

import json
from os import path, getcwd
from importlib import import_module

serverThreads = import_module("simple-server.server.threads")

def plugin_unloaded():
	for window in sublime.windows():
		window.run_command("simple_server_stop")

def resolve_settings_path(window):
	project_file = window.project_file_name()
	project_data = window.project_data()

	if project_data == None:
		return None

	if project_file == None:
		return project_data["folders"][0]["path"]

	return path.dirname(project_file)

def load_settings(window):
	base_dir = resolve_settings_path(window)
	settings_file = path.join(base_dir, "simple-server.json")

	if path.exists(settings_file) == False:
		return {"baseDir": base_dir}

	with open(settings_file) as json_file_handle:
		settings = json.load(json_file_handle)
		settings["baseDir"] = base_dir
		return settings

status_name = "simple_server_status"
class ViewStatus(sublime_plugin.EventListener):
	def on_activated(self, view):
		window = view.window()
		if window == None:
			return

		if serverThreads.running(window.id()) == False:
			view.erase_status(status_name)
			return
		view.set_status(
			status_name,
			serverThreads.status(
				window.id()
			)
		)

class SimpleServerStart(sublime_plugin.WindowCommand):
	def is_enabled(self):
		if resolve_settings_path(self.window) == None:
			return False
		return True

	def run(self, **args):
		settings = load_settings(self.window)

		loadedPath = settings.get("path", ".")
		servePath = (
			loadedPath
			if path.isabs(loadedPath) == False
			else f".{loadedPath}"
		)

		targetPath = path.abspath(
			path.join(
				settings.get("baseDir"),
				servePath
			)
		)

		serverThreads.create(
			windowID = self.window.id(),
			port = settings.get("port", 8008),
			path = targetPath,
			display = loadedPath
		)
		self.window.active_view().set_status(
			status_name,
			serverThreads.status(self.window.id())
		)

class SimpleServerStop(sublime_plugin.WindowCommand):
	def is_enabled(self):
		if resolve_settings_path(self.window) == None:
			return False
		return True

	def run(self, **args):
		serverThreads.destroy(self.window.id())
		self.window.active_view().erase_status(status_name)
