
import math
import random
import numpy as np


class MinMaxer:
    ROWS = 6
    COLS = 7
    EMPTY = 0
    SELF = -1   # AI / robot
    OPP = 1     # opponent

    @staticmethod
    def calculate_move(board_1d, depth=4):
        """Receive a 1D board (length 42) and return (new_board_1d, move_index).
        move_index is 0..41 where the piece is placed (or -1 if no move).
        Board indexing/shape: rows=6, cols=7, row 0 = bottom. index = row*7 + col.
        """
        board = np.array(board_1d, dtype=int).reshape((MinMaxer.ROWS, MinMaxer.COLS))

        score, best_col = MinMaxer.minimax(board, depth, -math.inf, math.inf, True)
        if best_col is None:
            return board.flatten(), -1

        row = MinMaxer.get_next_available_row(board, best_col)
        if row is None:
            return board.flatten(), -1

        MinMaxer.drop_piece(board, row, best_col, MinMaxer.SELF)
        return board.flatten(), int(row * MinMaxer.COLS + best_col)

    @staticmethod
    def is_valid_location(board, col):
        return board[MinMaxer.ROWS - 1, col] == MinMaxer.EMPTY

    @staticmethod
    def get_next_available_row(board, col):
        for r in range(MinMaxer.ROWS):
            if board[r, col] == MinMaxer.EMPTY:
                return r
        return None

    @staticmethod
    def drop_piece(board, row, col, piece):
        board[row, col] = piece

    @staticmethod
    def check_win(board, piece):
        # horizontal
        for c in range(MinMaxer.COLS - 3):
            for r in range(MinMaxer.ROWS):
                if board[r, c] == piece and board[r, c+1] == piece and board[r, c+2] == piece and board[r, c+3] == piece:
                    return True
        # vertical
        for c in range(MinMaxer.COLS):
            for r in range(MinMaxer.ROWS - 3):
                if board[r, c] == piece and board[r+1, c] == piece and board[r+2, c] == piece and board[r+3, c] == piece:
                    return True
        # diag up-right
        for c in range(MinMaxer.COLS - 3):
            for r in range(MinMaxer.ROWS - 3):
                if board[r, c] == piece and board[r+1, c+1] == piece and board[r+2, c+2] == piece and board[r+3, c+3] == piece:
                    return True
        # diag down-right
        for c in range(MinMaxer.COLS - 3):
            for r in range(3, MinMaxer.ROWS):
                if board[r, c] == piece and board[r-1, c+1] == piece and board[r-2, c+2] == piece and board[r-3, c+3] == piece:
                    return True
        return False

    @staticmethod
    def evaluate_window(window):
        score = 0
        self_count = window.count(MinMaxer.SELF)
        opp_count = window.count(MinMaxer.OPP)
        empty_count = window.count(MinMaxer.EMPTY)

        if self_count == 4:
            score += 100000
        elif self_count == 3 and empty_count == 1:
            score += 100
        elif self_count == 2 and empty_count == 2:
            score += 10

        if opp_count == 4:
            score -= 100000
        elif opp_count == 3 and empty_count == 1:
            score -= 80
        elif opp_count == 2 and empty_count == 2:
            score -= 5

        return score

    @staticmethod
    def evaluate_board(board):
        score = 0
        # center column preference
        center_array = [int(x) for x in list(board[:, MinMaxer.COLS // 2])]
        score += center_array.count(MinMaxer.SELF) * 3

        for r in range(MinMaxer.ROWS):
            for c in range(MinMaxer.COLS):
                # horizontal
                if c + 3 < MinMaxer.COLS:
                    window = [int(board[r, c+i]) for i in range(4)]
                    score += MinMaxer.evaluate_window(window)
                # vertical
                if r + 3 < MinMaxer.ROWS:
                    window = [int(board[r+i, c]) for i in range(4)]
                    score += MinMaxer.evaluate_window(window)
                # diag up-right
                if r + 3 < MinMaxer.ROWS and c + 3 < MinMaxer.COLS:
                    window = [int(board[r+i, c+i]) for i in range(4)]
                    score += MinMaxer.evaluate_window(window)
                # diag down-right
                if r - 3 >= 0 and c + 3 < MinMaxer.COLS:
                    window = [int(board[r-i, c+i]) for i in range(4)]
                    score += MinMaxer.evaluate_window(window)

        return score

    @staticmethod
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_cols = [c for c in range(MinMaxer.COLS) if MinMaxer.is_valid_location(board, c)]

        is_terminal = MinMaxer.check_win(board, MinMaxer.SELF) or MinMaxer.check_win(board, MinMaxer.OPP) or len(valid_cols) == 0
        if depth == 0 or is_terminal:
            if MinMaxer.check_win(board, MinMaxer.SELF):
                return (math.inf, None)
            elif MinMaxer.check_win(board, MinMaxer.OPP):
                return (-math.inf, None)
            else:
                return (MinMaxer.evaluate_board(board), None)

        if maximizing_player:
            value = -math.inf
            best_col = random.choice(valid_cols) if valid_cols else None
            for col in valid_cols:
                row = MinMaxer.get_next_available_row(board, col)
                temp = board.copy()
                MinMaxer.drop_piece(temp, row, col, MinMaxer.SELF)
                new_score, _ = MinMaxer.minimax(temp, depth - 1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_col
        else:
            value = math.inf
            best_col = random.choice(valid_cols) if valid_cols else None
            for col in valid_cols:
                row = MinMaxer.get_next_available_row(board, col)
                temp = board.copy()
                MinMaxer.drop_piece(temp, row, col, MinMaxer.OPP)
                new_score, _ = MinMaxer.minimax(temp, depth - 1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_col
