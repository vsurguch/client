import os.path
import sys
import hmac
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIcon, QBrush, QColor, QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QModelIndex, Qt, QObject
import datetime
from pathlib import Path

# import sky_client.client as client
# import sky_client.utils.contactlist as clst, sky_client.utils.message2 as msg
# import sky_client.utils.encryption as encryption
# import sky_client.database.database_client as dbc
# import sky_client.utils.conf as conf

import client as client
import utils.contactlist as clst, utils.message2 as msg
import utils.encryption as encryption
import database.database_client as dbc
import utils.conf as conf


HOSTNAME = 'localhost'
PORT = 8888
PATH_ONLINE_PNG = os.path.join(os.path.dirname(__file__), 'utils', 'on.png')
PATH_OFFLINE_PNG = os.path.join(os.path.dirname(__file__), 'utils', 'off.png')
PATH_DB = str(Path.home())


class StandardItemContact(QStandardItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setData(self, Any, role=None, *args, **kwargs):
        super().setData(Any, role, *args, **kwargs)

class StandardItemMessage(QStandardItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setData(self, Any, role=None, *args, **kwargs):
        super().setData(Any, role, *args, **kwargs)

class StandardItemModelContacts(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_online = QIcon(PATH_ONLINE_PNG)
        self.icon_offline = QIcon(PATH_OFFLINE_PNG)

    def make_item(self, contact):
        item = StandardItemContact()
        if contact.new > 0:
            secont_part = " [New: {}]".format(contact.new)
        else:
            secont_part = ""
        item.setData(contact.name + secont_part, role=Qt.DisplayRole)
        if contact.online:
            color = Qt.black
            icon = QIcon(self.icon_online)
        else:
            color = Qt.darkGray
            icon = QIcon(self.icon_offline)
        brush = QBrush(color)
        item.setData(brush, role=Qt.TextColorRole)
        item.setData(icon, role=Qt.DecorationRole)
        return item

    def add_item(self, contact):
        new_item = self.make_item(contact)
        self.appendRow(new_item)

    def delete_item(self, row):
        self.removeRow(row)

    def update_item(self, row, contact):
        index = self.index(row, 0)
        if contact.new > 0:
            secont_part = " [New: {}]".format(contact.new)
        else:
            secont_part = ""
        self.setData(index, contact.name + secont_part, role=Qt.DisplayRole)
        if contact.online:
            color = Qt.black
            icon = QIcon(self.icon_online)
        else:
            color = Qt.darkGray
            icon = QIcon(self.icon_offline)
        brush = QBrush(color)
        self.setData(index, brush, role=Qt.TextColorRole)
        self.setData(index, icon, role=Qt.DecorationRole)


class StandardItemModelMessages(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item(self, message, name):
        item = StandardItemMessage()
        if isinstance(message, dbc.Message):
            reply = message.reply
            file = message.file
            icon = None
            if os.path.exists(file):
                extension = os.path.splitext(file)[-1]
                if (extension == '.jpg') or (extension == '.png'):
                    icon = QIcon(file)
            color_gray = QColor()
            color_gray.setRgb(128, 128, 128, 64)
            color_blue = QColor()
            color_blue.setRgb(0, 0, 128, 64)
            sender = 'me' if reply else name
            orientation = Qt.AlignRight if reply else Qt.AlignLeft
            color = color_gray if reply else color_blue
            text = message.text
            time = message.time
            fullmessage = '{} [{}]:\n{}\n'.format(sender, time, text)
            brush = QBrush(color)
            if icon is not None:
                item.setIcon(icon)
            item.setData(fullmessage, role=Qt.DisplayRole)
            item.setData(orientation, role=Qt.TextAlignmentRole)
            item.setData(brush, role=Qt.BackgroundRole)
        return item

    def add_item(self, message, name):
        new_item = self.make_item(message, name)
        self.appendRow(new_item)


class ClientModel():
    def __init__(self, contact_list_model, messages_list_model):
        self.username = ''
        self.encripted_password = ''
        self.host = ''
        self.port = 0
        self.contactlist = clst.ContactList()
        self.contact_list_model = contact_list_model
        self.messages_list_model = messages_list_model
        self.messages_list_for_contact = []
        self.server_messages = []
        self.expected_contacts_count = 0
        self.update_contact_list_flag = False
        self.db = dbc.ClientDatabase()
        self.db_ready = False

    def open_db(self):
        self.db.open(os.path.join(PATH_DB, conf.FOLDER_NAME, self.username))
        self.db_ready = True

    def clear_data(self):
        self.contact_list_model.clear()
        self.messages_list_model.clear()
        self.messages_list_for_contact = []
        self.contactlist.clear()

    def add(self, contact):
        if isinstance(contact, clst.Contact):
            self.contactlist.add(contact)
            session = self.db.Session()
            self.db.add_contact_by_fields(session, contact.name, contact.fullname)
            session.close()
            self.contact_list_model.add_item(contact)

    def delete(self, name):
        #delete from database
        session = self.db.Session()
        self.db.delete_contact(session, name)
        session.close()
        #delete from listViewModel
        index = self.contactlist.get_index_for_name(name)
        self.contact_list_model.delete_item(index)
        #delete from contact_list
        result = self.contactlist.delete_contact_by_name(name)

    def set_online(self, name, online):
        row = self.contactlist.get_index_for_name(name)
        contact = self.contactlist.contacts[row]
        contact.online = online
        self.contact_list_model.update_item(row, contact)

    def new_message_increase(self, name, increase):
        row = self.contactlist.get_index_for_name(name)
        contact = self.contactlist.contacts[row]
        if not increase:
            contact.new = 0
        else:
            contact.new += 1
        self.contact_list_model.update_item(row, contact)

    def update_messages_for_contact(self, name):
        if self.db_ready:
            session = self.db.Session()
            messages = self.db.get_messages_for_contact(session, name)
            session.close()
            notread = len(messages) - len(self.messages_list_for_contact)
            if notread > 0:
                for message in messages[-notread:]:
                    self.messages_list_model.add_item(message, name)
                    self.messages_list_for_contact.append(message)


class ClientController(QObject):

    auth_recieved = pyqtSignal(bool)
    gotMessage = pyqtSignal(str)
    gotPersonal = pyqtSignal(str)
    sentMessaage = pyqtSignal(str)
    updateContacts = pyqtSignal(str)
    moveBottom = pyqtSignal(int)
    finished = pyqtSignal(int)

    def __init__(self, model):
        super().__init__()
        self.model = model
        #initializatin flags
        self.authenticated = False
        self.waiting_contact_list_flag = False
        self.waiting_file_flag = False
        self.update_contact_list_flag = False
        self.expected_contacts_count = 0
        self.file_data = None

    def user_disconnect(self):
        self.client.disconnect()
        self.authenticated = False
        self.waiting_contact_list_flag = False
        self.update_contact_list_flag = False
        self.expected_contacts_count = 0

    def new_message(self, recieved_message):
        # handlers
        def auth_response_ok():
            if not self.authenticated:
                self.authenticated = True
                self.auth_recieved.emit(True)

        def auth_response_error():
            self.auth_recieved.emit(False)

        def contact_list_recieved():
            if self.waiting_contact_list_flag:
                self.expected_contacts_count = int(recieved_message.alert)
                self.waiting_contact_list_flag = False

        def contact_add_ok():
            if self.waiting_contact_list_flag:
                self.expected_contacts_count = 1
                self.waiting_contact_list_flag = False

        def contact_delete_ok():
            deleted_contact = recieved_message.alert
            self.model.delete(deleted_contact)

        def personal_message_action():
            sender = recieved_message.src
            text = recieved_message.text
            # self.model.new_message_increase(sender, True)
            session = self.model.db.Session()
            self.model.db.add_message(session, sender, text, datetime.datetime.now(), '', reply=False)
            session.close()
            self.gotPersonal.emit(sender)

        def contact_list_action():
            contact_name = recieved_message.username
            contact_fullname = recieved_message.name
            contact_online = recieved_message.online
            contact = clst.Contact(contact_name, contact_fullname, contact_online)
            self.model.add(contact)
            self.expected_contacts_count -= 1

        def contact_online_action():
            self.model.set_online(recieved_message.contact, True)

        def contact_offline_action():
            self.model.set_online(recieved_message.contact, False)

        def wait_for_file():
            self.file_data = msg.File_data(recieved_message.name, recieved_message.filelength,
                                           recieved_message.src, recieved_message.dest)
            self.waiting_file_flag = True

        process_responses_dict = {
            200: auth_response_ok,
            402: auth_response_error,
            202: contact_list_recieved,
            205: contact_add_ok,
            206: contact_delete_ok,
            # 405: contact_add_error,
            # 406: contact_delete_error,
        }
        process_actions_dict = {
            'personal_message': personal_message_action,
            'contact_list': contact_list_action,
            'contact_online': contact_online_action,
            'contact_offline': contact_offline_action,
            'send_file': wait_for_file
        }

        # read response and do action
        if recieved_message.isResponse():
            response_code = recieved_message.response
            if response_code in process_responses_dict:
                process_responses_dict[response_code]()
            else:
                return
            #сохраняем сообщение
            # self.model.server_messages.append(recieved_message)

        elif recieved_message.isAction():
            action = recieved_message.action
            if action in process_actions_dict:
                process_actions_dict[action]()
            else:
                return

    def new_file_recieved(self, filepath):
        sender = self.file_data.src
        # self.model.new_message_increase(sender, True)
        session = self.model.db.Session()
        self.model.db.add_message(session, sender, filepath, datetime.datetime.now(), filepath, reply=False)
        session.close()
        self.gotPersonal.emit(sender)
        self.file_data = None
        self.waiting_file_flag = False

    def run_client(self):
        self.client = client.Client(self.model.host, self.model.port)
        self.client.listener = self
        self.client.run(self.model.username, self.model.encripted_password)
        self.authenticate()

    def authenticate(self):
        auth_message = msg.MessageAuthenticate(self.model.username, self.model.encripted_password)
        self.client.send_auth_data(auth_message)

    def ask_contact_list(self):
        self.waiting_contact_list_flag = True
        request_msg = msg.MessageGetContacts(self.model.username)
        self.client.send(request_msg)

    def add_contact(self, name):
        self.waiting_contact_list_flag = True
        message = msg.MessageAddContact(self.model.username, name)
        self.client.send(message)

    def delete_contact(self, name):
        self.waiting_contact_list_flag = True
        message = msg.MessageDeleteContact(self.model.username, name)
        self.client.send(message)

    def personal_message(self, contact, text):
        message = msg.MessagePersonal(self.model.username, contact, text)
        self.client.send(message)
        session = self.model.db.Session()
        self.model.db.add_message(session, contact, text, datetime.datetime.now(), filename='', reply=True)
        session.close()

    def send_file(self, contact, filename):
        encrypted_file = encryption.encrypt_file(filename, self.client.session_key)
        encrypted_file_length = len(encrypted_file)
        message = msg.MessageSendFile(os.path.basename(filename), encrypted_file_length, self.model.username, contact)
        self.client.send(message)
        self.client.send_file(encrypted_file)
        session = self.model.db.Session()
        self.model.db.add_message(session, contact, filename, datetime.datetime.now(), filename, reply=True)
        session.close()
