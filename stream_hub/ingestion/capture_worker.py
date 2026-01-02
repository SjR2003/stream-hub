from stream_hub.utils.latency_logger import measure_latency
from collections import deque
from threading import Thread
import logging
import time
import cv2

class CaptureWorker:
    def __init__(self, stream_id: str, url: str, fps: int = 15):
        self.__stream_id = stream_id
        self.__url = url
        self.__fps = fps

        self.__cap = None
        self.__frame_id = 0
        self.__stop_signal = False
        self.__frame_queue = deque(maxlen=1)

        self.__init_logger()
        self.__stream_thread = Thread(target=self.__start_stream, daemon=True)
        self.__stream_thread.start()

    def get_frame(self):
        if len(self.__frame_queue) == 0:
            return None, None, None
        return self.__frame_queue[-1]

    def get_stream_info(self):
        return {
            "stream_id": self.__stream_id,
            "url": self.__url,
            "fps": self.__fps,
        }

    def close(self):
        if self.__stream_thread.is_alive():
            self.__stop_signal = True
            print(f"[{self.__stream_id}] Closing stream.")

            if self.__cap is not None:
                self.__cap.release()
            self.__stream_thread.join(timeout=2)

            print(f"[{self.__stream_id}] Stream closed.")

    def __init_logger(self):
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.INFO)

    def __start_stream(self):
        print(f"[{self.__stream_id}] Opening stream: {self.__url}")

        self.__cap = cv2.VideoCapture(self.__url, cv2.CAP_FFMPEG)
        while not self.__stop_signal:
            if not self.__cap.isOpened():
                print(f"[{self.__stream_id}] Stream not opened. Retrying...")
                time.sleep(1)
                self.__cap.open(self.__url, cv2.CAP_FFMPEG)
            else:
                self.__read_frame()
 
    @measure_latency
    def __read_frame(self):
        t0 = time.perf_counter()
        ret, frame = self.__cap.read()
        read_ms = (time.perf_counter() - t0) * 1000
        print(f"[Latency] cap.read() = {read_ms:.3f} ms")

        if not ret or frame is None:
            print(f"[{self.__stream_id}] Failed to read frame. Retrying...")
            time.sleep(0.3)
            return
        
        ts = time.time()
        self.__frame_id += 1
        self.__frame_queue.append((frame, self.__frame_id, ts))

    def __del__(self):
        try:
            self.close()
        except:
            pass
