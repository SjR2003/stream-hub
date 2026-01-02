from pydantic import BaseModel

class PacketMetadata(BaseModel):
    stream_id: str
    frame_id: int
    timestamp: float
    source: str
    events: dict
    frame_size: int