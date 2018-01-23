

import json
import time

MSG_TEMPLATE = {
    "action": "",
    "time": 0,
}

RSP_TEMPLATE = {
    "response": 0,
    "time": 0,
    "alert": "",
}

RESPONSES_DICT = {
    '0': 'unknown code',
    '100': 'general notice',
    '101': ' important notice',
    '200': 'ok',
    '201': 'created',
    '202': 'accepted',
    '300': 'broadcast message',
    '400': 'bad request or bad json',
    '401': 'not authorized',
    '402': 'incorrect username or password',
    '403': 'forbidden : site ban in effect on users ip or similar',
    '404': 'not found : user or room does not exist on the server',
    '409': 'conflict : someone is already connected with a given user name',
    '410': 'gone : user exists but is not available (offline)',
    '500': '500 server error',
}

class GeneralMessage(object):
    def __init__(self, type='g'):
        if type == 'g':
            self.msg = {}
        if type == 'm':
            self.msg = MSG_TEMPLATE.copy()
            self.msg['time'] = time.time()
        if type == 'r':
            self.msg = RSP_TEMPLATE.copy()
            self.msg['time'] = time.time()

    def __getitem__(self, key):
        '''
        по ключу возвращает значние из словаря
        :param key:
        :return:
        '''
        if key in self.msg:
            if key == 'time':
                return self.get_ctime()
            return self.msg[key]
        else:
            return None

    def __setitem__(self, key, value):
        if key in self.msg:
            if key != 'time':
                self.msg[key] = value
        else:
            self.add_key_value(key, value)

    def get_time(self):
        return self.msg['time']

    def get_ctime(self):
        '''
        перевод UNIXSTAMP TIME в ctime
        :return: ctime
        '''
        return time.ctime(self.msg['time'])

    def __str__(self):
        '''
        выводит все пары ключ-значение словаря
        :return:
        '''
        result = ['{k}: {v}\n'.format(k=key, v=self[key]) for key in self.msg.keys()]
        s = ''.join(result)
        return s

    def length_json_bytes(self, encoding):
        return len((json.dumps(self.msg)).encode(encoding))

    def add_key_value(self, key, value):
        if key == '':
            raise TypeError
        else:
            self.msg[key] = value

    def get_binary_json(self, encoding):
        '''
        :param encoding: кодировка
        :return: бинарые данные в формате json
        '''
        jsn = json.dumps(self.msg)
        return jsn.encode(encoding)

    def make_from_binary_json(self, data, encoding):
        '''
        :param data: бинарные данные в формате json
        :param encoding: кодировка
        :return: self класса сообщение
        '''
        decoded_data = data.decode(encoding)
        self.msg = json.loads(decoded_data)

class ResponseMessage(GeneralMessage):
    def __init__(self, response_code=0, alert=''):
        super().__init__('r')
        self.msg['response'] = response_code
        if alert == '' and str(response_code) in RESPONSES_DICT:
            self['alert'] = RESPONSES_DICT[str(response_code)]
        else:
            self.msg['alert'] = alert

    @property
    def response_code(self):
        return self.msg['response']

    @response_code.setter
    def response_code(self, code):
        str_code = str(code)
        if str_code in RESPONSES_DICT:
            self.msg['response'] = code
            self.msg['alert'] = RESPONSES_DICT[str_code]
        else:
            self.msg['response'] = 0
            # raise Exceptions.NoResponseCode

    def get_response_info(self):
        '''
        :return: кортеж из кода ответа и текста ответа (из словаря)
        '''
        str_code = str(self.response_code)
        if str_code in RESPONSES_DICT:
            response_text = RESPONSES_DICT[str_code]
        else: response_text = 'unknown code'
        return (self.response_code, response_text)


class Message(GeneralMessage):
    def __init__(self, action=''):
        super().__init__('m')
        self.msg['action'] = action


class MessageAuthenticate(Message):
    def __init__(self, user, password):
        super().__init__('authentificate')
        user_data = {
            'account_name': user,
            'password': password,
        }
        self.add_key_value('user', user_data)

class MessageGetContacts(Message):
    def __init__(self, username):
        super().__init__('get_contacts')
        self.add_key_value('user', username)

class MessageAddContact(Message):
    def __init__(self, username, contact_name):
        super().__init__('add_contact')
        self.add_key_value('user', username)
        self.add_key_value('contact', contact_name)

class MessageDeleteContact(Message):
    def __init__(self, username, contact_name):
        super().__init__('delete_contact')
        self.add_key_value('user', username)
        self.add_key_value('contact', contact_name)

class MessageContactOnline(Message):
    def __init__(self, contact_name):
        super().__init__('contact_online')
        self.add_key_value('contact', contact_name)

class MessageContactOffline(Message):
    def __init__(self, contact_name):
        super().__init__('contact_offline')
        self.add_key_value('contact', contact_name)

class MessageContact(Message):
    def __init__(self, contact_login, contact_name, online):
        super().__init__('contact_list')
        self.add_key_value('username', contact_login)
        self.add_key_value('name', contact_name)
        self.add_key_value('online', online)

class MessagePersonal(Message):
    def __init__(self, username, dest, text):
        super().__init__('personal_message')
        self.add_key_value('user', username)
        self.add_key_value('dest', dest)
        self.add_key_value('text', text)

class MessagePersonalFrom(Message):
    def __init__(self, src_user, text):
        super().__init__('personal_message')
        self.add_key_value('src', src_user)
        self.add_key_value('text', text)

class MessageDeleteLastMessage(Message):
    def __init__(self, username, dest):
        super().__init__('delete_last_message')
        self.add_key_value('user', username)
        self.add_key_value('dest', dest)

class MessageDeleteLastMessageFwd(Message):
    def __init__(self, src):
        super().__init__('delete_last_message')
        self.add_key_value('src', src)


def main_test():
    response = ResponseMessage(100)
    print(response, response.get_response_info())
    response2 = ResponseMessage(20)
    print(response2, response2.get_response_info())
    message = Message('presence')
    message.add_key_value('user', 'vladimir')
    print(message)
    user = MessageAuthenticate('vladimir', 'abcd')
    user.someKey = 'anything'
    print(user)


if __name__ == '__main__':
    main_test()