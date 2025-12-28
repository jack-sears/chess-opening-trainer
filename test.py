import chess_pgn_parser as cpp

filename = 'pgn/alapin-sicilian-black.pgn'

lines = cpp.extract_all_lines(filename)

# Loop method
for item in lines[0]:  # Access the 0th list
    print(item[2], item[1])  # Print the 3rd element of each tuple
    print('-'*10)