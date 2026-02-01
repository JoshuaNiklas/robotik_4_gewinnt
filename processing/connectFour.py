import numpy as np
import random
import math
import xml.etree.ElementTree as ET
import os

ROW_COUNT = 6
COLUMN_COUNT = 7
EMPTY = 0
PLAYER = 1  
COMPUTER = 2  
XML_FILE = 'game_status.xml'

def create_board():
    return np.zeros((ROW_COUNT, COLUMN_COUNT), int)  # Initialize empty game board

def is_valid_location(board, col):
    return board[ROW_COUNT-1][col] == 0  # Check if column is not full

def get_next_available_row(board, col):
    for row in range(ROW_COUNT):
        if board[row][col] == 0:
            return row  # Find available row for move

def drop_piece(board, row, col, piece):
    board[row][col] = piece  # Drop piece on board

def check_win(board, piece):
    # Check all win conditions: horizontal, vertical, diagonal
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT-3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT-3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True
    for c in range(COLUMN_COUNT-3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True
    return False  # Check for winning sequence

def evaluate_board(board):
    score = 0
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT):
            if c + 3 < COLUMN_COUNT:
                window = [board[r][c+i] for i in range(4)]
                score += evaluate_window(window)
            if r + 3 < ROW_COUNT:
                window = [board[r+i][c] for i in range(4)]
                score += evaluate_window(window)
            if r + 3 < ROW_COUNT and c + 3 < COLUMN_COUNT:
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window)
            if r - 3 >= 0 and c + 3 < COLUMN_COUNT:
                window = [board[r-i][c+i] for i in range(4)]
                score += evaluate_window(window)
    return score  # Evaluate board state for AI

def evaluate_window(window):
    score = 0
    opponent = PLAYER if COMPUTER == 2 else COMPUTER
    if window.count(COMPUTER) == 4:
        score += 100
    elif window.count(COMPUTER) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(COMPUTER) == 2 and window.count(EMPTY) == 2:
        score += 2
    if window.count(PLAYER) == 3 and window.count(EMPTY) == 1:
        score -= 4
    if window.count(PLAYER) == 2 and window.count(EMPTY) == 2:
        score -= 2
    return score  # Evaluate score of four-cell window

def minimax(board, depth, alpha, beta, maximizing_player):
    valid_locations = [col for col in range(COLUMN_COUNT) if is_valid_location(board, col)]
    if depth == 0 or len(valid_locations) == 0:
        return evaluate_board(board), None
    if maximizing_player:
        max_eval = -math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_available_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, COMPUTER)
            eval_score, _ = minimax(temp_board, depth-1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_col = col
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_col
    else:
        min_eval = math.inf
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_available_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, PLAYER)
            eval_score, _ = minimax(temp_board, depth-1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_col = col
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_col  # Minimax with alpha-beta pruning

def get_computer_move(board, depth):
    _, col = minimax(board, depth, -math.inf, math.inf, True)
    return col  # Get best move for computer

def initialize_xml():
    if not os.path.exists(XML_FILE):
        root = ET.Element("game")
        player_column = ET.SubElement(root, "player_column")
        player_column.text = "-1"
        computer_column = ET.SubElement(root, "computer_column")
        computer_column.text = "-1"
        status = ET.SubElement(root, "status")
        status.text = "player_wait"
        moves = ET.SubElement(root, "moves")
        moves.text = "[]"
        board_state = ET.SubElement(root, "board_state")
        board_state.text = "[[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]"
        stop = ET.SubElement(root, "stop")
        stop.text = "0"
        tree = ET.ElementTree(root)
        tree.write(XML_FILE)
        print(f"XML file '{XML_FILE}' initialized.")
    else:
        root = ET.Element("game")
        player_column = ET.SubElement(root, "player_column")
        player_column.text = "-1"
        computer_column = ET.SubElement(root, "computer_column")
        computer_column.text = "-1"
        status = ET.SubElement(root, "status")
        status.text = "player_wait"
        moves = ET.SubElement(root, "moves")
        moves.text = "[]"
        board_state = ET.SubElement(root, "board_state")
        board_state.text = "[[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]"
        stop = ET.SubElement(root, "stop")
        stop.text = "0"
        tree = ET.ElementTree(root)
        tree.write(XML_FILE)
        print(f"XML file '{XML_FILE}' reset.")  # Initialize or reset XML file

def read_xml():
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        player_col = int(root.find('player_column').text)
        computer_col = int(root.find('computer_column').text)
        status = root.find('status').text
        stop = int(root.find('stop').text)
        moves = eval(root.find('moves').text)
        board_state = eval(root.find('board_state').text)
        return player_col, computer_col, status, stop, moves, board_state
    except Exception as e:
        print(f"Error reading XML: {e}")
        return None, None, 'error', 0, [], []  # Read current game status from XML

def write_xml(player_col, computer_col, status, stop, moves, board_state):
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
        root.find('player_column').text = str(player_col)
        root.find('computer_column').text = str(computer_col)
        root.find('status').text = status
        root.find('stop').text = str(stop)
        root.find('moves').text = str(moves)
        root.find('board_state').text = str(board_state[::-1])
        tree.write(XML_FILE)
    except Exception as e:
        print(f"Error writing XML: {e}")  # Write updated game status to XML

def play_game():
    initialize_xml()  # Ensure the XML file is initialized
    board = create_board()
    game_over = False
    turn = 0
    moves = []
    while not game_over:
        player_col, computer_col, status, stop, moves, board_state = read_xml()
        if stop == 1:
            print("The game has been stopped.")
            break
        
        if turn % 2 == 0:  # Player's turn
            if status == 'player_wait' and player_col != -1:
                if 0 <= player_col < COLUMN_COUNT and is_valid_location(board, player_col):
                    row = get_next_available_row(board, player_col)
                    drop_piece(board, row, player_col, PLAYER)
                    moves.append(('player', player_col))
                    write_xml(player_col, -1, 'computer_wait', 0, moves, board.tolist())
                    if check_win(board, PLAYER):
                        print("Player wins!")
                        write_xml(-1, computer_col, 'player_win', 0, moves, board.tolist())
                        game_over = True
                else:
                    print("Invalid move in XML! Try again.")
            else:
                print("Waiting for player to make a move...")

        else:  # Computer's turn
            if status == 'computer_wait':
                print("Computer is thinking...")
                computer_col = get_computer_move(board, 4)
                row = get_next_available_row(board, computer_col)
                drop_piece(board, row, computer_col, COMPUTER)
                moves.append(('computer', computer_col))
                write_xml(-1, computer_col, 'player_wait', 0, moves, board.tolist())
                if check_win(board, COMPUTER):
                    print("Computer wins!")
                    write_xml(-1, computer_col, 'computer_win', 0, moves, board.tolist())
                    game_over = True

        if np.all(board != 0):
            print("It's a tie!")
            write_xml(-1, -1, 'tie', 0, moves, board.tolist())
            game_over = True

        turn += 1
    initialize_xml()
    
if __name__ == "__main__":
    play_game()  # Start the game loop
