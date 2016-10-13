import os
import errno
import time

__log_file_name = None

def make_dir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def init():
    global __log_file_name
    make_dir("log")
    __log_file_name = "log/tis.log.%s" % (str(hex(int(time.time())))[2:])


def log(s):
    log_file = open(__log_file_name, 'a')
    log_file.write("%f: %s\n" % (time.time(), s))
    log_file.close()