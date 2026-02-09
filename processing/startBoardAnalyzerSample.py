import subprocess
import sys

def run_program_with_args(board_1, board_2):
    command = [
        'python', 'boardAnalyzer.py',
        repr(board_1),
        repr(board_2)
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        print("Output of program.py:")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running program: {e}")
        print(f"stderr: {e.stderr}")
        
    except FileNotFoundError:
        print("The file 'program.py' was not found. Please make sure the program exists.")

if __name__ == "__main__":
    board_1 = [['', '', '', '', '', '', ''],
               ['', '', '', '', '', '', ''],
               ['', '', '', '', '', '', ''],
               ['', '', '', '', '', '', ''],
               ['', '', '', '', '', '', ''],
               ['', '', '', '', '', '', '']]

    board_2 = [['', '', '', '', '', '', ''],
                ['', '', '', '', '', '', ''],
                ['', '', '', '', '', '', ''],
                ['', '', '', '', '', '', ''],
                ['', '', '', '', '', '', ''],
                ['', 'X', '', '', '', '', '']]

    run_program_with_args(board_1, board_2)
