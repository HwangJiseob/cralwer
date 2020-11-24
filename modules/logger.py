'''
Logger.py
<Reference>
Github solidpple/CustomLogger.py, https://gist.github.com/solidpple/ce4b3793da04514c7b7a5ae190c7783d#file-customlogger-py

'''

import re, os, sys, logging, traceback

class SingletonType(type):
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance

class StandardLogger(object):
    __metaclass__ = SingletonType
    _logger = None

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

        # 빌드 시 logging level이 좀 더 상위가 되도록 설정할 것.
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s|%(filename)s] %(asctime)s > %(message)s')

        import datetime
        now = datetime.datetime.now()
        import time
        timestamp = time.mktime(now.timetuple())

        dirname = './log'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        log_dir = "./log/test_"+now.strftime("%Y%m%d_%H%M%S")+".log"
        fileHandler = logging.FileHandler(filename=log_dir, encoding="utf8")
        streamHandler = logging.StreamHandler()

        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        self._logger.addHandler(fileHandler)
        self._logger.addHandler(streamHandler)

    def get_logger(self):
        return self._logger


###
def exclog(exc):
    # traceback 내용을 log에 담기 위해
    # 해당 내용을 parsing하는 것.
    if type(exc) == type(traceback):
        exc = exc.format_exc()
    elif type(exc) == str:
        pass
    else:
        raise TypeError
    arr = exc.split('\n')
    tar = re.findall(r'[ ]*File \"c:[/\S]+[.py]\"', arr[1])
    strlog = arr[1].replace(tar[0], '') + arr[2] + '\t' + arr[3]
    return strlog


