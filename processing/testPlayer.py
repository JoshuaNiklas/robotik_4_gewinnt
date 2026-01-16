import numpy as np

ROW_COUNT = 6
COLUMN_COUNT = 7
EMPTY = 0
PLAYER = 1  # Player is 'X'
COMPUTER = 2  # Computer is 'O'

def print_board(board):
    print(np.flip(board, 0))

def is_valid_location(board, col):
    return board[ROW_COUNT-1][col] == 0

def get_next_available_row(board, col):
    for row in range(ROW_COUNT):
        if board[row][col] == 0:
            return row

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def check_win(board, piece):
    # Horizontal win
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Vertical win
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT-3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Diagonal win (bottom-left to top-right)
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT-3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Diagonal win (top-left to bottom-right)
    for c in range(COLUMN_COUNT-3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

    return False

def play_game():
    board = np.zeros((ROW_COUNT, COLUMN_COUNT), int)
    game_over = False
    turn = 0

    while not game_over:
        print_board(board)
        
        if turn % 2 == 0:  # Player's turn
            player = PLAYER
            player_name = "Player (X)"
            
            valid_move = False
            while not valid_move:
                try:
                    col = int(input(f"{player_name}, choose a column (1-7): ")) - 1
                    if 0 <= col < COLUMN_COUNT and is_valid_location(board, col):
                        valid_move = True
                    else:
                        print("Invalid move! Try again.")
                except ValueError:
                    print("Please enter a number between 1 and 7.")
            
            row = get_next_available_row(board, col)
            drop_piece(board, row, col, player)

            if check_win(board, player):
                print_board(board)
                print("Player wins!")
                game_over = True

        else:  # Computer's turn
            print("Computer is thinking...")

            # Import the computer's move function from Program 1
            from connectFour import get_computer_move_response
            
            col = get_computer_move_response(board, 4)  # Depth is set to 4 for better decision-making
            row = get_next_available_row(board, col)
            drop_piece(board, row, col, COMPUTER)

            if check_win(board, COMPUTER):
                print_board(board)
                print("Computer wins!")
                game_over = True

        if np.all(board != 0):
            print_board(board)
            print("It's a tie!")
            game_over = True

        turn += 1

if __name__ == "__main__":
    play_game()
