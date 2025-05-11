import os
import time

from pyparsing import CloseMatch


def timer_for_thread(waiting_time,name_thread):

        for number in range(waiting_time):
            try:
                time.sleep(1)
            except:
                print(f"timer for {name_thread} is stopped")
                os._exit(0)