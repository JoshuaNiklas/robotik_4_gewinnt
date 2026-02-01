import os
import re
import sys
import time
import signal
import xml.etree.ElementTree as ET
from paddleocr import TextRecognition

# --------------------------------------------------
# Stop handling
# --------------------------------------------------
running = True
XML_FILE = './processing/board_detection.xml'

def write_xml(board_state):
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        root.find('board_state').text = str(board_state)
        tree.write(XML_FILE)
    except Exception as e:
        print(f"Error writing XML: {e}")  # Write updated game status to XML

def handle_stop(signum, frame):
    global running
    print("Tracker stopping...")
    running = False


def initialize_xml():
    if not os.path.exists(XML_FILE):
        root = ET.Element("detection")
        board_state = ET.SubElement(root, "board_state")
        board_state.text = "[]"
        tree = ET.ElementTree(root)
        tree.write(XML_FILE)
        print(f"XML file '{XML_FILE}' initialized.")
    else:
        root = ET.Element("detection")
        board_state = ET.SubElement(root, "board_state")
        board_state.text = "[]"
        tree = ET.ElementTree(root)
        tree.write(XML_FILE)
        print(f"XML file '{XML_FILE}' reset.")  # Initialize or reset XML file

signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)

# --------------------------------------------------
# Path setup
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
image_folder = os.path.join(DATA_DIR, "output", "cells")

# --------------------------------------------------
# Initialize PaddleOCR
# --------------------------------------------------
model = TextRecognition(model_name="en_PP-OCRv5_mobile_rec")

def extract_numeric(filename):
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(0))
    return float('inf')

# --------------------------------------------------
# Validating text for Connect Four
# --------------------------------------------------
def validate_text(text):
    valid_characters = ['X', 'O', 'x', 'o', '0']
    if text.upper() in valid_characters:
        return text.upper()
    return ""

# --------------------------------------------------
# Infinite processing loop
# --------------------------------------------------
initialize_xml()

while running:
    detected_texts = []

    image_files = sorted(
        [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))],
        key=extract_numeric
    )

    for filename in image_files:
        if not running:
            break

        image_path = os.path.join(image_folder, filename)
        output = model.predict(input=image_path, batch_size=1)

        if not output:
            detected_texts.append({
                'input_path': image_path,
                'text': "",
                'score': 0.0,
            })
        else:
            for result in output:
                detected_text = result.get('rec_text', "")
                validated_text = validate_text(detected_text)  # Validate the detected text
                detected_texts.append({
                    'input_path': image_path,
                    'text': validated_text,  # Use validated text
                    'score': result.get('rec_score', 0.0),
                })
    
    detected_texts = detected_texts[:42]
    
    if (len(detected_texts) < 42):
        print("Detection faild: not enough cells")
    
    rows, cols = 6, 7
    detected_texts_2d = []

    for i in range(0, len(detected_texts), cols):
        row = []
        for j in range(cols):
            if i + j < len(detected_texts):
                row.append(detected_texts[i + j]['text'])
            else:
                row.append("")
        detected_texts_2d.append(row)

    for row in detected_texts_2d:
        print(row)

    write_xml(detected_texts_2d)

    # Preventing overload
    time.sleep(0.5)

print("Tracker exited cleanly")
sys.exit(0)
