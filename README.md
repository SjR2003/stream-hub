# Stream Hub

A lightweight, high-performance **multi-camera ingestion and synchronization hub** designed for real-time AI pipelines, analytics systems, and UI consumption.

Stream Hub captures multiple RTSP streams, timestamps frames, injects event-based metadata, and publishes synchronized JPEG frames over ZeroMQ to a set of independent consumer modules (e.g., perception, analytics, UI).

It is designed to be modular, fast, and easy to integrate into complex video-based systems without manually wiring modules together.

---

## Demo

<video src="" 
       width="640" 
       autoplay 
       loop 
       muted 
       playsinline>
</video>

---

## Key Features

* **Multi-stream ingestion** with per-stream workers
* **Zero buffering RTSP capture** → avoids internal RTSP latency
* **Accurate per-frame timestamping** for stream synchronization
* **Event feedback system** from downstream modules (UI, analytics, perception)
* **Metadata injection** into each frame
* **Decoupled architecture** using ZMQ pub/sub
* **Config-driven**, scalable, and easy to deploy (local or Docker)

---

## High-Level Architecture

Below is the system flow illustrated in the provided diagram:

<!-- ![Image]() -->

**Pipeline overview:**

1. **Capture RTSP streams** from multiple cameras
2. **Timestamp each frame** (RTSP normally lacks usable timestamps)
3. **Assign event feedback** from consumer modules (UI, analytics, perception)
4. **Generate metadata** per frame
5. **Broadcast frames + metadata** via ZMQ PUB/SUB
6. **Consumer modules act independently**, based on events relevant to them
7. **Feedback events** flow back to Stream Hub to adjust stream priorities or UI selections

**Feedback channels:** (it's flexible and can be changed in the config file `hub.yaml`)

| Module     | Endpoint               | Events                        |
| ---------- | ---------------------- | ----------------------------- |
| perception | `tcp://127.0.0.1:7201` | objects_count, spatial_object |
| analytics  | `tcp://127.0.0.1:7202` | accident, mistake             |
| UI         | `tcp://127.0.0.1:7203` | user_selection                |

---

## Directory Structure

```
stream_hub/
│
├── main.py
├── configs/
│   ├── hub.yaml
│   └── streams.yaml
│
├── ingestion/
│   ├── capture_worker.py
│   ├── frame_encoder.py
│   ├── stream_manager.py
│   └── stream_worker_process.py
│
├── network/
│   ├── proxy.py
│   └── zmq_handler.py
│
└── utils/
    ├── latency_logger.py
    ├── logger.py
    └── utils.py
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your/repo.git
cd stream-hub
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure streams

Edit `stream_hub/configs/streams.yaml`:

```yaml
streams:
  - id: cam1
    source: "rtsp://localhost:8554/cam1"
    enabled: true
    fps: 30
```

### 4. Configure hub and feedback routing

Edit `hub.yaml`:

```yaml
zmq:
  hub_endpoint: "tcp://127.0.0.1:7500"
  proxy_endpoint: "tcp://127.0.0.1:7501"
```

### 5. Run Stream Hub

```bash
python -m stream_hub.main
```

---

## How It Works (High-Level)

### 🟦 1. StreamManager

Creates a dedicated **process** for each camera stream.
Each worker handles:

* RTSP capture
* Timing control (FPS enforcement)
* Metadata generation
* Event injection
* Publishing frames

### 🟩 2. CaptureWorker

Runs in a **background thread**, pulling frames from OpenCV with minimal buffering.

### 🟨 3. FrameEncoder

Encodes frames to **JPEG** with configurable quality for efficient transmission.

### 🟥 4. ZmqHandler

Handles:

* PUB: sending frames + metadata
* SUB: receiving feedback from UI / analytics / perception

### 🟧 5. ZmqHubProxy

Routes messages between workers and consumers using XPUB/XSUB sockets.

---

## Metadata Schema

Each published message contains:

```python
{
  "metadata": {
    "stream_id": "cam1",
    "frame_id": 1245,
    "timestamp": 1710001112.532,
    "source": "rtsp://localhost/cam1",
    "events": {
      "ui": {...},
      "perception": {...},
      "analytics": {...}
    },
    "frame_size": 34812
  },
  "jpeg_bytes": <binary JPEG>
}
```

Consumers simply `SUB` to the hub endpoint and decode JPEG frames as needed.

---

## Intended Use Cases

* Real-time AI pipelines (object detection, tracking, analytics)
* Multi-camera dashboards and UI applications
* Edge devices where RTSP latency is unacceptable
* Systems requiring cross-module feedback without tight coupling
* Robotics, surveillance, industrial monitoring

---

## Feature work

- complete Docker configuration
- delete print statements and fix logger bug

---

## License

MIT (or specify your license)
