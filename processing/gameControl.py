import time
import copy
import subprocess
import xml.etree.ElementTree as ET

###########################
# Transform A->B          #
###########################
#    A       |     B      #
# .          |        .   #
# .          |        .   #
# .          |        .   #
# 0,0 . . .  |  . . . 0,0 #
###########################

def to_1d_index(row, col, num_cols=7):
    return row * num_cols + (num_cols - 1 - col)

def write_xml(xml_file, changes):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for key, value in changes.items():
            root.find(f'{key}').text = str(value)
        tree.write(xml_file)
    except Exception as e:
        print(f"Error writing XML: {e}")

def read_xml(xml_file, tags):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        vals = {}
        for tag in tags:
            val = root.find(f'{tag}').text
            vals.update({f'{tag}':val})
        return vals
        
    except Exception as e:
        print(f"Error reading XML: {e}")
        return None

def count_non_empty(board):
    return sum(1 for row in board for cell in row if cell != '')

def check_boards(board_1, board_2):
    command = [
        'python', 'boardAnalyzer.py',
        repr(board_1),
        repr(board_2)
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
                
        # handle stdout
        return (result.stdout).split("\n")[-2]
        
    except subprocess.CalledProcessError as e:
        print(f"Error running program: {e}")
        print(f"stderr: {e.stderr}")

        return "None"
        
    except FileNotFoundError:
        print("The file 'program.py' was not found. Please make sure the program exists.")

        return "None"

def game_start():
    print("Welcome to Connect Four:")
    print("\nGame Description:")
    print("1. You will play Connect Four on paper by drawing circles for your moves.")
    print("2. The robot will detect your circles and draw crosses in response.")
    print("3. The goal is the same: connect four of your marks in a row, column, or diagonal.")
    print("4. You have to press Enter after drawing the circle to continue the game.")
    print("5. Make sure the grid is clear and visible to the robot camera.")
    
    # Ask the user if they want to start
    start = input("\nDo you want to start the game? (yes/no): ").strip().lower()
    
    if start == "yes":
        print("Awesome! Prepare your paper grid and let the robot see your moves.")
        print("The game will start now...")
    else:
        print("Okay, maybe next time. bye!")

board_1 = []
board_2 = []
detection_id = 0
player_move = "None"
computer_move = "None"

# game start
game_start()

# check for empty board
res = read_xml("board_detection.xml", ["detection_id"])
detection_id = int(res["detection_id"])

write_xml("board_detection.xml", {"capture_status": 1})
print("Waiting for tracker.py to write the detection in board_detection.xml")

while(True):
    res = read_xml("board_detection.xml", ["board_state", "detection_id"])
    if (detection_id + 1 == int(res["detection_id"])):
        if (count_non_empty(eval(res["board_state"])) == 0):
            board_1 = eval(res["board_state"])
            break
        else:
            print("Please clear the board and start the game again")
            exit()
    
    time.sleep(1)

# take player move
while(True):
    input("Please draw a circle on the board and press Enter ...")

    res = read_xml("board_detection.xml", ["detection_id"])
    detection_id = int(res["detection_id"])

    write_xml("board_detection.xml", {"capture_status": 1})
    print("Waiting for tracker.py to write the detection in board_detection.xml")

    while(True):
        res = read_xml("board_detection.xml", ["board_state", "detection_id"])
        if (detection_id  + 1 == int(res["detection_id"])):
            board_2 = eval(res["board_state"])
            break
        
        time.sleep(1)

    player_move = check_boards(board_1, board_2)

    # Not a valid move
    if(player_move == "None"):
        print("Your last move was detected as invalid. Please clear the board and start the game again")
        exit()
    # Nothing was detected
    elif(player_move == "-1"):
        print("If you have already drawn a circle, it wasnt detected")
    # a valid move was detected
    else:
        break

# provide the player_move to game_status.xml so that connectFour.py can calculate the computer_move
res = read_xml("game_status.xml", ["start", "last_win_state"])

if (int(res["last_win_state"]) != 0):
    write_xml("game_status.xml", {"last_win_state":0})

if (int(res["start"]) == 0):
    print("The connectFour.py program that calculates the computers move is not running. Please start the game again !")
    exit()

print("Computer is calculating its move ...")
write_xml("game_status.xml", {"player_column":player_move})

# TODO check if the computer has calculated its move (the algorithm is supposed to calculate the move and write it to game_status.xml in less than 2 minutes)
time.sleep(2)
computer_move = read_xml("game_status.xml", ["computer_row", "computer_column"])

print(f"Selected Cell :{computer_move}")
# TODO check if it is correct
# transformed index from the algorithms solution to the robots cell selection list
computer_move = to_1d_index(int(computer_move["computer_row"]), int(computer_move["computer_column"]))
print(f"Selected Cell :{computer_move}")

# robot will draw its move
res = read_xml("robotControl.xml", ["CELL_SEL", "SYNC_VAR"])
capture_CELL_SEL = int(res["CELL_SEL"])
capture_SYNC_VAR = int(res["SYNC_VAR"])

print("the robot is drawing...")
write_xml("robotControl.xml", {"CELL_SEL": computer_move})
# wait for the robot to draw a cross and complete its movement at the boards capture position
while(True):
    res = read_xml("robotControl.xml", ["CELL_SEL", "SYNC_VAR"])

    if(int(res["SYNC_VAR"]) == capture_SYNC_VAR + 2):
        break
    time.sleep(2)

res = read_xml("game_status.xml", ["game_state"])
board_2 = eval(res["game_state"])

board_1 = copy.deepcopy(board_2)

# TODO Implement a break condition after a win situation 
# Continue game after start
while(True):
    # take player move
    while(True):
        input("Please draw a circle on the board and press Enter ...")

        res = read_xml("board_detection.xml", ["detection_id"])
        detection_id = int(res["detection_id"])

        write_xml("board_detection.xml", {"capture_status": 1})
        print("Waiting for tracker.py to write the detection in board_detection.xml")

        while(True):
            res = read_xml("board_detection.xml", ["board_state", "detection_id"])
            if (detection_id + 1 == int(res["detection_id"])):
                board_2 = eval(res["board_state"])
                break
            
            time.sleep(1)
       
        player_move = check_boards(board_1, board_2)

        # Not a valid move
        if(player_move == "None"):
            print("Your last move was detected as invalid. Please clear the board and start the game again")
            exit()
        # Nothing was detected
        elif(player_move == "-1"):
            print("If you have already drawn a circle, it wasnt detected")
        # a valid move was detected
        else:
            break

    # provide the player_move to game_status.xml so that connectFour.py can calculate the computer_move
    res = read_xml("game_status.xml", ["start", "last_win_state"])

    if (int(res["last_win_state"]) != 0):
        if(int(res["last_win_state"]) == 1):
            print("This is a Tie")
        elif(int(res["last_win_state"]) == 2):
            print("Computer wins !!!")
        elif(int(res["last_win_state"]) == 3):
            print("Player wins !!!")
            
        write_xml("game_status.xml", {"last_win_state":0})
        exit()

    if (int(res["start"]) == 0):
        print("The connectFour.py program that calculates the computers move is not running. Please start the game again !")
        exit()

    print("Computer is calculating its move ...")
    write_xml("game_status.xml", {"player_column":player_move})

    # TODO check if the computer has calculated its move (the algorithm is supposed to calculate the move and write it to game_status.xml in less than 2 minutes)
    time.sleep(2)
    computer_move = read_xml("game_status.xml", ["computer_row", "computer_column"])

    print(f"Selected Cell :{computer_move}")
    # TODO check if it is correct
    # transformed index from the algorithms solution to the robots cell selection list
    computer_move = to_1d_index(int(computer_move["computer_row"]), int(computer_move["computer_column"]))
    print(f"Calculated Selected Cell :{computer_move}")

    # robot will draw its move
    res = read_xml("robotControl.xml", ["CELL_SEL", "SYNC_VAR"])
    capture_CELL_SEL = int(res["CELL_SEL"])
    capture_SYNC_VAR = int(res["SYNC_VAR"])

    print("the robot is drawing...")
    write_xml("robotControl.xml", {"CELL_SEL": computer_move})
    # wait for the robot to draw a cross and complete its movement at the boards capture position
    while(True):
        res = read_xml("robotControl.xml", ["CELL_SEL", "SYNC_VAR"])
        if(int(res["SYNC_VAR"]) == capture_SYNC_VAR + 2):
            break
        time.sleep(2)

    res = read_xml("game_status.xml", ["game_state"])
    board_2 = eval(res["game_state"])

    board_1 = copy.deepcopy(board_2)
