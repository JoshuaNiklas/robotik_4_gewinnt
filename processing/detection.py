from paddleocr import TableCellsDetection, TableStructureRecognition
import numpy as np
import cv2
import os
import time

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------
CROP_IMAGE_PATH = "./data/crop.png"
OUTPUT_DIR = "./data/output/cells"
PROCESSED_IMAGE_PATH = "./data/processed_live.png"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Detection: Waiting for crop.png...")

    # ----------------------------------------------------------
    # Load models (DO NOT CHANGE)
    # ----------------------------------------------------------
    model_cells = TableCellsDetection(
        model_name="RT-DETR-L_wired_table_cell_det"
    )
    model_structure = TableStructureRecognition(
        model_name="RT-DETR-L_wired_table_cell_det"
    )

    # ----------------------------------------------------------
    # Main loop
    # ----------------------------------------------------------
    while True:
        if not os.path.exists(CROP_IMAGE_PATH):
            time.sleep(0.5)
            continue

        frame = cv2.imread(CROP_IMAGE_PATH)

        if frame is None:
            time.sleep(0.5)
            continue

        frame = cv2.resize(frame, (640, 480))

        print("Detection: Processing crop.png")

        # ------------------------------------------------------
        # Step 1: Table cell detection
        # ------------------------------------------------------
        output_cells = model_cells.predict(
            frame,
            threshold=0.6,
            batch_size=1
        )

        all_cells = []
        for res in output_cells:
            if 'boxes' in res:
                for box in res['boxes']:
                    x1, y1, x2, y2 = map(int, box['coordinate'])
                    all_cells.append((x1, y1, x2, y2))
                    
        # ------------------------------------------------------
        # Optimized row-wise ordering
        # ------------------------------------------------------
        cells_with_center = []
        for x1, y1, x2, y2 in all_cells:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            cells_with_center.append((x1, y1, x2, y2, cx, cy))

        cells_with_center.sort(key=lambda c: c[5])

        rows = []
        ROW_THRESHOLD = 15

        for cell in cells_with_center:
            placed = False
            for row in rows:
                if abs(cell[5] - row[0][5]) < ROW_THRESHOLD:
                    row.append(cell)
                    placed = True
                    break
            if not placed:
                rows.append([cell])

        for row in rows:
            row.sort(key=lambda c: c[4])

        all_cells_sorted = [
            (x1, y1, x2, y2)
            for row in rows
            for (x1, y1, x2, y2, _, _) in row
        ]

        # ------------------------------------------------------
        # Crop detected cells
        # ------------------------------------------------------
        for idx, (x1, y1, x2, y2) in enumerate(all_cells_sorted, start=1):
            crop = frame[y1:y2, x1:x2]

            save_path = os.path.join(
                OUTPUT_DIR,
                f"cell_{idx:02d}.png"
            )

            cv2.imwrite(save_path, crop)
            print("Saved:", save_path)

        # ------------------------------------------------------
        # Step 2: Table structure
        # ------------------------------------------------------
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, processed_image = cv2.threshold(
            gray, 150, 255, cv2.THRESH_BINARY
        )

        cv2.imwrite(PROCESSED_IMAGE_PATH, processed_image)

        output_structure = model_structure.predict(
            processed_image,
            batch_size=1
        )

        print("Structure boxes:", output_structure[0]['boxes'])

        # detection rate
        time.sleep(2)

if __name__ == "__main__":
    main()