

import os.path
import sys
import hmac
from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import datetime
from pathlib import Path

import sky_client.client as client
import sky_client.utils.contactlist as clst, sky_client.utils.message as msg
import sky_client.database.database_client as dbc
import sky_client.utils.conf as conf

# from utils import singleton
# import client as client
# import utils.contactlist as clst, sky_message.utils.message as msg
# import database.database_client as dbc
# import utils.conf as conf


HOSTNAME = 'localhost'
PORT = 8888
PATH_GUI = os.path.join(os.path.dirname(__file__), 'client_gui.ui')
PATH_AUTHGUI = os.path.join(os.path.dirname(__file__), 'auth2.ui')
PATH_ONLINE_PNG = os.path.join(os.path.dirname(__file__), 'utils', 'on.png')
PATH_OFFLINE_PNG = os.path.join(os.path.dirname(__file__), 'utils', 'off.png')
PATH_DB = str(Path.home())

class StandardItemContact(QtGui.QStandardItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setData(self, Any, role=None, *args, **kwargs):
        super().setData(Any, role, *args, **kwargs)

class StandardItemMessage(QtGui.QStandardItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setData(self, Any, role=None, *args, **kwargs):
        super().setData(Any, role, *args, **kwargs)

class StandardItemModelContacts(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_online = QtGui.QIcon(PATH_ONLINE_PNG)
        self.icon_offline = QtGui.QIcon(PATH_OFFLINE_PNG)

    def make_item(self, contact):
        item = StandardItemContact()
        if contact.new > 0:
            secont_part = " [New: {}]".format(contact.new)
        else:
            secont_part = ""
        item.setData(contact.name + secont_part, role=QtCore.Qt.DisplayRole)
        if contact.online:
            color = QtCore.Qt.black
            icon = QtGui.QIcon(self.icon_online)
        else:
            color = QtCore.Qt.darkGray
            icon = QtGui.QIcon(self.icon_offline)
        brush = QtGui.QBrush(color)
        item.setData(brush, role=QtCore.Qt.TextColorRole)
        item.setData(icon, role=QtCore.Qt.DecorationRole)
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
        self.setData(index, contact.name + secont_part, role=QtCore.Qt.DisplayRole)
        if contact.online:
            color = QtCore.Qt.black
            icon = QtGui.QIcon(self.icon_online)
        else:
            color = QtCore.Qt.darkGray
            icon = QtGui.QIcon(self.icon_offline)
        brush = QtGui.QBrush(color)
        self.setData(index, brush, role=QtCore.Qt.TextColorRole)
        self.setData(index, icon, role=QtCore.Qt.DecorationRole)


class StandardItemModelMessages(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def make_item(self, message, name):
        item = StandardItemMessage()
        if isinstance(message, dbc.Message):
            reply = message.reply
            color_gray = QtGui.QColor()
            color_gray.setRgb(128, 128, 128, 64)
            color_blue = QtGui.QColor()
            color_blue.setRgb(0, 0, 128, 64)
            sender = 'me' if reply else name
            orientation = QtCore.Qt.AlignRight if reply else QtCore.Qt.AlignLeft
            color = color_gray if reply else color_blue
            text = message.text
            time = message.time
            fullmessage = '{} [{}]:\n{}\n'.format(sender, time, text)
            brush = QtGui.QBrush(color)
            item = QtGui.QStandardItem()
            item.setData(fullmessage, role=QtCore.Qt.DisplayRole)
            item.setData(orientation, role=QtCore.Qt.TextAlignmentRole)
            item.setData(brush, role=QtCore.Qt.BackgroundRole)
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


class ClientController(QtCore.QObject):

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
        self.update_contact_list_flag = False
        self.expected_contacts_count = 0

    def user_disconnect(self):
        self.client.disconnect()
        self.authenticated = False
        self.waiting_contact_list_flag = False
        self.update_contact_list_flag = False
        self.expected_contacts_count = 0

    def new_message(self, recieved_message):
        # print(recieved_message)
        # parse recieved message
        if 'response' in recieved_message.msg:
            response_code = recieved_message['response']
            message_text = recieved_message['alert']

            if not self.authenticated:
                if response_code == 200:
                    self.authenticated = True
                    self.auth_recieved.emit(True)
                else:
                    self.auth_recieved.emit(False)

            elif self.waiting_contact_list_flag:
                if recieved_message['response'] == 202:
                    self.expected_contacts_count = int(recieved_message['alert'])
                    self.waiting_contact_list_flag = False
                if recieved_message['response'] == 203:
                    if recieved_message['alert'] == 'contact_add_ok':
                        self.expected_contacts_count = 1
                        self.waiting_contact_list_flag = False
                    elif recieved_message['alert'] == 'contact_add_error':
                        pass
                    elif recieved_message['alert'] == 'contact_delete_ok':
                        deleted_contact = recieved_message['contact']
                        self.model.delete(deleted_contact)
                        # self.update_contact_list_flag = True
                    elif recieved_message['alert'] == 'contact_delete_error':
                        pass
            #сохраняем сообщение
            # self.model.server_messages.append(recieved_message)
        else:
            converted_message = msg.Message()
            converted_message.msg = recieved_message.msg
            if converted_message['action'] == 'personal_message':
                sender = converted_message['src']
                text = converted_message['text']
                # self.model.new_message_increase(sender, True)
                session = self.model.db.Session()
                self.model.db.add_message(session, sender, text, datetime.datetime.now(), reply=False)
                session.close()
                self.gotPersonal.emit(sender)
            elif converted_message['action'] == 'contact_list':
                if self.expected_contacts_count > 0:
                    contact_name = converted_message['username']
                    contact_fullname = converted_message['name']
                    contact_online = converted_message['online']
                    contact = clst.Contact(contact_name, contact_fullname, contact_online)
                    self.model.add(contact)
                    self.expected_contacts_count -= 1
            elif converted_message['action'] == 'contact_online':
                self.model.set_online(converted_message['contact'], True)
            elif converted_message['action'] == 'contact_offline':
                self.model.set_online(converted_message['contact'], False)

        #signal - slot

        # if self.update_contact_list_flag:
        #     self.update_contact_list()
        #     self.update_contact_list_flag = False

        # if sender == 'server':
        #     message_str = 'Server: {time}: {text}\n'.format(sender = sender, time=recieved_message['time'],
        #                                                          text=text)
        #     self.gotMessage.emit(message_str)
        # else:
        #     self.gotPersonal.emit(sender)

    def run_client(self):
        self.client = client.Client(self.model.host, self.model.port)
        self.client.listener = self
        self.client.run(self.model.username, self.model.encripted_password)

    # def authenticate(self):
    #     auth_msg = msg.MessageAuthenticate(self.model.username, self.model.encripted_password)
    #     self.client.send(auth_msg)

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
        self.model.db.add_message(session, contact, text, datetime.datetime.now(), reply=True)
        session.close()


class AuthDialog(QtWidgets.QDialog):
    def __init__(self, model, username, hostname, port, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        uic.loadUi(os.path.join(PATH_AUTHGUI), self)
        self.model = model
        self.usernameLineEdit.setText(username)
        self.lineEditHost.setText(hostname)
        self.lineEditPort.setText(port)

    def accept(self):
        self.model.username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()
        self.model.host = self.lineEditHost.text()
        self.model.port = int(self.lineEditPort.text())
        secret_key = b'i_believe_i_can_fly'
        hash = hmac.new(secret_key, password.encode('utf-8'))
        digest = hash.hexdigest()
        self.model.encripted_password = digest
        super().accept()


class ClientWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        #set up GUI
        uic.loadUi(PATH_GUI, self)
        self.checkBoxConnect.stateChanged.connect(self.connect_disconnect)
        self.btnAddContact.clicked.connect(self.add_contact)
        self.btnDeleteContact.clicked.connect(self.delete_contact)
        self.btnSend.clicked.connect(self.send_message)
        self.listViewContacts.clicked.connect(self.select_contact)

        # model -controller - view
        self.contact_list_model = StandardItemModelContacts(self)
        self.messages_list_model = StandardItemModelMessages(self)
        self.model = ClientModel(self.contact_list_model, self.messages_list_model)
        self.listViewContacts.setModel(self.contact_list_model)
        self.listViewMessages.setModel(self.messages_list_model)
        self.controller = ClientController(self.model)

        #signal-slot
        self.controller.auth_recieved.connect(self.authentification_recieved)
        self.controller.gotPersonal.connect(self.new_personal_message)

        #not connected
        self.connected = False
        # nobody selected
        self.currently_selected = ''

    # @pyqtSlot(int)
    # def move_list_view_messages_bottom(self):
    #     print(self.listViewMessages.verticalScrollBar().value(), self.listViewMessages.verticalScrollBar().maximum())
    #     self.listViewMessages.verticalScrollBar().setSliderPosition(self.listViewMessages.verticalScrollBar().maximum())
    #

    def connect_disconnect(self):
        self.checkBoxConnect.setEnabled(False)
        if self.checkBoxConnect.isChecked():
            self.authentification()
        else:
            self.user_disconnect()
            self.checkBoxConnect.setEnabled(True)

    # Log in  dialog
    def authentification(self):
        #read config file
        d = conf.read_conf()
        #show Authorization dialog
        auth_dialog = AuthDialog(self.model, d['username'], d['hostname'], d['port'], parent=self)
        auth_dialog.accepted.connect(self.auth_dialog_accepted)
        auth_dialog.rejected.connect(self.auth_dialog_rejected)
        auth_dialog.show()

    def auth_dialog_accepted(self):
        self.checkBoxConnect.setEnabled(True)
        self.controller.run_client()

    def auth_dialog_rejected(self):
        self.checkBoxConnect.setChecked(False)
        self.checkBoxConnect.setEnabled(True)

    @pyqtSlot(bool)
    def authentification_recieved(self, ok):
        if ok:
            self.connected = True
            self.checkBoxConnect.setText('Connected')
            self.labelUsername.setText('{}:'.format(self.model.username))
            self.model.contactlist.clear()
            self.model.personal_messages = []
            self.model.server_messages = []
            self.model.sent_messages = []
            self.model.open_db()
            self.controller.ask_contact_list()
        else:
            self.checkBoxConnect.setChecked(False)

    def user_disconnect(self):
        if self.connected:
            conf.save_conf(username=self.model.username, hostname=self.model.host, port=str(self.model.port))
            self.model.clear_data()
            self.controller.user_disconnect()
            self.lineEditAddContact.setText('')
            self.labelUsername.setText('')
            self.checkBoxConnect.setText('Connect')
            self.connected = False
            self.currently_selected = ''

    @pyqtSlot(str)
    def get_contact_list(self):
        pass

    def add_contact(self):
        name = self.lineEditAddContact.text()
        if name != '':
            self.controller.add_contact(name)
            self.lineEditAddContact.setText('')

    def delete_contact(self):
        name = self.lineEditAddContact.text()
        if name != '':
            self.controller.delete_contact(name)
            self.lineEditAddContact.setText('')

    def send_message(self):
        sel_list = self.listViewContacts.selectionModel().selectedIndexes()
        if len(sel_list) > 0:
            contact = self.model.contactlist.contacts[sel_list[0].row()]
            self.controller.personal_message(contact.name, self.textEditMessage.toPlainText())
            self.textEditMessage.clear()
            self.model.update_messages_for_contact(contact.name)
        else:
            pass

    @pyqtSlot(QtCore.QModelIndex)
    def select_contact(self, modelindex):
        item = self.contact_list_model.data(modelindex, role=QtCore.Qt.DisplayRole)
        contact_name = self.model.contactlist.contacts_name[modelindex.row()]
        self.lineEditAddContact.setText(contact_name)
        self.show_messages_for_contact(contact_name)
        self.listViewContacts.setCurrentIndex(modelindex)
        self.currently_selected = contact_name

    @pyqtSlot(str)
    def new_personal_message(self, sender):
        self.model.new_message_increase(sender, True)
        # sel_list = self.listViewContacts.selectionModel().selectedIndexes()
        if sender == self.currently_selected:
            self.show_messages_for_contact(self.currently_selected)


    @pyqtSlot(str)
    def show_messages_for_contact(self, contact_name):
        self.model.update_messages_for_contact(contact_name)
        self.model.new_message_increase(contact_name, False)
        self.listViewMessages.scrollToBottom()
        # print()
        # print(self.listViewMessages.verticalScrollBar().minimum())

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

