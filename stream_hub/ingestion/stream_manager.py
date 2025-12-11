import logging
from multiprocessing import Process
from stream_hub.ingestion.stream_worker_process import stream_worker_entry

class StreamManager:
    def __init__(self, streams_cfg, proxy, feedback, fps=15):
        self.__logger = logging.getLogger(__name__)
        self.__streams_cfg = streams_cfg
        self.__proxy = proxy
        self.__feedbacks = feedback
        self.__fps = fps
        self.__processes = {}

    def start(self):
        for cfg in self.__streams_cfg:
            if not cfg.get("enabled", True):
                print(f"[{cfg['id']}] Disabled stream skipped")
                continue

            p = Process(
                target=stream_worker_entry,
                args=(cfg, self.__proxy, self.__feedbacks, self.__fps),
            )
            p.daemon = False
            p.start()

            self.__processes[cfg["id"]] = p
            print(f"[{cfg['id']}] Started worker PID={p.pid}")

    def stop(self):
        print("Stopping StreamManager...")

        for sid, proc in self.__processes.items():
            if proc.is_alive():
                print(f"[{sid}] Terminating process {proc.pid}")
                proc.terminate()
                proc.join(timeout=3)

        print("All workers stopped")
