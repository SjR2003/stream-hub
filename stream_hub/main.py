from pathlib import Path    
import multiprocessing
import threading
import logging
import signal
import ctypes
import time

from stream_hub.ingestion.stream_manager import StreamManager
from stream_hub.utils.logger import setup_logger
from stream_hub.network.proxy import ZmqHubProxy
from stream_hub.utils.utils import load_yaml

def main():
    logger = setup_logger("stream-hub", level=logging.INFO)
    ctypes.WinDLL('winmm').timeBeginPeriod(1)

    base_dir = Path(__file__).resolve().parent
    cfg_dir = base_dir / "configs"

    streams_cfg = load_yaml(cfg_dir / "streams.yaml").get("streams", [])
    hub_cfg = load_yaml(cfg_dir / "hub.yaml")

    zmq_cfg = hub_cfg.get("zmq", {})
    ingestion_cfg = hub_cfg.get("ingestion", {})

    feedbacks = hub_cfg.get("feedbacks")
    hub_endpoint = zmq_cfg.get("hub_endpoint", "tcp://127.0.0.1:7500")
    proxy_endpoint = zmq_cfg.get("proxy_endpoint", "tcp://127.0.0.1:7501")

    proxy = ZmqHubProxy(pub_port=hub_endpoint, sub_port=proxy_endpoint)
    proxy.start()
    time.sleep(1)
    stop_event = threading.Event()

    manager = StreamManager(
        streams_cfg=streams_cfg,
        proxy=proxy_endpoint,
        feedback=feedbacks,
        fps=int(ingestion_cfg.get("fps", 30)),
    )

    def handle_sig(signum, frame):
        logger.info("Received signal %s → shutting down ...", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    logger.info("Starting stream manager with %d streams", len(streams_cfg))
    manager.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()

    logger.info("Waiting for workers to close ...")
    manager.stop()

    ctypes.WinDLL('winmm').timeEndPeriod(1)
    logger.info("Stream-hub stopped cleanly")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
