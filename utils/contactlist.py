

class Contact(object):
    def __init__(self, name, fullname, online=False):
        self.name = name
        self.fullname = fullname
        self.new = 0
        self.online = online

    def __str__(self):
        return '{} ({}) ({})'.format(self.name, self.fullname, 'online' if self.online else 'offline' )

class ContactList(object):
    def __init__(self):
        self.contacts_name = []
        self.contacts = []

    def add(self, contact):
        if isinstance(contact, Contact):
            if contact.name not in self.contacts_name:
                self.contacts.append(contact)
                self.contacts_name.append(contact.name)

    def delete_contact_by_name(self, name):
        index = self.get_index_for_name(name)
        if index >= 0:
            self.contacts_name.pop(index)
            self.contacts.pop(index)
            return 0
        else:
            return -1

    def get_index_for_name(self, name):
        if name in self.contacts_name:
            index = self.contacts_name.index(name)
            return index
        else:
            return -1

    def clear(self):
        self.contacts = []
        self.contacts_name = []

    def count(self):
        return len(self.contacts)