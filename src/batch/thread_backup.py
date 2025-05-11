from threading import Thread
from ..service.backup import backup_database_auto


def start_thread_backup():
    backup_thread = Thread(target=backup_database_auto,daemon=True)
    backup_thread.start()
