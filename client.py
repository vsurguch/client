import queue
import socket
import threading as th
import utils.encryption as encryption
import utils.message2 as msg
from utils.conf import get_path

# import sky_client.utils.encryption as encryption
# import sky_client.utils.message2 as msg
# from sky_client.utils.conf import get_path

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
        print('run')
        while not self.stop:
            try:
                #вставить Lock
                bl = self.socket.recv(4)
                leng = int.from_bytes(bl, 'big')
                message = b''
                left_to_read = leng
                while left_to_read != 0:
                    to_read = 4096 if left_to_read > 4096 else left_to_read
                    data = self.socket.recv(to_read)
                    message += data
                    left_to_read -= len(data)

                print('message recieved ok') if leng == len(message) else print('incomplete message recived')

                # while leng > 4096:
                #     data += self.socket.recv(4096)
                #     leng -= 4096
                # data += self.socket.recv(leng)
                if not message:
                    break
                else:
                    self.recieved_queue.put(message)
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
                l = len(message)
                bl = l.to_bytes(4, 'big')
                self.socket.sendall(bl + message)


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
        self.session_key_encrypted = encryption.generate_session_key(self.cipher_rsa, self.session_key)

    def send_auth_data(self, auth_message):
        auth_bmessage = auth_message.get_binary_json('utf-8')
        auth_message_encrypted = encryption.encrypt(auth_bmessage, self.session_key)
        self.sender_thread.send_queue.put(self.session_key_encrypted + auth_message_encrypted)

    def send(self, message):
        bmessage = message.get_binary_json('utf-8')
        encrypted_message = encryption.encrypt(bmessage, self.session_key)
        self.sender_thread.send_queue.put(encrypted_message)

    def send_file(self, encrypted_data):
        self.sender_thread.send_queue.put(encrypted_data)

    # разрыв соединения
    def disconnect(self):
        self.reciever_thread.stop = True
        self.sender_thread.stop = True
        self.socket.close()
        self.session_key_recieved_by_server=False

    def new_message(self):
        encrypted_data = self.reciever_thread.recieved_queue.get()
        if self.listener.waiting_file_flag:
            print(self.listener.file_data.name)
            file_path = get_path(self.listener.file_data.name)
            encryption.decrypt_file(encrypted_data, self.session_key, file_path)
            self.listener.new_file_recieved(file_path)
        else:
            bmessage = encryption.decrypt(encrypted_data, self.session_key)
            message = msg.GeneralMessage()
            message.make_from_binary_json(bmessage, 'utf-8')
            self.listener.new_message(message)



