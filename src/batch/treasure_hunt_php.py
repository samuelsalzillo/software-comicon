import time
from threading import Thread
from ..service.service_treasure_hunt import service_treasure_hunt


def start_thread_treasure_hunt(app_instance):
    backup_thread = Thread(target=service_treasure_hunt,daemon=True,args=(app_instance,))
    backup_thread.start()
