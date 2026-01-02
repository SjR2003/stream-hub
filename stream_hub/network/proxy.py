import threading
import logging
import zmq

class ZmqHubProxy:
    def __init__(self, pub_port="tcp://*:7500", sub_port="tcp://*:7501"):
        self.__logger = logging.getLogger(__name__)
        self.pub_port = pub_port
        self.sub_port = sub_port
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run_proxy, daemon=True).start()

    def _run_proxy(self):
        print(f"[Proxy] Starting ZeroMQ Proxy...")
        context = zmq.Context.instance()
        
        xsub = context.socket(zmq.XSUB)
        xpub = context.socket(zmq.XPUB)

        xsub.bind(self.sub_port)
        print(f"[Proxy] XSUB bound at {self.sub_port}")

        xpub.bind(self.pub_port)
        print(f"[Proxy] XPUB bound at {self.pub_port}")

        try:
            zmq.proxy(xsub, xpub)
        except Exception as e:
            print(f"[Proxy] Error: {e}")

        print("[Proxy] Shutting down...")
        xsub.close()
        xpub.close()
