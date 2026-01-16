from multiprocessing import shared_memory
import numpy as np
import time
import cv2
import logging

# --------------------------------------------------
# Configuration
# --------------------------------------------------
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CHANNELS = 3
TARGET_FPS = 30

FRAME_BYTES = FRAME_WIDTH * FRAME_HEIGHT * CHANNELS
GAMMA = 1.4  # Adjustable light 1.2-1.6

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CAMERA] %(levelname)s: %(message)s"
)

# --------------------------------------------------
# Gamma LUT (precomputed, fast)
# --------------------------------------------------
GAMMA_LUT = np.array(
    [(i / 255.0) ** (1.0 / GAMMA) * 255 for i in range(256)],
    dtype=np.uint8
)

# --------------------------------------------------
# Camera open helper
# --------------------------------------------------
def open_camera_fast(indices=(1, 2)):
    for index in indices:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            logging.info("Camera opened on index %d", index)
            return cap
        cap.release()
    return None


# --------------------------------------------------
# Camera process entry point
# --------------------------------------------------
def main(pipe=None):
    shm = None
    cap = None

    try:
        # --------------------------------------------------
        # Shared memory
        # --------------------------------------------------
        shm = shared_memory.SharedMemory(create=True, size=FRAME_BYTES)
        frame_buffer = np.ndarray(
            (FRAME_HEIGHT, FRAME_WIDTH, CHANNELS),
            dtype=np.uint8,
            buffer=shm.buf
        )
        frame_buffer[:] = 0

        # --------------------------------------------------
        # Camera open (defaults)
        # --------------------------------------------------
        cap = open_camera_fast()
        if cap is None:
            raise RuntimeError("No camera available")

        # Lock geometry & FPS (keep camera defaults otherwise)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

        # --------------------------------------------------
        # Exposure warm-up (CRITICAL)
        # --------------------------------------------------
        logging.info("Warming up camera exposure...")
        for _ in range(25):
            cap.read()
            time.sleep(0.02)

        # --------------------------------------------------
        # Notify UI AFTER camera is ready
        # --------------------------------------------------
        if pipe:
            pipe.send(shm.name)

        logging.info("Camera ready, entering capture loop")

        # --------------------------------------------------
        # Capture loop (stable pacing)
        # --------------------------------------------------
        frame_interval = 1.0 / TARGET_FPS
        next_frame_time = time.perf_counter()

        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.002)
                continue

            if frame.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # Gamma correction (fix dark image)
            frame = cv2.LUT(frame, GAMMA_LUT)

            # Write directly to shared memory
            frame_buffer[:] = frame

            # Frame pacing
            next_frame_time += frame_interval
            sleep_time = next_frame_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except Exception:
        logging.exception("Camera process failed")
        if pipe:
            pipe.send("ERROR")

    finally:
        logging.info("Shutting down camera process")
        if cap:
            cap.release()
        if shm:
            shm.close()
            shm.unlink()
