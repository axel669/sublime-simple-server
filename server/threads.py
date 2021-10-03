from threading import Thread, Event
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

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
    def __init__(self, directory, port, display):
        super().__init__(self)
        self.quit_event = Event()
        handler = partial(ManagedRequestHandler, directory = directory)
        server = ManagedServer(("", port), handler)
        server.timeout = 0.1
        self.server = server
        self.port = port
        self.path = directory
        self.display = display

    def run(self):
        while self.quit_event.is_set() == False:
            self.server.handle_request()
        self.server.server_close()
        for conn in self.server.connections:
            conn.shutdown(1)
            conn.close()

threads = {}
def create(windowID, port, path, display):
    if windowID in threads:
        return

    thread = ServerThread(path, port, display)
    thread.daemon = True
    thread.start()
    threads[windowID] = thread

def running(windowID):
    return windowID in threads

def status(windowID):
    if windowID not in threads:
        return ""
    thread = threads[windowID]
    return f"[🌐 Simple Server] port {thread.port} from {thread.display}"

def destroy(windowID):
    if windowID not in threads:
        return
    thread = threads[windowID]
    thread.quit_event.set()
    thread.join()
    threads.pop(windowID, None)
