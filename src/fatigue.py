from datetime import datetime

def drive_time_score(session_start: datetime) -> float:
    minutes_driven = (datetime.now() - session_start).seconds / 60

    if minutes_driven < 90:
        return 0.1
    elif minutes_driven < 150:
        return 0.4
    elif minutes_driven < 210:
        return 0.7
    else:
        return 1.0

def time_of_day_score() -> float:
    hour = datetime.now().hour

    if 2 <= hour <= 5:      # Deep night — most dangerous
        return 1.0
    elif 14 <= hour <= 16:  # Post-lunch dip
        return 0.6
    elif 22 <= hour <= 23:  # Late night
        return 0.4
    else:
        return 0.1

def get_fatigue_score(session_start: datetime) -> float:
    w_drive = 0.5
    w_time  = 0.5

    score = (
        w_drive * drive_time_score(session_start) +
        w_time  * time_of_day_score()
    )
    return round(min(score, 1.0), 3)