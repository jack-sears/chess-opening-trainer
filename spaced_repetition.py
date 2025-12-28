"""
Spaced Repetition Algorithm for Chess Opening Trainer

Implements a modified SM-2 algorithm to prioritize lines based on:
- Time since last practice
- Mastery level
- Recent mistakes
- Current interval vs elapsed time
"""

from datetime import datetime, timedelta
import math

# Constants
DEFAULT_MASTERY_LEVEL = 0.0
DEFAULT_EASINESS_FACTOR = 2.5
DEFAULT_INTERVAL_DAYS = 1.0
MIN_INTERVAL_DAYS = 0.1
MAX_INTERVAL_DAYS = 365.0
RECENT_MISTAKE_WINDOW_DAYS = 7
MIN_PRIORITY_SCORE = 0.01


def calculate_recent_mistake_weight(recent_mistakes, current_time=None):
    """
    Calculate weight for recent mistakes.
    More recent mistakes count more heavily.
    
    Args:
        recent_mistakes: List of timestamps (ISO format strings or datetime objects)
        current_time: Current time (defaults to now)
    
    Returns:
        Weight multiplier (0.0 to 2.0+)
    """
    if not recent_mistakes:
        return 0.0
    
    if current_time is None:
        current_time = datetime.now()
    
    # Convert string timestamps to datetime if needed
    mistake_times = []
    for mistake_time in recent_mistakes:
        if isinstance(mistake_time, str):
            try:
                mistake_times.append(datetime.fromisoformat(mistake_time))
            except (ValueError, AttributeError):
                continue
        elif isinstance(mistake_time, datetime):
            mistake_times.append(mistake_time)
    
    if not mistake_times:
        return 0.0
    
    total_weight = 0.0
    for mistake_time in mistake_times:
        days_ago = (current_time - mistake_time).total_seconds() / 86400.0
        
        # Exponential decay: mistakes in last 24 hours = 2.0x, last week = 1.0x, older = less
        if days_ago <= 1.0:
            weight = 2.0
        elif days_ago <= RECENT_MISTAKE_WINDOW_DAYS:
            # Linear decay from 2.0 to 0.5 over the week
            weight = 2.0 - (1.5 * (days_ago - 1.0) / (RECENT_MISTAKE_WINDOW_DAYS - 1.0))
        else:
            # Exponential decay for older mistakes
            weight = 0.5 * math.exp(-(days_ago - RECENT_MISTAKE_WINDOW_DAYS) / 7.0)
        
        total_weight += weight
    
    # Cap the total weight to prevent one line from dominating
    return min(total_weight, 5.0)


def calculate_priority_score(mastery_level, easiness_factor, last_practiced, 
                            interval_days, recent_mistakes, current_time=None):
    """
    Calculate priority score for a line. Higher score = more urgent to practice.
    
    Priority Score = (time_overdue / interval) * (1 - mastery) * (1 + recent_mistake_weight)
    
    Args:
        mastery_level: 0.0 (new) to 1.0 (mastered)
        easiness_factor: SM-2 easiness factor (typically 1.3 to 2.5)
        last_practiced: Timestamp of last practice (ISO string, datetime, or None)
        interval_days: Days until next review
        recent_mistakes: List of mistake timestamps
        current_time: Current time (defaults to now)
    
    Returns:
        Priority score (higher = more urgent)
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Parse last_practiced timestamp
    if last_practiced is None:
        # Never practiced - high priority
        time_since_practice = float('inf')
    elif isinstance(last_practiced, str):
        try:
            last_practiced_dt = datetime.fromisoformat(last_practiced)
            time_since_practice = (current_time - last_practiced_dt).total_seconds() / 86400.0
        except (ValueError, AttributeError):
            time_since_practice = float('inf')
    elif isinstance(last_practiced, datetime):
        time_since_practice = (current_time - last_practiced).total_seconds() / 86400.0
    else:
        time_since_practice = float('inf')
    
    # Calculate how overdue this line is (negative if not yet due)
    if interval_days <= 0:
        interval_days = MIN_INTERVAL_DAYS
    
    time_overdue = max(0, time_since_practice - interval_days)
    
    # Base priority: how overdue relative to interval
    if time_since_practice == float('inf'):
        # Never practiced
        overdue_ratio = 10.0  # Very high priority
    else:
        overdue_ratio = max(0.1, time_overdue / max(interval_days, 0.1))
    
    # Mastery factor: lower mastery = higher priority
    mastery_factor = 1.0 - mastery_level
    
    # Recent mistake weight
    mistake_weight = calculate_recent_mistake_weight(recent_mistakes, current_time)
    mistake_factor = 1.0 + (mistake_weight * 0.2)  # Scale mistake weight
    
    # Calculate final priority score
    priority = overdue_ratio * mastery_factor * mistake_factor
    
    # Add base priority for lines that have never been practiced
    if last_practiced is None:
        priority += 5.0
    
    return max(MIN_PRIORITY_SCORE, priority)


def update_mastery_after_practice(mastery_level, easiness_factor, was_correct, 
                                 streak_count, mistake_count):
    """
    Update mastery level after practicing a line.
    
    Args:
        mastery_level: Current mastery (0.0-1.0)
        easiness_factor: Current easiness factor
        was_correct: True if line was completed without mistakes
        streak_count: Current streak count
        mistake_count: Total mistake count
    
    Returns:
        (new_mastery_level, new_easiness_factor)
    """
    if was_correct:
        # Increase mastery based on easiness factor and streak
        mastery_increase = 0.1 * easiness_factor * (1.0 + streak_count * 0.1)
        new_mastery = min(1.0, mastery_level + mastery_increase)
        
        # Slightly increase easiness for correct answers
        new_easiness = min(2.5, easiness_factor + 0.05)
    else:
        # Decrease mastery based on mistakes
        mastery_decrease = 0.15 * (1.0 + mistake_count * 0.1)
        new_mastery = max(0.0, mastery_level - mastery_decrease)
        
        # Decrease easiness for incorrect answers
        new_easiness = max(1.3, easiness_factor - 0.2)
    
    return new_mastery, new_easiness


def calculate_next_interval(mastery_level, easiness_factor, current_interval, 
                           was_correct, streak_count):
    """
    Calculate next review interval using SM-2 style algorithm.
    
    Args:
        mastery_level: Current mastery (0.0-1.0)
        easiness_factor: Current easiness factor
        current_interval: Current interval in days
        was_correct: True if line was completed correctly
        streak_count: Current streak count
    
    Returns:
        Next interval in days
    """
    if was_correct:
        if current_interval <= 0:
            # First correct answer
            next_interval = 1.0
        elif current_interval < 1.0:
            # Second correct answer
            next_interval = 6.0
        else:
            # Subsequent correct answers: multiply by easiness factor
            next_interval = current_interval * easiness_factor
            
            # Bonus for high mastery and streaks
            if mastery_level > 0.8 and streak_count >= 3:
                next_interval *= 1.2
    else:
        # Reset interval on mistake, but don't go below minimum
        next_interval = max(MIN_INTERVAL_DAYS, current_interval * 0.5)
    
    # Apply mastery-based scaling
    mastery_multiplier = 0.5 + (mastery_level * 0.5)  # 0.5x to 1.0x
    next_interval *= mastery_multiplier
    
    # Clamp to reasonable bounds
    return max(MIN_INTERVAL_DAYS, min(MAX_INTERVAL_DAYS, next_interval))


def decay_mastery_over_time(mastery_level, last_practiced, current_time=None, 
                           decay_rate=0.01):
    """
    Decay mastery level if line hasn't been practiced in a while.
    
    Args:
        mastery_level: Current mastery level
        last_practiced: Timestamp of last practice
        current_time: Current time (defaults to now)
        decay_rate: Daily decay rate (default 1% per day after interval)
    
    Returns:
        Decayed mastery level
    """
    if current_time is None:
        current_time = datetime.now()
    
    if last_practiced is None:
        return mastery_level  # No decay if never practiced
    
    # Parse timestamp
    if isinstance(last_practiced, str):
        try:
            last_practiced_dt = datetime.fromisoformat(last_practiced)
        except (ValueError, AttributeError):
            return mastery_level
    elif isinstance(last_practiced, datetime):
        last_practiced_dt = last_practiced
    else:
        return mastery_level
    
    days_since = (current_time - last_practiced_dt).total_seconds() / 86400.0
    
    # Only decay if significantly past the review interval
    # Decay increases exponentially with time
    if days_since > 30:
        decay_days = days_since - 30
        decay_factor = 1.0 - (decay_rate * decay_days * 0.1)  # Slower decay
        return max(0.0, mastery_level * decay_factor)
    
    return mastery_level


def add_mistake_timestamp(recent_mistakes, current_time=None, max_mistakes=20):
    """
    Add a new mistake timestamp to the list, removing old ones.
    
    Args:
        recent_mistakes: List of mistake timestamps
        current_time: Current time (defaults to now)
        max_mistakes: Maximum number of mistakes to keep
    
    Returns:
        Updated list of mistake timestamps (ISO format strings)
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Add current timestamp
    new_mistakes = recent_mistakes.copy() if recent_mistakes else []
    new_mistakes.append(current_time.isoformat())
    
    # Remove mistakes older than the window
    cutoff_time = current_time - timedelta(days=RECENT_MISTAKE_WINDOW_DAYS * 2)
    filtered_mistakes = []
    
    for mistake_time_str in new_mistakes:
        try:
            if isinstance(mistake_time_str, str):
                mistake_time = datetime.fromisoformat(mistake_time_str)
            elif isinstance(mistake_time_str, datetime):
                mistake_time = mistake_time_str
            else:
                continue
            
            if mistake_time >= cutoff_time:
                filtered_mistakes.append(mistake_time.isoformat() if isinstance(mistake_time, datetime) else mistake_time_str)
        except (ValueError, AttributeError):
            continue
    
    # Keep only the most recent mistakes
    return filtered_mistakes[-max_mistakes:]

