# Listens for RevolutionBot to change the server name.
# Note: this is currently set up to listen only on localhost,
# but it's pretty straightforward to adapt it to communicate over the internet.

from multiprocessing.connection import Listener
from _thread import start_new_thread
from threading import Lock

from common import send_image_message
from responses import normalize_message

address = ('localhost', 420)

class revbot_listener:
    def __init__(self, updater):
        self.updater  = updater
        self.listener = Listener(address)
        self.handlers = dict()
        self.lock     = Lock()

        def thread_loop():
            connection = self.listener.accept()

            while True:
                try:
                    message = connection.recv()

                    if isinstance(message, tuple) and len(message) == 2:
                        with self.lock:
                            if message[0] in self.handlers:
                                for handler in self.handlers[message[0]]: handler(self.updater, message[1])

                    else:
                        print('[RevBot Listener]: Received invalid message.')
                except EOFError: connection = self.listener.accept()

        start_new_thread(thread_loop, ())


    def add_handler(self, msg_type, handler):
        with self.lock:
            if msg_type in self.handlers: self.handlers[msg_type].append(handler)
            else: self.handlers[msg_type] = [handler]



def on_server_name_changed(updater, arguments):
    chat_id, chat_name = arguments
    chat_name = normalize_message(chat_name)

    def any_in_name(*strings):
        return any([s in chat_name for s in list(strings)])

    if any_in_name('soviet', 'communis', 'marx', 'lenin', 'stalin', 'jinping'):
        send_image_message(updater, chat_id, 'happy_xi.jpg')
    elif any_in_name('uyghur', 'capitalis'):
        send_image_message(updater, chat_id, 'sad_xi.jpg')
