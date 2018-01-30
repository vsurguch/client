
from os import mkdir
from os.path import join, exists
from pathlib import Path

FOLDER_NAME = 'sky_msg'
CONF_FILE_NAME = 'sky_msg.conf'
CONF_DIR = join(str(Path.home()), FOLDER_NAME)


def conf_file_path():
    file_path = join(CONF_DIR, CONF_FILE_NAME)
    return file_path

def make_conf():
    if not exists(CONF_DIR):
        mkdir(CONF_DIR)
    conf_file = conf_file_path()
    f = open(conf_file, 'w')
    f.close()

def write_conf(conf_file, d):
    with open(conf_file, 'w') as f:
        for k, v in d.items():
            str_line = '{}={}\n'.format(k, v)
            f.write(str_line)

def read_conf_file(conf_file):
    result = {}
    with open(conf_file, 'r') as f:
        for str_line in f:
            kv = str_line.split("=")
            k = kv[0]
            v = kv[1][:-1]
            result[k] = v
    return result

def save_conf(**kwargs):
    if not exists(CONF_DIR):
       make_conf()
    conf_file = conf_file_path()
    write_conf(conf_file, kwargs)

def read_conf():
    result = {'username': 'username',
              'hostname': 'localhost',
              'port': '8888'}
    conf_file = join(CONF_DIR, CONF_FILE_NAME)
    if not exists(conf_file):
        make_conf()
        write_conf(conf_file, result)
        return result
    else:
        return read_conf_file(conf_file)

def get_path(filename=''):
    return join(CONF_DIR, filename)




