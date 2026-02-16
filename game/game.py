import time
import numpy as np
from minMaxer import MinMaxer
from detection.boardDetection import BoardDetection


class Game:
    
    def __init__(self):
        self.board = np.zeros(42, dtype=int)  # 0 for empty, 1 for player, -1 for robot
        self.n_turn = 0

    def play_robot(self):
        self.board, move = MinMaxer.calculate_move(self.board)
        return move

    def play_player(self):
        self.board = BoardDetection.detect_board(self.board)