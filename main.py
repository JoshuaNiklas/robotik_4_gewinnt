"""Entry point: start the bundled robotic Connect Four orchestrator.

By default we run the orchestrator which connects camera, detection,
tracker, game engine and produces the robot XML only at the end.
If you prefer the GUI, run `python -m ui.main_ui`.
"""
from run_robotic_connect_four import main as orchestrator_main


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    orchestrator_main()
