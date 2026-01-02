from typing import Any, Dict, Optional
from threading import Thread, Lock
import logging
import time
import zmq

from stream_hub.utils.latency_logger import measure_latency

class ZmqHandler:
    def __init__(self, proxy_endpoint: str, feedbacks_cfg: Dict[str, Dict[str, Any]]):
        self.__logger = logging.getLogger(__name__)
        self.__proxy_endpoint = proxy_endpoint
        self.__feedbacks_cfg = feedbacks_cfg or {}

        self.__ctx: Optional[zmq.Context] = None
        self.__pub_socket: Optional[zmq.Socket] = None
        self.__sub_socket: Optional[zmq.Socket] = None

        self.__feedback_state: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.__feedback_lock = Lock()
        self.__feedback_thread: Optional[Thread] = None


    def initialize_runtime(self):
        self.__ctx = zmq.Context.instance()
        self.__pub_socket = self.__ctx.socket(zmq.PUB)
        self.__pub_socket.setsockopt(zmq.SNDHWM, 20)
        self.__pub_socket.setsockopt(zmq.LINGER, 50)

        try:
            self.__pub_socket.connect(self.__proxy_endpoint)
            print(f"[ZMQ] PUB connect at {self.__proxy_endpoint}")
        except Exception as e:
            print(f"[ZMQ] connect failed: {e}")

        if self.__feedbacks_cfg:
            self.__sub_socket = self.__ctx.socket(zmq.SUB)
            self.__sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

            for name, cfg in self.__feedbacks_cfg.items():
                endpoint = cfg.get("zmq") if isinstance(cfg, dict) else None
                if endpoint:
                    self.__sub_socket.connect(endpoint)
                    print(f"[ZMQ] Worker connected to FEEDBACK '{name}' → {endpoint}")

            self.__feedback_thread = Thread(
                target=self.__feedback_receive_loop,
                daemon=True
            )
            self.__feedback_thread.start()

    @measure_latency
    def publish(self, message) -> None:
        if self.__pub_socket is None:
            raise RuntimeError("ZmqHandler.publish() called before initialize_runtime()")
        try:
            self.__pub_socket.send_pyobj(message)
        except Exception as e:
            print(f"[ZMQ] Publish error on {self.__proxy_endpoint}: {e}")

    def __feedback_receive_loop(self):
        while True:
            try:
                msg = self.__sub_socket.recv_pyobj()
            except Exception as e:
                print(f"[ZMQ] Feedback recv error: {e}")
                time.sleep(0.1)
                continue

            if not isinstance(msg, dict):
                continue

            stream_id = msg.get("stream_id")
            node_name = msg.get("node_name") or msg.get("module")
            event = msg.get("event")
            target = msg.get("target", [])
            ts = msg.get("ts", time.time())

            if not stream_id or not node_name:
                continue

            cfg = self.__feedbacks_cfg.get(node_name)
            allowed_events = None
            if isinstance(cfg, dict):
                allowed_events = cfg.get("events")
            if allowed_events and event not in allowed_events:
                continue
            
            with self.__feedback_lock:
                per_stream = self.__feedback_state.setdefault(stream_id, {})
                per_stream[node_name] = {
                    "data": event,
                    "target": target,
                    "ts": ts,
                }

    def get_feedback(self, stream_id: str) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        with self.__feedback_lock:
            per_stream = self.__feedback_state.get(stream_id, {})

            for name in self.__feedbacks_cfg.keys():
                info = per_stream.get(name)
                if info is None:
                    result[name] = {"data": None, "target": None, "ts": None}
                else:
                    result[name] = {
                        "data": info.get("data", None),
                        "target": list(info.get("target", None)),
                        "ts": float(info.get("ts", None)),
                    }
        return result

    def close(self):
        if self.__pub_socket:
            try:
                self.__pub_socket.close()
            except Exception:
                pass
        if self.__sub_socket:
            try:
                self.__sub_socket.close()
            except Exception:
                pass

        self.__pub_socket = None
        self.__sub_socket = None

    def __del__(self):
        self.close()
