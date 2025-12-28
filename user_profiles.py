import os
import json
from datetime import datetime, timedelta

PROFILE_DIR = "profiles"
os.makedirs(PROFILE_DIR, exist_ok=True)

# Default values for new spaced repetition fields
DEFAULT_MASTERY_LEVEL = 0.0
DEFAULT_EASINESS_FACTOR = 2.5
DEFAULT_INTERVAL_DAYS = 1.0

def load_user_profile(username):
    """Loads user profile and migrates to new format if needed."""
    profile_path = os.path.join(PROFILE_DIR, f"{username}.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profile = json.load(f)
        # Migrate old format if needed
        return migrate_profile_data(profile)
    return {}

def migrate_profile_data(user_data):
    """Migrates old profile format to new format with spaced repetition fields."""
    for opening_name, opening_data in user_data.items():
        if not isinstance(opening_data, dict):
            continue
            
        num_lines = len(opening_data.get("mistakes", []))
        
        # Initialize new fields if they don't exist
        if "mastery_level" not in opening_data:
            opening_data["mastery_level"] = [DEFAULT_MASTERY_LEVEL] * num_lines
        if "easiness_factor" not in opening_data:
            opening_data["easiness_factor"] = [DEFAULT_EASINESS_FACTOR] * num_lines
        if "last_practiced" not in opening_data:
            opening_data["last_practiced"] = [None] * num_lines
        if "interval_days" not in opening_data:
            opening_data["interval_days"] = [DEFAULT_INTERVAL_DAYS] * num_lines
        if "recent_mistakes" not in opening_data:
            opening_data["recent_mistakes"] = [[] for _ in range(num_lines)]
        
        # Ensure all lists are the same length
        current_length = len(opening_data.get("mistakes", []))
        for field in ["mistakes", "streaks", "mastery_level", "easiness_factor", 
                      "last_practiced", "interval_days", "recent_mistakes"]:
            if field in opening_data:
                if len(opening_data[field]) < current_length:
                    if field == "recent_mistakes":
                        opening_data[field].extend([[] for _ in range(current_length - len(opening_data[field]))])
                    elif field == "last_practiced":
                        opening_data[field].extend([None] * (current_length - len(opening_data[field])))
                    elif field == "mastery_level":
                        opening_data[field].extend([DEFAULT_MASTERY_LEVEL] * (current_length - len(opening_data[field])))
                    elif field == "easiness_factor":
                        opening_data[field].extend([DEFAULT_EASINESS_FACTOR] * (current_length - len(opening_data[field])))
                    elif field == "interval_days":
                        opening_data[field].extend([DEFAULT_INTERVAL_DAYS] * (current_length - len(opening_data[field])))
                    else:
                        opening_data[field].extend([0] * (current_length - len(opening_data[field])))
    
    return user_data

def merge_training_data(all_openings, user_data):
    """Merges parsed PGN lines with user mistake/streak data and spaced repetition fields."""
    # Migrate old profile format if needed
    user_data = migrate_profile_data(user_data)
    
    for pgn_file, data in all_openings.items():
        num_lines = len(data["lines"])

        # If user has trained on this opening before, merge the data
        if pgn_file in user_data:
            user_mistakes = user_data[pgn_file].get("mistakes", [])
            user_streaks = user_data[pgn_file].get("streaks", [])
            user_mastery = user_data[pgn_file].get("mastery_level", [])
            user_easiness = user_data[pgn_file].get("easiness_factor", [])
            user_last_practiced = user_data[pgn_file].get("last_practiced", [])
            user_interval = user_data[pgn_file].get("interval_days", [])
            user_recent_mistakes = user_data[pgn_file].get("recent_mistakes", [])

            # Expand or truncate all fields to match the new number of lines
            data["mistakes"] = (user_mistakes + [0] * num_lines)[:num_lines]
            data["streaks"] = (user_streaks + [0] * num_lines)[:num_lines]
            data["mastery_level"] = (user_mastery + [DEFAULT_MASTERY_LEVEL] * num_lines)[:num_lines]
            data["easiness_factor"] = (user_easiness + [DEFAULT_EASINESS_FACTOR] * num_lines)[:num_lines]
            data["last_practiced"] = (user_last_practiced + [None] * num_lines)[:num_lines]
            data["interval_days"] = (user_interval + [DEFAULT_INTERVAL_DAYS] * num_lines)[:num_lines]
            data["recent_mistakes"] = (user_recent_mistakes + [[] for _ in range(num_lines)])[:num_lines]
        
        else:
            # First time training this opening → initialize all fields
            data["mistakes"] = [0] * num_lines
            data["streaks"] = [0] * num_lines
            data["mastery_level"] = [DEFAULT_MASTERY_LEVEL] * num_lines
            data["easiness_factor"] = [DEFAULT_EASINESS_FACTOR] * num_lines
            data["last_practiced"] = [None] * num_lines
            data["interval_days"] = [DEFAULT_INTERVAL_DAYS] * num_lines
            data["recent_mistakes"] = [[] for _ in range(num_lines)]


def save_user_profile(all_openings, username):
    """Extracts all training data from parsed_pgns and saves them to a JSON file."""
    filename = os.path.join(PROFILE_DIR, f"{username}.json")

    # Load existing data if it exists
    if os.path.exists(filename):
        with open(filename, "r") as file:
            existing_data = json.load(file)
        # Migrate old format if needed
        existing_data = migrate_profile_data(existing_data)
    else:
        existing_data = {}  # No file yet, start fresh

    # Merge new data with existing data
    for opening, data in all_openings.items():
        if opening in existing_data:
            # Update all fields
            existing_data[opening]["mistakes"] = data["mistakes"]
            existing_data[opening]["streaks"] = data["streaks"]
            existing_data[opening]["mastery_level"] = data.get("mastery_level", [DEFAULT_MASTERY_LEVEL] * len(data["mistakes"]))
            existing_data[opening]["easiness_factor"] = data.get("easiness_factor", [DEFAULT_EASINESS_FACTOR] * len(data["mistakes"]))
            existing_data[opening]["last_practiced"] = data.get("last_practiced", [None] * len(data["mistakes"]))
            existing_data[opening]["interval_days"] = data.get("interval_days", [DEFAULT_INTERVAL_DAYS] * len(data["mistakes"]))
            existing_data[opening]["recent_mistakes"] = data.get("recent_mistakes", [[] for _ in range(len(data["mistakes"]))])
        else:
            existing_data[opening] = {
                "mistakes": data["mistakes"],
                "streaks": data["streaks"],
                "mastery_level": data.get("mastery_level", [DEFAULT_MASTERY_LEVEL] * len(data["mistakes"])),
                "easiness_factor": data.get("easiness_factor", [DEFAULT_EASINESS_FACTOR] * len(data["mistakes"])),
                "last_practiced": data.get("last_practiced", [None] * len(data["mistakes"])),
                "interval_days": data.get("interval_days", [DEFAULT_INTERVAL_DAYS] * len(data["mistakes"])),
                "recent_mistakes": data.get("recent_mistakes", [[] for _ in range(len(data["mistakes"]))])
            }

    # Save updated data
    with open(filename, "w") as file:
        json.dump(existing_data, file, indent=4, default=str)

def start_training_session():
    username = input("Enter your username: ")
    profile = load_user_profile(username)
    
    print(f"Welcome, {username}! Training session starting...")
    return username, profile

'''# Example usage
if __name__ == "__main__":
    user, user_profile = start_training_session()
    print(json.dumps(user_profile, indent=4))'''