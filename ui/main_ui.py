import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from multiprocessing import Process, Pipe, shared_memory
import numpy as np
from PIL import Image, ImageTk
import cv2
import yaml
import os
import logging
from processing.captureCamera import main as camera_main
from tkinter import messagebox
import xml.etree.ElementTree as ET

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
COLOR_CHANNELS = 3
FRAMES_PER_SECOND = 30
SAVE_INTERVAL_MS = 2000  # 2 secs
CROP_FILENAME = "crop.png"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
DATA_DIR = os.path.join(BASE_DIR, "data")
CROP_SAVE_PATH = os.path.join(DATA_DIR, CROP_FILENAME)
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
GAME_STATUS_PATH = os.path.join(PROCESSING_DIR, "game_status.xml")

ROW_COUNT = 6
COLUMN_COUNT = 7
EMPTY = 0
PLAYER = 1  # Computer and 'X'
COMPUTER = 2  # Player and 'O'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ------------------------------------------------------------------
# Image utilities
# ------------------------------------------------------------------
def crop_to_black_frame(
    image: np.ndarray,
    quad_points: np.ndarray
) -> np.ndarray | None:
    """
    Crop image inside a quadrilateral and return a rectangular black-framed image.
    - Safe against out-of-bounds points
    - Safe against zero-area crops
    - Never returns an empty array
    """

    if image is None or image.size == 0:
        return None

    if quad_points is None or len(quad_points) != 4:
        return None

    h, w = image.shape[:2]

    points = np.array(quad_points, dtype=np.int32)

    points[:, 0] = np.clip(points[:, 0], 0, w - 1)
    points[:, 1] = np.clip(points[:, 1], 0, h - 1)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [points], 255)

    masked = cv2.bitwise_and(image, image, mask=mask)

    x_min = int(np.min(points[:, 0]))
    x_max = int(np.max(points[:, 0]))
    y_min = int(np.min(points[:, 1]))
    y_max = int(np.max(points[:, 1]))

    if x_max <= x_min or y_max <= y_min:
        logging.warning("Invalid crop box: %s", points.tolist())
        return None

    cropped = masked[y_min:y_max, x_min:x_max]

    if cropped.size == 0:
        return None

    black_frame = np.zeros_like(cropped)
    black_frame[:] = cropped

    return black_frame


def order_quad_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.int32)

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect

def load_points_from_yaml(file_path: str):
    """Load quadrilateral points from YAML file."""
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        points = [(p["x"], p["y"]) for p in data["points"]]
        return points, np.array(points, dtype=np.float32)

    except FileNotFoundError:
        logging.error("YAML file not found: %s", file_path)
    except Exception:
        logging.exception("Invalid YAML file")

    return [], None

def read_xml():
    """Parse the XML to get the board state."""
    try:
        tree = ET.parse(GAME_STATUS_PATH)
        root = tree.getroot()

        # Extract the board state as a string
        board_state_str = root.find("board_state").text
        board_state = eval(board_state_str)

        return board_state
    except Exception as e:
        print(f"Error reading XML file: {e}")
        return []


# ------------------------------------------------------------------
# UI Class
# ------------------------------------------------------------------
class CameraInterface:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Camera Controller")

        self.board = [[0 for _ in range(7)] for _ in range(6)]

        self._init_tabs()
        self._init_camera_state()
        self._init_camera_tab()
        self._init_blank_tab()
        self._init_crop_tab()
        self._init_detection_tab()
        self._init_game_tab()

        self.last_cropped_frame = None
        os.makedirs(DATA_DIR, exist_ok=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # --------------------------------------------------------------
    # Initialization
    # --------------------------------------------------------------
    def _init_tabs(self):
        self.notebook = ttk.Notebook(self.root)

        self.camera_tab = ttk.Frame(self.notebook)
        self.blank_tab = ttk.Frame(self.notebook)
        self.crop_tab = ttk.Frame(self.notebook)
        self.detection_tab = ttk.Frame(self.notebook)
        self.game_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.camera_tab, text="Camera")
        self.notebook.add(self.blank_tab, text="Crop Pos")
        self.notebook.add(self.crop_tab, text="Crop")
        self.notebook.add(self.detection_tab, text="Detection")
        self.notebook.add(self.game_tab, text="Game")
        self.notebook.pack(expand=True, fill="both")

    def _init_camera_state(self):
        self.camera_process = None
        self.camera_pipe = None
        self.camera_running = False

        self.output_shared_memory = None
        self.input_shared_memory = None

        self.camera_frame_buffer = None
        self.snapshot_frame = None

        self.quad_points = []
        self.quad_lines = []
        self.selected_point_index = None

    # --------------------------------------------------------------
    # Camera Tab
    # --------------------------------------------------------------
    def _init_camera_tab(self):
        self.status_label = tk.Label(
            self.camera_tab, text="Camera: STOPPED",
            bg="red", fg="white", width=30
        )
        self.status_label.pack(pady=10)

        self.shm_label = tk.Label(self.camera_tab, text="Shared Memory: -")
        self.shm_label.pack()

        self.toggle_button = tk.Button(
            self.camera_tab, text="Start Camera",
            command=self.toggle_camera, width=20
        )
        self.toggle_button.pack(pady=10)

        self.preview_canvas = tk.Canvas(
            self.camera_tab,
            width=FRAME_WIDTH,
            height=FRAME_HEIGHT
        )
        self.preview_canvas.pack()

        self.preview_image_id = None

    def toggle_camera(self):
        if self.camera_running:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        if self.camera_process and self.camera_process.is_alive():
            return

        self.camera_pipe, child_pipe = Pipe()
        self.camera_process = Process(
            target=camera_main,
            args=(child_pipe,),
            daemon=True
        )
        self.camera_process.start()

        self.camera_running = True
        self.toggle_button.config(text="Stop Camera")
        self.status_label.config(text="Camera: STARTING", bg="orange")

        self.root.after(100, self._check_camera_ready)

    def stop_camera(self):
        if self.camera_process:
            self.camera_process.terminate()

        self.camera_process = None
        self.camera_pipe = None
        self.camera_running = False

        self.toggle_button.config(text="Start Camera")
        self.status_label.config(text="Camera: STOPPED", bg="red")
        self.shm_label.config(text="Shared Memory: -")

        if self.output_shared_memory:
            try:
                self.output_shared_memory.close()
                self.output_shared_memory.unlink()
            except FileNotFoundError:
                pass

        self.output_shared_memory = None
        self.camera_frame_buffer = None

    def _check_camera_ready(self):
        if not self.camera_pipe or not self.camera_running:
            return

        try:
            if self.camera_pipe.poll():
                shm_name = self.camera_pipe.recv()

                if shm_name == "ERROR":
                    logging.error("Camera process reported an error")
                    self.stop_camera()
                    return

                self.output_shared_memory = shared_memory.SharedMemory(name=shm_name)
                self.camera_frame_buffer = np.ndarray(
                    (FRAME_HEIGHT, FRAME_WIDTH, COLOR_CHANNELS),
                    dtype=np.uint8,
                    buffer=self.output_shared_memory.buf
                )

                self.status_label.config(text="Camera: RUNNING", bg="green")
                self.shm_label.config(text=f"Shared Memory: {shm_name}")

                self._update_preview()
                return

        except Exception as e:
            logging.exception("Failed while waiting for camera")
            self.stop_camera()
            return

        self.root.after(50, self._check_camera_ready)


    def _update_preview(self):
        if not self.camera_running or self.camera_frame_buffer is None:
            return

        frame = cv2.cvtColor(self.camera_frame_buffer, cv2.COLOR_BGR2RGB)
        image = ImageTk.PhotoImage(Image.fromarray(frame))

        if self.preview_image_id is None:
            self.preview_image_id = self.preview_canvas.create_image(
                0, 0, anchor="nw", image=image
            )
        else:
            self.preview_canvas.itemconfig(self.preview_image_id, image=image)

        self.preview_canvas.image = image
        self.root.after(int(1000 / FRAMES_PER_SECOND), self._update_preview)

    # --------------------------------------------------------------
    # Blank Tab
    # --------------------------------------------------------------
    def _init_blank_tab(self):
        tk.Button(
            self.blank_tab,
            text="Take Snapshot",
            command=self.take_snapshot
        ).pack(pady=5)

        self.blank_canvas = tk.Canvas(
            self.blank_tab,
            width=FRAME_WIDTH,
            height=FRAME_HEIGHT
        )
        self.blank_canvas.pack()

        self.blank_image_id = None

        self.blank_canvas.bind("<Button-1>", self.on_blank_click)
        self.blank_canvas.bind("<B1-Motion>", self.on_blank_drag)
        self.blank_canvas.bind("<ButtonRelease-1>", self.on_blank_release)

        tk.Button(
            self.blank_tab,
            text="Save Crop Position",
            command=self.save_crop_points
        ).pack(pady=5)

    def take_snapshot(self):
        if self.camera_frame_buffer is None:
            logging.warning("No frame available for snapshot")
            return

        self.snapshot_frame = self.camera_frame_buffer.copy()
        self.quad_points.clear()

        for line in self.quad_lines:
            self.blank_canvas.delete(line)
        self.quad_lines.clear()

        self._update_blank_preview()

    def _update_blank_preview(self):
        if self.snapshot_frame is None:
            return

        frame = cv2.cvtColor(self.snapshot_frame, cv2.COLOR_BGR2RGB)
        image = ImageTk.PhotoImage(Image.fromarray(frame))

        if self.blank_image_id is None:
            self.blank_image_id = self.blank_canvas.create_image(
                0, 0, anchor="nw", image=image
            )
        else:
            self.blank_canvas.itemconfig(self.blank_image_id, image=image)

        self.blank_canvas.image = image
        self._draw_quad()

    def save_crop_points(self):
        if len(self.quad_points) != 4:
            logging.warning("Exactly 4 points are required")
            return

        config = {
            "points": [
                {
                    "x": x / (FRAME_WIDTH - 1),
                    "y": y / (FRAME_HEIGHT - 1)
                }
                for x, y in self.quad_points
            ]
        }

        with open(CONFIG_PATH, "w") as f:
            yaml.dump(config, f)

        logging.info("Crop points saved to %s", CONFIG_PATH)


    # --------------------------------------------------------------
    # Crop Tab
    # --------------------------------------------------------------
    def _init_crop_tab(self):
        tk.Button(
            self.crop_tab,
            text="Crop Image",
            command=self.start_crop_preview
        ).pack(pady=10)

        self.crop_canvas = tk.Canvas(
            self.crop_tab,
            width=FRAME_WIDTH,
            height=FRAME_HEIGHT
        )
        self.crop_canvas.pack()

        self.crop_image_id = None

    def start_crop_preview(self):
        _, points_array = load_points_from_yaml(CONFIG_PATH)
        if points_array is None or len(points_array) != 4:
            return

        self.crop_points = np.array([
            (
                min(max(int(p[0] * FRAME_WIDTH), 0), FRAME_WIDTH - 1),
                min(max(int(p[1] * FRAME_HEIGHT), 0), FRAME_HEIGHT - 1),
            )
            for p in points_array
        ], dtype=np.int32)

        if not hasattr(self, "_crop_saving_started"):
            self._crop_saving_started = True
            self.root.after(SAVE_INTERVAL_MS, self._save_cropped_frame_periodically)

        self._update_crop_preview()

    def _update_crop_preview(self):
        if not self.camera_running:
            return

        if self.camera_frame_buffer is None:
            return

        if not hasattr(self, "crop_points") or self.crop_points is None:
            return

        ordered_points = order_quad_points(self.crop_points)

        cropped = crop_to_black_frame(
            self.camera_frame_buffer,
            ordered_points
        )

        if cropped is None or cropped.size == 0:
            return

        self.last_cropped_frame = cropped.copy()

        rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        image = ImageTk.PhotoImage(Image.fromarray(rgb))

        if self.crop_image_id is None:
            self.crop_image_id = self.crop_canvas.create_image(
                0, 0, anchor="nw", image=image
            )
        else:
            self.crop_canvas.itemconfig(self.crop_image_id, image=image)

        self.crop_canvas.image = image

        self.root.after(
            int(1000 / FRAMES_PER_SECOND),
            self._update_crop_preview
        )

    def _save_cropped_frame_periodically(self):
        if self.last_cropped_frame is not None:
            try:
                cv2.imwrite(CROP_SAVE_PATH, self.last_cropped_frame)
            except Exception:
                logging.exception("Failed to save cropped frame")

        self.root.after(SAVE_INTERVAL_MS, self._save_cropped_frame_periodically)

    # --------------------------------------------------------------
    # Detection Tab
    # --------------------------------------------------------------
    def _init_detection_tab(self):
        self.detection_process = None
        self.detection_running = False
    
        self.tracker_process = None
        self.tracker_running = False

        self.detect_status_label = tk.Label(
            self.detection_tab,
            text="Detection: STOPPED",
            bg="red",
            fg="white",
            width=30
        )
        self.detect_status_label.pack(pady=10)

        self.start_detect_button = tk.Button(
            self.detection_tab,
            text="Start Detection",
            width=20,
            command=self.start_detection
        )
        self.start_detect_button.pack(pady=5)

        self.stop_detect_button = tk.Button(
            self.detection_tab,
            text="Stop Detection",
            width=20,
            command=self.stop_detection,
            state="disabled"
        )
        self.stop_detect_button.pack(pady=5)

        ttk.Separator(self.detection_tab, orient="horizontal").pack(fill="x", pady=10)

        self.tracker_status_label = tk.Label(
            self.detection_tab,
            text="Tracker: STOPPED",
            bg="red",
            fg="white",
            width=30
        )
        self.tracker_status_label.pack(pady=10)

        self.start_tracker_button = tk.Button(
            self.detection_tab,
            text="Start Tracker",
            width=20,
            command=self.start_tracker
        )
        self.start_tracker_button.pack(pady=5)

        self.stop_tracker_button = tk.Button(
            self.detection_tab,
            text="Stop Tracker",
            width=20,
            command=self.stop_tracker,
            state="disabled"
        )
        self.stop_tracker_button.pack(pady=5)


    def start_detection(self):
        if self.detection_process is not None:
            return

        self.detection_process = subprocess.Popen(
            [sys.executable, "-m", "processing.detection"],
            cwd=os.getcwd()
        )

        self.detect_status_label.config(
            text="Detection: RUNNING",
            bg="green"
        )

        self.start_detect_button.config(state="disabled")
        self.stop_detect_button.config(state="normal")


    def stop_detection(self):
        if self.detection_process is None:
            return

        self.detection_process.terminate()
        self.detection_process.wait(timeout=2)

        self.detection_process = None

        self.detect_status_label.config(
            text="Detection: STOPPED",
            bg="red"
        )

        self.start_detect_button.config(state="normal")
        self.stop_detect_button.config(state="disabled")

    def start_tracker(self):
        if self.tracker_process is not None:
            return

        self.tracker_process = subprocess.Popen(
            [sys.executable, "-m", "processing.tracker"],
            cwd=os.getcwd()
        )

        self.tracker_status_label.config(
            text="Tracker: RUNNING",
            bg="green"
        )

        self.start_tracker_button.config(state="disabled")
        self.stop_tracker_button.config(state="normal")


    def stop_tracker(self):
        if self.tracker_process is None:
            return

        self.tracker_process.terminate()
        self.tracker_process.wait(timeout=2)

        self.tracker_process = None

        self.tracker_status_label.config(
            text="Tracker: STOPPED",
            bg="red"
        )

        self.start_tracker_button.config(state="normal")
        self.stop_tracker_button.config(state="disabled")

    # --------------------------------------------------------------
    # Game Tab
    # TODO Debug and Test
    # --------------------------------------------------------------
    def _init_game_tab(self):
        # Create a 7x6 grid of labels (for the Connect Four board)
        self.grid_labels = []
        for row in range(6):
            row_labels = []
            for col in range(7):
                label = tk.Label(self.game_tab, width=6, height=3, relief="solid", bg="white")
                label.grid(row=row, column=col, padx=2, pady=2)
                row_labels.append(label)
            self.grid_labels.append(row_labels)

        self.update_board()

    def update_board(self):
        board_state = read_xml()

        if board_state:
            for row in range(6):
                for col in range(7):
                    cell_value = board_state[row][col]
                    if cell_value == 1:
                        self.grid_labels[row][col].config(bg="red")  # Player's piece
                    elif cell_value == 2:
                        self.grid_labels[row][col].config(bg="yellow")  # Computer's piece
                    else:
                        self.grid_labels[row][col].config(bg="white")  # Empty cell

        self.root.after(1000, self.update_board)

    # --------------------------------------------------------------
    # Quadrilateral interaction
    # --------------------------------------------------------------
    def on_blank_click(self, event):
        for i, (x, y) in enumerate(self.quad_points):
            if (event.x - x) ** 2 + (event.y - y) ** 2 < 100:
                self.selected_point_index = i
                return

        if len(self.quad_points) < 4:
            self.quad_points.append((event.x, event.y))
            self._draw_quad()

    def on_blank_drag(self, event):
        if self.selected_point_index is not None:
            self.quad_points[self.selected_point_index] = (event.x, event.y)
            self._draw_quad()

    def on_blank_release(self, _):
        self.selected_point_index = None

    def _draw_quad(self):
        for line in self.quad_lines:
            self.blank_canvas.delete(line)
        self.quad_lines.clear()

        for i in range(len(self.quad_points) - 1):
            self.quad_lines.append(
                self.blank_canvas.create_line(
                    *self.quad_points[i],
                    *self.quad_points[i + 1],
                    fill="red",
                    width=2
                )
            )

        if len(self.quad_points) == 4:
            self.quad_lines.append(
                self.blank_canvas.create_line(
                    *self.quad_points[3],
                    *self.quad_points[0],
                    fill="red",
                    width=2
                )
            )

    # --------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------
    def on_close(self):
        logging.info("Shutting down UI")
        self.stop_detection()
        self.stop_tracker()
        self.stop_camera()
        self.root.destroy()


def start_ui():
    root = tk.Tk()
    CameraInterface(root)
    root.mainloop()
