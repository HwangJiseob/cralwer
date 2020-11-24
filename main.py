import time, threading, sys, win32api
from test3 import CRAWLER

def CRAWLER_MANAGER(event):
    # step = CRAWLER()
    # while True:
    #     if not event.isSet():
    #         print(step.__next__())

    i = 0
    while i<10:
        if not event.isSet():
            print(i)
            i += 1
        time.sleep(1)


def watch(event):
    print_paused  = 0
    print_restart = 0
    while True:
        c_down = abs(win32api.GetKeyState(ord('C'))& 0x8000)
        p_down = abs(win32api.GetKeyState(ord('P'))& 0x8000)
        s_down = abs(win32api.GetKeyState(ord('S'))& 0x8000)

        paused  = c_down == 32768 and p_down == 32768
        restart = c_down == 32768 and s_down == 32768

        if paused:
            if print_paused == 0:
                print("pause")
                print_paused += 1
            event.set()
        else:
            print_paused = 0

        if restart:
            if print_restart == 0:
                print("restart")
                print_restart += 1
            event.clear()
        else:
            print_restart = 0
        



if __name__ == "__main__":
    event = threading.Event()
    event.clear()
    t1 = threading.Thread(target=CRAWLER_MANAGER, args=(event, ))
    t2 = threading.Thread(target=watch, args=(event, ))

    t1.start()
    t2.start()