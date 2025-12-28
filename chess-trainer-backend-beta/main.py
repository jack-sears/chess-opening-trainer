import chess_pgn_parser as cp
import chess_trainer as ct
import user_profiles as up
import utils

def main():
    username, profile = up.start_training_session()
    pgn_dir = 'pgn'    

    selected_openings = utils.get_user_opening_selection(pgn_dir)
    for pgn_file in selected_openings:
        print(f"Selected: {pgn_file}")

    lines = cp.parse_all_pgn(selected_openings)

    up.merge_training_data(lines, profile)

    if not lines:
        print("No positions found in PGN!")
        return

    while True:
        mode = input("Choose mode: (1) Random Positions, (2) Full Line, (Q) Quit: ").strip().lower()
        print()
        if mode == "1":
            ct.train_random_positions(lines, profile)
        elif mode == "2":
            ct.train_full_line(lines, profile)
        elif mode == "q":
            break
        else:
            print("Invalid choice.")
    
    up.save_user_profile(lines, username)

if __name__ == "__main__":
    main()
