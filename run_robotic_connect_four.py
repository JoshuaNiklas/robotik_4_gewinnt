#!/usr/bin/env python3
"""
Orchestrator: verbindet Kamera, Detection, Tracker, Spiel-Engine und sammelt
Roboter-Kommandos. Die XML-Datei für den Roboter wird erst am Ende erzeugt.
"""
import os
import sys
import time
import signal
import subprocess
import threading
import xml.etree.ElementTree as ET
from multiprocessing import Process, Pipe

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
DATA_DIR = os.path.join(BASE_DIR, "data")
CROP_PATH = os.path.join(DATA_DIR, "crop.png")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
GAME_STATUS_PATH = os.path.join(PROCESSING_DIR, "game_status.xml")
ROBOT_XML_OUTPUT = os.path.join(BASE_DIR, "robot_commands.xml")

shutdown_flag = False


def load_crop_points(config_path=CONFIG_PATH, frame_w=640, frame_h=480):
    import yaml
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        pts = data.get("points", [])
        if len(pts) != 4:
            return None
        abs_pts = [(
            min(max(int(p["x"] * (frame_w - 1)), 0), frame_w - 1),
            min(max(int(p["y"] * (frame_h - 1)), 0), frame_h - 1),
        ) for p in pts]
        return abs_pts
    except Exception:
        return None


def save_crops_from_shm(shm_name, frame_w, frame_h, channels, interval=2.0):
    """Periodisch das crop-Bild aus SharedMemory extrahieren und abspeichern."""
    import numpy as np
    from multiprocessing import shared_memory
    import cv2

    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except Exception:
        return

    buf = shm.buf

    def work():
        global shutdown_flag
        while not shutdown_flag:
            try:
                arr = np.ndarray((frame_h, frame_w, channels), dtype=np.uint8, buffer=buf)
                pts = load_crop_points(frame_w=frame_w, frame_h=frame_h)
                if pts:
                    import cv2 as _cv
                    import numpy as _np
                    pts_np = _np.array(pts, dtype=_np.int32)
                    x_min = int(_np.min(pts_np[:, 0]))
                    x_max = int(_np.max(pts_np[:, 0]))
                    y_min = int(_np.min(pts_np[:, 1]))
                    y_max = int(_np.max(pts_np[:, 1]))
                    if x_max > x_min and y_max > y_min:
                        cropped = arr[y_min:y_max, x_min:x_max]
                        try:
                            _cv.imwrite(CROP_PATH, cropped)
                        except Exception:
                            pass
                time.sleep(interval)
            except Exception:
                time.sleep(0.5)

    t = threading.Thread(target=work, daemon=True)
    t.start()
    return t


def tail_game_moves(poll_interval=0.5):
    """Überwacht `game_status.xml` und sammelt neue Züge. Gibt Liste robot-commands zurück."""
    robot_commands = []
    last_moves = []

    def parse_moves_from_xml(path):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            moves_text = root.find('moves').text
            moves = eval(moves_text) if moves_text else []
            status = root.find('status').text if root.find('status') is not None else ''
            return moves, status
        except Exception:
            return [], ''

    global shutdown_flag
    while not shutdown_flag:
        if os.path.exists(GAME_STATUS_PATH):
            moves, status = parse_moves_from_xml(GAME_STATUS_PATH)
            if len(moves) > len(last_moves):
                for mv in moves[len(last_moves):]:
                    who, col = mv
                    if who == 'computer':
                        cmd = f'<Move Column="{col}"/>'
                        robot_commands.append(cmd)
                last_moves = moves
            if status in ('player_win', 'computer_win', 'tie'):
                break
        time.sleep(poll_interval)

    return robot_commands


def write_robot_xml(commands, output_path=ROBOT_XML_OUTPUT):
    try:
        root = ET.Element('commands')
        for c in commands:
            try:
                elem = ET.fromstring(c)
                root.append(elem)
            except Exception:
                cmd_el = ET.SubElement(root, 'cmd')
                cmd_el.text = str(c)

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print('Wrote robot XML to', output_path)
    except Exception as e:
        print('Failed to write robot XML:', e)


def main():
    import processing.captureCamera as capmod

    parent_pipe, child_pipe = Pipe()
    cam_proc = Process(target=capmod.main, args=(child_pipe,), daemon=True)
    cam_proc.start()

    shm_name = None
    frame_w = getattr(capmod, 'FRAME_WIDTH', 640)
    frame_h = getattr(capmod, 'FRAME_HEIGHT', 480)
    channels = getattr(capmod, 'CHANNELS', 3)

    start_time = time.time()
    while time.time() - start_time < 10:
        if parent_pipe.poll():
            shm_name = parent_pipe.recv()
            if shm_name == 'ERROR':
                print('Camera failed to start')
            break
        time.sleep(0.05)

    crop_thread = None
    if shm_name and shm_name != 'ERROR':
        crop_thread = save_crops_from_shm(shm_name, frame_w, frame_h, channels, interval=1.5)

    detect_proc = None
    tracker_proc = None
    try:
        detect_proc = subprocess.Popen([sys.executable, '-m', 'processing.detection'], cwd=BASE_DIR)
    except Exception as e:
        print('Failed to start detection:', e)
    try:
        tracker_proc = subprocess.Popen([sys.executable, '-m', 'processing.tracker'], cwd=BASE_DIR)
    except Exception as e:
        print('Failed to start tracker:', e)

    game_proc = None
    try:
        game_proc = subprocess.Popen([sys.executable, '-m', 'processing.connectFour'], cwd=PROCESSING_DIR)
    except Exception as e:
        print('Failed to start game engine:', e)

    try:
        robot_commands = tail_game_moves(poll_interval=0.5)
    except KeyboardInterrupt:
        robot_commands = []

    global shutdown_flag
    shutdown_flag = True

    def safe_terminate(p):
        try:
            if p and p.poll() is None:
                p.terminate()
                p.wait(timeout=2)
        except Exception:
            pass

    safe_terminate(game_proc)
    safe_terminate(detect_proc)
    safe_terminate(tracker_proc)

    if cam_proc and cam_proc.is_alive():
        try:
            cam_proc.terminate()
            cam_proc.join(timeout=1)
        except Exception:
            pass

    write_robot_xml(robot_commands)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
