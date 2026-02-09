import sys
import ast

class BoardAnalyzer:
    def __init__(self):
        pass

    def analyze(self, board_1, board_2):
        if self.check_valid_placement(board_1) and self.check_valid_placement(board_2):
            res = self.subtract_boards(board_1, board_2)
            if self.count_non_empty(res) == 0:
                res = self.subtract_boards(board_2, board_1)
                res = self.count_non_empty(res)
                if res == 0:
                    return -1  # No changes detected
                if res == 1:
                    res = self.subtract_boards(board_2, board_1)
                    column = self.get_non_empty_column(res)
                    # index = self.get_non_empty_index(res)            
                    return column
                    #return index
        return None  # Invalid situation

    def get_non_empty_index(self, board):
        for i, sublist in enumerate(board):
            for j, element in enumerate(sublist):
                if element:
                    one_d_index = i * len(sublist) + j
                    print(f"First non-empty element is at index: {one_d_index}")
                    return one_d_index
            else:
                continue
    
    def get_non_empty_column(self, board):
        for row in board:
            for col_idx, cell in enumerate(row):
                if cell != '':
                    return col_idx
        return None

    def count_non_empty(self, board):
        return sum(1 for row in board for cell in row if cell != '')

    def subtract_boards(self, board_1, board_2):
        result = []
        
        for row_b3, row_b2 in zip(board_1, board_2):
            result_row = []
            for cell_b3, cell_b2 in zip(row_b3, row_b2):
                if cell_b3 != '' and cell_b3 != cell_b2:
                    result_row.append(cell_b3)
                else:
                    result_row.append('')
            result.append(result_row)
        
        return result

    def check_valid_placement(self, board_state):
        for col in range(len(board_state[0])):
            column = [row[col] for row in board_state]

            for row in range(len(column)):
                if column[row] != '':
                    for below_row in range(row + 1, len(column)):
                        if column[below_row] == '':
                            print("Invalid placement: Symbol placed above an empty space")
                            return False 
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python program.py '<board_1>' '<board_2>'")
        sys.exit(1)
    
    # Parse board_1 and board_2 from command line arguments
    try:
        board_1 = ast.literal_eval(sys.argv[1])
        board_2 = ast.literal_eval(sys.argv[2])
    except (ValueError, SyntaxError):
        print("Invalid board format. Please provide valid Python list syntax.")
        sys.exit(1)
    
    # Initialize BoardAnalyzer and run the analysis
    analyzer = BoardAnalyzer()
    result = analyzer.analyze(board_1, board_2)

    if result is None:
        print("None")
    elif result == -1:
        print("-1")
    else:
        print(result)
