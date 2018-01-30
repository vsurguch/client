
import sqlalchemy as sql
import sqlalchemy.orm as orm
import sqlalchemy.ext.declarative as declarative

DeclarativeBase = declarative.declarative_base()

class Contact(DeclarativeBase):
    __tablename__ = 'Contacts'

    id = sql.Column('id', sql.Integer, primary_key=True)
    name = sql.Column('name', sql.String)
    fullname = sql.Column('fullname', sql.String)
    messages = orm.relationship("Message", backref=orm.backref('contact'))

    def __init__(self, contact_name, fullname):
        self.name = contact_name
        self.fullname = fullname

    def __repr__(self):
        return '<Contact: {} ({})>'.format(self.fullname, self.name)


class Message(DeclarativeBase):
    __tablename__ = 'Messages'

    id = sql.Column('id', sql.Integer, primary_key=True)
    text = sql.Column('text', sql.String)
    time = sql.Column('time', sql.DateTime)
    reply = sql.Column('reply', sql.Boolean)
    file = sql.Column('file', sql.String)
    contact_id = sql.Column('user_id', sql.Integer, sql.ForeignKey('Contacts.id'))

    # contact = orm.relationship(Contact, backref=orm.backref('messages', uselist=True))

    def __init__(self, message_text, message_time, file='', reply=False):
        self.text = message_text
        self.time = message_time
        self.reply = reply
        self.file = file

    def __repr__(self):
        return '<Message: {} ({})>'.format(self.text, self.time)


class ClientDatabase(object):
    def __init__(self):
        self.opened = False


    def open(self, path):
        self.engine = sql.create_engine('sqlite:///{}.db'.format(path))
        DeclarativeBase.metadata.create_all(self.engine)
        session_factory = orm.sessionmaker(bind=self.engine)
        self.Session = orm.scoped_session(session_factory)
        self.opened = True

    def close(self):
        self.openend = False

    def add_contact(self, session, contact):
        session.add(contact)
        session.commit()

    def add_contact_by_fields(self, session, contact_name, fullname):
        contact = Contact(contact_name, fullname)
        session.add(contact)
        session.commit()

    def get_all(self, session):
        return session.query(Contact).all()

    def get_contact_by_name(self, session, contact_name):
        return session.query(Contact).filter_by(name=contact_name).first()


    def delete_contact(self, session, contact_name):
        contact = session.query(Contact).filter_by(name=contact_name).first()
        if contact is not None:
            session.delete(contact)
            session.commit()

    def add_message(self, session, contact_name, message_text, message_time, filename, reply):
        contact = session.query(Contact).filter_by(name=contact_name).first()
        if contact is not None:
            message = Message(message_text, message_time, file=filename, reply=reply)
            contact.messages.append(message)
            session.commit()

    def delete_message(self, session, id):
        message = session.query(Message).filter(Message.id==id).first()
        session.delete(message)
        session.commit()

    def get_messages_for_contact(self, session, contact_name):
        contact = session.query(Contact).filter_by(name=contact_name).first()
        return contact.messages


def main():
    client_db = ClientDatabase()
    client_db.open('Ivanov')
    session = client_db.Session()
    contacts = session.query(Contact).all()
    print(contacts)
    session.close()

if __name__ == '__main__':
    main()




