import queue
import socket
import threading as th
import sky_client.utils.encryption as encryption
import sky_client.utils.message as msg

# import utils.encryption as encryption
# import utils.message as msg


class MessageReceiver(th.Thread):
    def __init__(self, client, connection):
        super().__init__()
        self.daemon = True
        self.client = client
        self.socket = connection
        self.recieved_queue = queue.Queue()
        self.stop = False

    def run(self):
        # self.socket.settimeout(0.2)
        while not self.stop:
            try:
                #вставить Lock
                data = self.socket.recv(1024)
                if not data:
                    break
                else:
                    self.recieved_queue.put(data)
                    self.client.new_message()
            except:
                pass


class MessageSender(th.Thread):
    def __init__(self,  connection):
        super().__init__()
        self.daemon = True
        self.socket = connection
        self.send_queue = queue.Queue()
        self.stop = False


    def run(self):
        while not self.stop:
            if self.send_queue.not_empty:
                message = self.send_queue.get()
                # вставить Lock
                self.socket.sendall(message)

class Client:
    # инициализация клиента
    def __init__(self, host, port):
        self.server_address = (host, port)
        self.listener = None
        self.session_key_recieved_by_server = False
        self.cipher_rsa = b''
        self.authenticated = False

    # соединение с сервером, encryption, запуск получателя и отправителя сообщений в потоках
    def run(self, username='', password=''):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #conn
        try:
            self.socket.connect(self.server_address)
        except TimeoutError:
            print('timeout error')
        except ConnectionRefusedError:
            print('connection refused, socket problem')

        # encryption dialog start
        public_key_binary = self.socket.recv(1024)
        self.cipher_rsa = encryption.generate_cipher_rsa(public_key_binary)

        #threads start
        self.reciever_thread = MessageReceiver(self, self.socket)
        self.reciever_thread.start()
        self.sender_thread = MessageSender(self.socket)
        self.sender_thread.start()

        self.session_key = b'Sixteen byte key'
        session_key_encrypted = encryption.generate_session_key(self.cipher_rsa, self.session_key)

        auth_message = msg.MessageAuthenticate(username, password)
        auth_bmessage = auth_message.get_binary_json('utf-8')
        auth_message_encrypted = encryption.encrypt(encryption.padding_text(auth_bmessage), self.session_key)
        self.sender_thread.send_queue.put(session_key_encrypted + auth_message_encrypted)

    def send(self, message):
        bmessage = message.get_binary_json('utf-8')
        encrypted_message = encryption.encrypt(encryption.padding_text(bmessage), self.session_key)
        self.sender_thread.send_queue.put(encrypted_message)

    # разрыв соединения
    def disconnect(self):
        self.reciever_thread.stop = True
        self.sender_thread.stop = True
        self.socket.close()
        self.session_key_recieved_by_server=False

    def new_message(self):
        encrypted_message = self.reciever_thread.recieved_queue.get()
        bmessage = encryption.decrypt(encrypted_message, self.session_key)
        message = msg.GeneralMessage()
        message.make_from_binary_json(bmessage, 'utf-8')
        self.listener.new_message(message)



