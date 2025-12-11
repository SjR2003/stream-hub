# stream_hub/ingestion/stream_worker_process.py
from datetime import datetime
from typing import Dict
import logging
import ctypes
import time

from stream_hub.ingestion.capture_worker import CaptureWorker
from stream_hub.ingestion.frame_encoder import FrameEncoder
from stream_hub.network.zmq_handler import ZmqHandler
from stream_hub.utils.logger import setup_logger


def stream_worker_entry(stream_cfg, proxy_endpoint: str, feedbacks: Dict, default_fps: int):
    setup_logger(f"worker-{stream_cfg['id']}", level=logging.INFO)
    worker = StreamProcessWorker(stream_cfg, proxy_endpoint, feedbacks, default_fps)
    worker.run()


class StreamProcessWorker:
    def __init__(
        self,
        stream_cfg,
        proxy_endpoint: str,
        feedbacks: Dict,
        default_fps: int = 15,
        reconnect_delay: int = 5,
    ):
        self.__logger = logging.getLogger(__name__)
        self.__proxy_endpoint = proxy_endpoint
        self.__feedbacks_cfg = feedbacks or {}

        self.__reconnect_delay = reconnect_delay
        self.__fps = int(stream_cfg.get("fps", default_fps))
        self.__stream_id = stream_cfg["id"]
        self.__source = stream_cfg["source"]
        self.__zmq_handler: ZmqHandler | None = None

        self.__stats = {
            "frames_processed": 0,
            "frames_failed": 0,
            "reconnects": 0,
            "start_time": datetime.now(),
        }

    def run(self):
        print(f"[{self.__stream_id}] Worker started")
        ctypes.WinDLL("winmm").timeBeginPeriod(1)

        self.__init_zmq_handler()

        worker = None
        frame_interval = 1.0 / self.__fps

        try:
            while True:
                try:
                    if worker is None:
                        worker = CaptureWorker(
                            self.__stream_id,
                            self.__source,
                            fps=self.__fps,
                        )
                        print(f"[{self.__stream_id}] CaptureWorker started")

                    t0 = time.perf_counter()

                    frame, frame_id, ts = worker.get_frame()

                    if frame is None:
                        self.__stats["frames_failed"] += 1
                        time.sleep(0.02)
                        continue

                    jpeg = FrameEncoder.encode(frame, 85)
                    if jpeg is None:
                        self.__stats["frames_failed"] += 1
                        continue

                    events = self.__get_events_feedback(self.__stream_id)

                    metadata = {
                        "stream_id": self.__stream_id,
                        "frame_id": frame_id,
                        "timestamp": ts,
                        "source": self.__source,
                        "events": events,
                        "frame_size": len(jpeg),
                    }

                    self.__zmq_handler.publish(metadata, jpeg)
                    self.__stats["frames_processed"] += 1

                    elapsed = time.perf_counter() - t0
                    remain = frame_interval - elapsed
                    if remain > 0:
                        time.sleep(remain)

                except Exception as e:
                    print(f"[{self.__stream_id}] Worker loop error: {e}")

                    self.__stats["frames_failed"] += 1
                    if worker:
                        worker.close()
                        worker = None
                    time.sleep(self.__reconnect_delay)

        finally:
            if worker:
                worker.close()
            print(f"[{self.__stream_id}] Worker shutting down → {self.__stats}")
            ctypes.WinDLL("winmm").timeEndPeriod(1)

    def __get_events_feedback(self, stream_id: str) -> Dict:
        packet = self.__zmq_handler.get_feedback(stream_id)
        result = {}
        for name in self.__feedbacks_cfg.keys():
            info = packet.get(name, {}) or {}
            if not info:
                result[name] = {
                    "data": None,
                    "target": None,
                    "timestamp": None,
                }
                continue
            elif info["ts"] is None:
                continue
            
            ts = info.get("ts")
            result[name] = {
                "data": info.get("data"),          
                "target": info.get("target", []),   
                "timestamp": ts,
            }
        return result

    def __init_zmq_handler(self):
        self.__zmq_handler = ZmqHandler(self.__proxy_endpoint, self.__feedbacks_cfg)
        self.__zmq_handler.initialize_runtime()
