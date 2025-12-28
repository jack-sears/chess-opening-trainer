import os
import json
from datetime import datetime

PROFILE_DIR = "profiles"
os.makedirs(PROFILE_DIR, exist_ok=True)

def load_user_profile(username):
    profile_path = os.path.join(PROFILE_DIR, f"{username}.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            return json.load(f)
    return {}

def merge_training_data(all_openings, user_data):
    """Merges parsed PGN lines with user mistake/streak data."""
    for pgn_file, data in all_openings.items():
        num_lines = len(data["lines"])

        # If user has trained on this opening before, merge the data
        if pgn_file in user_data:
            user_mistakes = user_data[pgn_file].get("mistakes", [])
            user_streaks = user_data[pgn_file].get("streaks", [])

            # Expand or truncate mistakes/streaks to match the new number of lines
            data["mistakes"] = (user_mistakes + [0] * num_lines)[:num_lines]
            data["streaks"] = (user_streaks + [0] * num_lines)[:num_lines]
        
        else:
            # First time training this opening → initialize mistakes & streaks
            data["mistakes"] = [0] * num_lines
            data["streaks"] = [0] * num_lines


def save_user_profile(all_openings, username):
    """Extracts mistakes & streaks from parsed_pgns and saves them to a JSON file."""
    filename = os.path.join(PROFILE_DIR, f"{username}.json")

    # Load existing data if it exists
    if os.path.exists(filename):
        with open(filename, "r") as file:
            existing_data = json.load(file)
    else:
        existing_data = {}  # No file yet, start fresh

    # Merge new data with existing data
    for opening, data in all_openings.items():
        if opening in existing_data:
            existing_data[opening]["mistakes"] = data["mistakes"]
            existing_data[opening]["streaks"] = data["streaks"]
        else:
            existing_data[opening] = {
                "mistakes": data["mistakes"],
                "streaks": data["streaks"]
            }

    # Save updated data
    with open(filename, "w") as file:
        json.dump(existing_data, file, indent=4)

def start_training_session():
    username = input("Enter your username: ")
    profile = load_user_profile(username)
    
    print(f"Welcome, {username}! Training session starting...")
    return username, profile

'''# Example usage
if __name__ == "__main__":
    user, user_profile = start_training_session()
    print(json.dumps(user_profile, indent=4))'''