import numpy as np
import random
import math

# Constants
ROW_COUNT = 6
COLUMN_COUNT = 7
EMPTY = 0
PLAYER = 1  # Player and 'X'
COMPUTER = 2  # Computer and 'O'

# board 6x7 matrix
def create_board():
    board = np.zeros((ROW_COUNT, COLUMN_COUNT), int)
    return board

def print_board(board):
    print(np.flip(board, 0))

def is_valid_location(board, col):
    return board[ROW_COUNT-1][col] == 0

def get_next_available_row(board, col):
    for row in range(ROW_COUNT)
        if board[row][col] == 0:
            return row

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def check_win(board, piece):
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

    return False

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

    return score

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
    
    return score

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
        return min_eval, best_col

def get_computer_move(board, depth):
    _, col = minimax(board, depth, -math.inf, math.inf, True)
    return col

def get_computer_move_response(board, depth):
    col = get_computer_move(board, depth)
    return col
