import cv2
import numpy as np
import logging
from typing import Optional
from stream_hub.utils.latency_logger import measure_latency 
logger = logging.getLogger(__name__)

class FrameEncoder:
    @staticmethod
    @measure_latency
    def encode(frame, quality: int = 85) -> Optional[bytes]:
        if frame is None or frame.size == 0:
            print("Cannot encode empty frame")
            return None
            
        try:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            ok, buf = cv2.imencode(".jpg", frame, encode_params)
            
            if not ok:
                print("JPEG encoding failed")
                return None
                
            return buf.tobytes()
        except Exception as e:
            print(f"Frame encoding error: {e}")
            return None

    @staticmethod
    @measure_latency
    def decode(data: bytes) -> Optional[np.ndarray]:
        if not data or len(data) == 0:
            print("Cannot decode empty data")
            return None
            
        try:
            arr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("Frame decoding failed")
            return frame
        
        except Exception as e:
            print(f"Frame decoding error: {e}")
            return None

    @staticmethod
    def validate_frame(frame) -> bool:
        if frame is None:
            return False
        if not isinstance(frame, np.ndarray):
            return False
        if frame.size == 0:
            return False
        if len(frame.shape) != 3:
            return False
        return True