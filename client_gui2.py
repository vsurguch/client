
import os.path
import sys
import hmac
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QGridLayout, \
    QListView, QPlainTextEdit, QFileDialog, \
    QPushButton, QLabel, QLineEdit, QCheckBox, QHBoxLayout, QFrame, QDialog, QVBoxLayout, \
        QDialogButtonBox, QLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QModelIndex, Qt, QMimeData, QSize
from client_controller import StandardItemModelContacts, StandardItemModelMessages, ClientModel, ClientController
from utils import conf

PATH_AUTHGUI = os.path.join(os.path.dirname(__file__), 'auth2.ui')

class MessageField(QPlainTextEdit):
    drop = pyqtSignal(QMimeData)

    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        self.setAcceptDrops(True)
        self.file = ''

    def dropEvent(self, ev):
        # self.drop.emit(ev.mimeData())
        self.file = ev.mimeData().text()[8:]
        t = ' <file to send: ' + self.file + '> '
        self.appendPlainText(t)


class AuthDialog(QDialog):
    def __init__(self, model, username, hostname, port, parent=None):
        QDialog.__init__(self, parent)
        self.buttonBox = QDialogButtonBox(Qt.Vertical)
        self.buttonBox.addButton('Ok', QDialogButtonBox.ActionRole)
        self.buttonBox.addButton('Cancel', QDialogButtonBox.ActionRole)
        self.buttonBox.addButton('More', QDialogButtonBox.ActionRole)

        # self.buttonBox.accepted.connect(self.accept)
        # self.buttonBox.rejected.connect(self.reject)

        self.topLeft = QFrame()
        topLayout = QGridLayout()
        usernameLabel = QLabel('Username')
        self.username = QLineEdit(username)
        usernameLabel.setBuddy(self.username)
        passwordLabel = QLabel('Password')
        self.password = QLineEdit()
        passwordLabel.setBuddy(self.password)
        topLayout.addWidget(usernameLabel, 0, 0)
        topLayout.addWidget(self.username, 0, 1)
        topLayout.addWidget(passwordLabel, 1, 0)
        topLayout.addWidget(self.password, 1, 1)
        topLayout.setRowMinimumHeight(2, 20)
        self.topLeft.setLayout(topLayout)

        self.extension = QFrame()
        extensionLaytout = QVBoxLayout()
        self.hostLabel = QLabel('Host')
        self.host = QLineEdit(hostname)
        self.portLabel = QLabel('Port')
        self.port = QLineEdit(port)
        extensionLaytout.addWidget(self.hostLabel)
        extensionLaytout.addWidget(self.host)
        extensionLaytout.addWidget(self.portLabel)
        extensionLaytout.addWidget(self.port)
        extensionLaytout.addWidget(self.buttonBox)
        self.extension.setLayout(extensionLaytout)

        mainLayout = QGridLayout()
        mainLayout.setSizeConstraint(QLayout.SetFixedSize)
        mainLayout.addWidget(self.topLeft, 0, 0, alignment=Qt.AlignBottom)
        mainLayout.addWidget(self.buttonBox, 0, 1, alignment=Qt.AlignVCenter)
        mainLayout.addWidget(self.extension, 1, 0, 1, 2)
        # mainLayout.setRowMinimumHeight(0, 80)
        mainLayout.setRowStretch(2, 1)
        self.buttonBox.buttons()[0].clicked.connect(self.accept)
        self.buttonBox.buttons()[1].clicked.connect(self.reject)
        self.buttonBox.buttons()[2].setCheckable(True)
        self.buttonBox.buttons()[2].toggled.connect(self.extension.setVisible)

        self.extension.hide()
        self.setLayout(mainLayout)

        self.model = model
        self.show_all = False

    def accept(self):
        self.model.username = self.username.text()
        password = self.password.text()
        self.model.host = self.host.text()
        self.model.port = int(self.port.text())
        secret_key = b'i_believe_i_can_fly'
        hash = hmac.new(secret_key, password.encode('utf-8'))
        digest = hash.hexdigest()
        self.model.encripted_password = digest
        super().accept()

    def show_more(self):
        if not self.show_all:
            self.extension.setVisible(True)

            # self.hostLabel.setVisible(True)
            # self.host.setVisible(True)
            # self.portLabel.setVisible(True)
            # self.port.setVisible(True)
            self.more.setText('Less - >')
            self.show_all = True
        else:
            # self.hostLabel.setVisible(False)
            # self.host.setVisible(False)
            # self.portLabel.setVisible(False)
            # self.port.setVisible(False)
            self.extension.hide()
            self.extension.setParent(None)
            self.more.setText('More - >')
            self.show_all = False



class AppWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setGeometry(100, 100, 550, 400)
        self.setUpMenu()
        self.setUpLayout()
        self.checkBoxConnect.stateChanged.connect(self.connect_disconnect)
        self.addButton.clicked.connect(self.add_contact)
        self.deleteButton.clicked.connect(self.delete_contact)
        self.sendButton.clicked.connect(self.send_message)
        self.contactsList.clicked.connect(self.select_contact)
        # self.messageField.drop.connect(self.add_file_to_message)

        # model -controller - view
        self.contact_list_model = StandardItemModelContacts(self)
        self.messages_list_model = StandardItemModelMessages(self)
        self.model = ClientModel(self.contact_list_model, self.messages_list_model)
        self.contactsList.setModel(self.contact_list_model)
        self.messagesList.setModel(self.messages_list_model)
        self.controller = ClientController(self.model)

        # signal-slot
        self.controller.auth_recieved.connect(self.authentification_recieved)
        self.controller.gotPersonal.connect(self.new_personal_message)

        # not connected
        self.connected = False
        # nobody selected
        self.currently_selected = ''

    def setUpMenu(self):
        fileMenu = self.menuBar().addMenu('File')
        quitAct = QAction('Quit', self)
        quitAct.triggered.connect(self.doQuit)
        fileMenu.addAction(quitAct)
        sendMenu = self.menuBar().addMenu('Send')
        sendFile = QAction('Send File', self)
        sendFile.triggered.connect(self.doSendFile)
        sendMenu.addAction(sendFile)

    def setUpLayout(self):
        hBoxLayout = QHBoxLayout()
        mainFrame = QFrame()
        mainFrame.setLayout(hBoxLayout)

        self.contact = QLineEdit()
        self.contact.setFont(QFont('Calibri', 14))
        self.contact.setPlaceholderText('Add Contact Here')
        self.contact.setMinimumHeight(30)
        self.contact.setMaximumHeight(30)

        self.addButton = QPushButton('+')
        self.addButton.setMinimumHeight(30)
        self.addButton.setMaximumHeight(30)
        self.addButton.setMinimumWidth(30)
        self.addButton.setMaximumWidth(30)

        self.deleteButton = QPushButton('-')
        self.deleteButton.setMinimumHeight(30)
        self.deleteButton.setMaximumHeight(30)
        self.deleteButton.setMinimumWidth(30)
        self.deleteButton.setMaximumWidth(30)

        self.contactsList = QListView()
        self.contactsList.setFrameShape(QFrame.Box)

        spacer = QFrame()
        spacer.setMaximumWidth(5)

        self.nameLabel = QLabel('Username')
        self.nameLabel.setMinimumHeight(30)
        self.nameLabel.setMaximumHeight(30)
        self.nameLabel.setFont(QFont('Calibri', 14))
        self.checkBoxConnect = QCheckBox()
        self.checkBoxConnect.setText('Connect')
        self.checkBoxConnect.setChecked(False)
        self.checkBoxConnect.setMaximumHeight(30)
        self.checkBoxConnect.setMinimumHeight(30)
        self.checkBoxConnect.setMaximumWidth(70)
        self.checkBoxConnect.setMinimumWidth(70)

        self.messagesList = QListView()
        self.messagesList.setIconSize(QSize(30, 30))
        self.messagesList.setFrameShape(QFrame.Box)
        self.messageField = MessageField()
        self.messageField.setMinimumHeight(50)
        self.messageField.setMaximumHeight(50)
        self.sendButton = QPushButton()
        self.sendButton.setText('>>')
        self.sendButton.setMinimumHeight(50)
        self.sendButton.setMaximumHeight(50)
        self.sendButton.setMinimumWidth(50)
        self.sendButton.setMaximumWidth(50)

        contBox = QGridLayout()
        contBox.addWidget(self.contact, 0, 0)
        contBox.addWidget(self.addButton, 0, 1)
        contBox.addWidget(self.deleteButton, 0, 2)
        contBox.addWidget(self.contactsList, 1, 0, 2, 3)
        contBox.addWidget(spacer, 0, 3, 3, 1)
        contBox.addWidget(self.nameLabel, 0, 4)
        contBox.addWidget(self.checkBoxConnect, 0, 5, 1, 2)
        contBox.addWidget(self.messagesList, 1, 4, 1, 3)
        contBox.addWidget(self.messageField, 2, 4, 1, 2)
        contBox.addWidget(self.sendButton, 2, 6)
        contBox.setColumnStretch(0, 3)
        contBox.setColumnStretch(4, 6)
        groupBoxCont = QFrame()
        groupBoxCont.setLayout(contBox)

        self.setCentralWidget(groupBoxCont)

    def doQuit(self):
        self.close()

    def doSendFile(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]
        self.messageField.file = filename
        self.messageField.appendPlainText(filename)

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
            self.nameLabel.setText('{}:'.format(self.model.username))
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
            self.contact.setText('')
            self.nameLabel.setText('')
            self.checkBoxConnect.setText('Connect')
            self.connected = False
            self.currently_selected = ''

    @pyqtSlot(str)
    def get_contact_list(self):
        pass

    def add_contact(self):
        name = self.contact.text()
        if name != '':
            self.controller.add_contact(name)
            self.contact.setText('')

    def delete_contact(self):
        name = self.contact.text()
        if name != '':
            self.controller.delete_contact(name)
            self.contact.setText('')

    @pyqtSlot(QMimeData)
    def add_file_to_message(self, mime):
        self.messageField.setPlainText(mime.text())

    def send_message(self):
        sel_list = self.contactsList.selectionModel().selectedIndexes()
        if len(sel_list) > 0:
            contact = self.model.contactlist.contacts[sel_list[0].row()]
            if self.messageField.file != '':
                self.controller.send_file(contact.name, self.messageField.file)
                self.messageField.file = ''
            else:
                self.controller.personal_message(contact.name, self.messageField.toPlainText())
            self.messageField.clear()
            self.model.update_messages_for_contact(contact.name)
        else:
            pass

    @pyqtSlot(QModelIndex)
    def select_contact(self, modelindex):
        item = self.contact_list_model.data(modelindex, role=Qt.DisplayRole)
        contact_name = self.model.contactlist.contacts_name[modelindex.row()]
        self.contact.setText(contact_name)
        self.show_messages_for_contact(contact_name)
        self.contactsList.setCurrentIndex(modelindex)
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
        self.messagesList.scrollToBottom()


def main():
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
