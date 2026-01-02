from pydantic import BaseModel
import numpy as np

from stream_hub.schemas.metadata import PacketMetadata

class Packet(BaseModel):
    metadata: PacketMetadata
    frame: np.ndarray

    model_config = {
        "arbitrary_types_allowed": True
    }