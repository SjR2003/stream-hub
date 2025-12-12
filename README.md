# Stream Hub

Stream Hub is a lightweight, high-performance **A real-time multi-camera ingestion and synchronization backbone**
designed to sit at the core of real-time AI pipelines.

It captures multiple RTSP streams, timestamps frames with low latency, injects event-based metadata,
and publishes synchronized JPEG frames over ZeroMQ to independent downstream consumers
such as perception, analytics, and UI modules.

The hub is intentionally **decoupled**:
it does not run AI models, dashboards, or business logic.
Instead, it acts as a real-time coordination and data-routing backbone.

---

## Demo

> A short demo video showcasing multi-camera ingestion and synchronized playback
> will be added soon.

<video src=""
       width="640"
       autoplay
       loop
       muted
       playsinline>
</video>


---

## Key Features

- **Multi-stream ingestion** using isolated worker processes
- **Low-latency RTSP capture** (minimal internal buffering)
- **Accurate per-frame timestamping** (RTSP timestamps are unreliable)
- **Event feedback loop** from external modules (UI, analytics, perception)
- **Metadata injection** per frame
- **Fully decoupled architecture** via ZeroMQ XPUB/XSUB
- **Config-driven design** (no hard-coded ports or routes)
- **Docker-friendly** (single-service container)

---

## High-Level Architecture

Stream Hub sits between cameras and consumer modules.
It enables complex multi-module systems without direct module-to-module wiring.

Cameras → Stream Hub → Consumers  
Consumers → Feedback → Stream Hub

<div align="center">
  <img
    width="1280"
    height="320"
    alt="Stream Hub Architecture"
    src="https://github.com/user-attachments/assets/e40420bd-92f1-415e-bf09-7cfbf86c34c7"
  />
  <p><em>High-level Stream Hub architecture and data flow</em></p>
</div>


**Pipeline overview:**

```text
RTSP Cameras
     |
     ▼
[ Stream Workers ]  ← per camera (process-based)
     |
     ▼
[ ZMQ XSUB ]        ← internal
     |
     ▼
[ ZMQ XPUB ]  ───────────► Consumers (UI / Analytics / Perception)
     ▲
     |
Feedback Events (ZMQ PUB)
```

---

## Feedback Channels

Feedback channels allow downstream modules to influence
how frames are annotated or prioritized — without direct coupling.
Feedback events are **optional** and **non-blocking**.
If a consumer is offline, Stream Hub continues operating normally.

All feedback routing is defined in `hub.yaml`.


| Module     | Direction | Example Events    |
| ---------- | --------- | ----------------- |
| UI         | → Hub     | user_selection    |
| Perception | → Hub     | spatial_object    |
| Analytics  | → Hub     | accident, mistake |

---

## Configuration

Stream Hub is fully driven by YAML configuration.
Restarting the container is enough to apply changes.


#### `streams.yaml`

```yaml
streams:
  - id: cam1
    source: rtsp://host.docker.internal:8554/cam1
    enabled: true
    fps: 30
```

* `id`: logical stream identifier
* `source`: RTSP URL (simulated or real camera)
* `fps`: enforced output FPS (not camera FPS)



#### `hub.yaml`

```yaml
zmq:
  hub_endpoint: "tcp://0.0.0.0:7500"   # consumers connect here
  proxy_endpoint: "tcp://127.0.0.1:7501" # internal workers only

feedbacks:
  ui:
    zmq: "tcp://0.0.0.0:7203"
    events: [user_selection]
```

> ⚠️ `proxy_endpoint` is **internal only**
> `hub_endpoint` and feedback ports may be exposed externally.

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

### Local usage

#### 1. Clone the repository

```
git clone https://github.com/your/repo.git
cd stream-hub
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure streams

Edit `configs/streams.yaml`:

#### 4. Configure hub and feedback routing

Edit `configs/hub.yaml`:

#### 5. Run Stream Hub

```bash
python -m stream_hub.main --stream_config path_to_`streams.yaml`  --hub_config path_to_`hub.yaml`
```

###  Docker Usage

#### 1. Clone the repository

```bash
git clone https://github.com/your/repo.git
cd stream-hub
```

#### 2. Configure streams

Edit `configs/streams.yaml`:

#### 3. Configure hub and feedback routing

Edit `configs/hub.yaml`:

### 4. Generate `.env` from config

```bash
python utils/generate_env.py --hub_config configs/hub.yaml
```

### 5. Run container

```bash
docker compose up --build
```

After the first build if config change:

```bash
python utils/generate_env.py --hub_config configs/hub.yaml
```

```bash
docker compose up -d --force-recreate
```

otherwise:

```bash
docker compose up
```
This setup is optimized for edge devices and on-prem deployments.

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

## Roadmap

- [ ] Replace print statements with structured logging
- [ ] Improve latency metrics and observability

---

## License

MIT

