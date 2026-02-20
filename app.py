"""
Heat Acclimation Calendar - Flask app
Based on TrainRight Ultrarunners' Heat Acclimation Cheat Sheet:
https://trainright.com/ultrarunners-heat-acclimation-cheat-sheet/
"""
from datetime import datetime, timedelta
from calendar import monthcalendar, month_name
from flask import Flask, render_template, request

app = Flask(__name__)

# Protocol 1 (Single exposure): 10 consecutive days starting 19 days out, then maintenance
# Per cheat sheet image: 10 days (race-19 to race-10), 2 off, sauna (race-7), 1 off, sauna (race-5), 4 off, race
PROTOCOL1_BOUT_START_DAYS_OUT = 19  # first session is 19 days before race
PROTOCOL1_BOUT_DAYS = 10
PROTOCOL1_MAINTENANCE_DAYS = [7, 5]  # maintenance sessions 7 and 5 days before race

# Protocol 2 (Repeated exposure): Pattern from cheat sheet, anchored to race date
# Bout 1: 11 sessions over 14 days at 6+5 weeks out (days 2,3,5,6,7 then 9,10,12,13,14,15 of the 2-week block)
# Maintenance: 2-4 weeks out, 2 sessions per week (days 2 and 5 of each 7-day block)
# Bout 2: 3 sessions at 5, 4, and 2 days before race


def protocol1_sessions(race_date: datetime) -> tuple[list[datetime], list[datetime]]:
    """
    Single exposure: 10 consecutive days starting 19 days out, then maintenance at 7 and 5 days out.
    Per TrainRight cheat sheet: bout (race-19 to race-10), 2 off, sauna (race-7), 1 off, sauna (race-5), 4 off, race.
    Returns (bout, maintenance).
    """
    # Bout: 10 consecutive days starting 19 days before race
    first_day = race_date - timedelta(days=PROTOCOL1_BOUT_START_DAYS_OUT)
    bout = [first_day + timedelta(days=i) for i in range(PROTOCOL1_BOUT_DAYS)]
    # Maintenance: sessions at 7 and 5 days before race
    maintenance = [
        race_date - timedelta(days=d) for d in PROTOCOL1_MAINTENANCE_DAYS
    ]
    return (bout, maintenance)


def protocol2_sessions(race_date: datetime) -> tuple[list[datetime], list[datetime], list[datetime]]:
    """
    Repeated exposure per TrainRight cheat sheet image.
    Pattern anchored to race date: schedule shifts so it aligns with race weekday.
    (Image shows Saturday race; for Thursday race, everything shifts 2 days earlier.)
    Bout 1: 11 sessions over 14 days at 6+5 weeks out.
    Maintenance: 2 sessions per week for 2-4 weeks out.
    Bout 2: sessions at 5, 4, 2 days before race.
    Returns (bout1, maintenance, bout2).
    """
    race_norm = race_date.replace(hour=0, minute=0, second=0, microsecond=0)
    # Image uses Saturday race; offset so block start shifts with race weekday
    offset = (race_norm.weekday() - 5)  # 5=Saturday; Thu race -> -2 (start 2 days earlier)

    # Bout 1: 14-day block. Monday of "6 weeks before" in image; add offset for race weekday
    monday_6w = (race_norm - timedelta(days=42)) - timedelta(
        days=(race_norm - timedelta(days=42)).weekday()
    )
    block_start = monday_6w + timedelta(days=offset)
    bout1_offsets = [0, 1, 3, 4, 5, 7, 8, 10, 11, 12, 13]
    bout1 = [block_start + timedelta(days=i) for i in bout1_offsets]

    # Maintenance: 3 blocks of 7 days (4, 3, 2 weeks out). 2 sessions at days 2 and 5 of each.
    maintenance = []
    for weeks_out in [4, 3, 2]:
        week_center = race_norm - timedelta(days=weeks_out * 7)
        monday_of_week = week_center - timedelta(days=week_center.weekday())
        block_start_m = monday_of_week + timedelta(days=offset)
        maintenance.append(block_start_m + timedelta(days=2))
        maintenance.append(block_start_m + timedelta(days=5))

    # Bout 2: 2 weeks. Week 1 = same on/off pattern as Bout 1 week 2 (days 12,11,9,8,7,6 before race).
    # Week 2 = tapered: 5, 4, 2 days before race.
    bout2_week1_offsets = [12, 11, 9, 8, 7, 6]  # matches Bout 1 pattern (skip Wed equiv)
    bout2_week1 = [race_norm - timedelta(days=d) for d in bout2_week1_offsets]
    bout2_week2 = [race_norm - timedelta(days=d) for d in [5, 4, 2]]
    bout2 = bout2_week1 + bout2_week2

    return (bout1, maintenance, bout2)


def sessions_to_set(sessions: list[datetime]) -> set[datetime]:
    """Normalize to date-only for membership tests."""
    return {d.replace(hour=0, minute=0, second=0, microsecond=0) for d in sessions}


def month_calendar_data_protocol1(
    year: int,
    month: int,
    bout_set: set[datetime],
    maint_set: set[datetime],
    race_date: datetime | None,
):
    """
    Build calendar grid for Protocol 1. Each day is (day_num, type): 'race' | 'bout' | 'maintenance' | None.
    """
    weeks = monthcalendar(year, month)
    result = []
    race_norm = (
        race_date.replace(hour=0, minute=0, second=0, microsecond=0) if race_date else None
    )
    for week in weeks:
        row = []
        for day in week:
            if day == 0:
                row.append((None, None))
                continue
            d = datetime(year, month, day)
            d_norm = d.replace(hour=0, minute=0, second=0, microsecond=0)
            if race_norm and d_norm == race_norm:
                cell_type = "race"
            elif d_norm in bout_set:
                cell_type = "bout"
            elif d_norm in maint_set:
                cell_type = "maintenance"
            else:
                cell_type = None
            row.append((day, cell_type))
        result.append(row)
    return result


def month_calendar_data_protocol2(
    year: int,
    month: int,
    bout1_set: set[datetime],
    maint_set: set[datetime],
    bout2_set: set[datetime],
    race_date: datetime | None,
):
    """
    Build calendar grid for Protocol 2. Each day is (day_num, type): 'race' | 'bout1' | 'maintenance' | 'bout2' | None.
    """
    weeks = monthcalendar(year, month)
    result = []
    race_norm = (
        race_date.replace(hour=0, minute=0, second=0, microsecond=0) if race_date else None
    )
    for week in weeks:
        row = []
        for day in week:
            if day == 0:
                row.append((None, None))
                continue
            d = datetime(year, month, day)
            d_norm = d.replace(hour=0, minute=0, second=0, microsecond=0)
            if race_norm and d_norm == race_norm:
                cell_type = "race"
            elif d_norm in bout1_set:
                cell_type = "bout1"
            elif d_norm in maint_set:
                cell_type = "maintenance"
            elif d_norm in bout2_set:
                cell_type = "bout2"
            else:
                cell_type = None
            row.append((day, cell_type))
        result.append(row)
    return result


def months_to_show(dates: list[datetime], race_date: datetime) -> list[tuple[int, int]]:
    """Return list of (year, month) that need to be displayed for the given dates + race."""
    all_d = set(d.replace(hour=0, minute=0, second=0, microsecond=0) for d in dates)
    all_d.add(race_date.replace(hour=0, minute=0, second=0, microsecond=0))
    months = sorted(set((d.year, d.month) for d in all_d))
    return months


@app.route("/", methods=["GET", "POST"])
def index():
    race_date = None
    protocol1_bout = []
    protocol1_maintenance = []
    protocol2_bout1 = []
    protocol2_maint = []
    protocol2_bout2 = []
    protocol1_calendar_months = []  # list of (year, month, grid)
    protocol2_calendar_months = []
    error = None

    if request.method == "POST":
        date_str = request.form.get("race_date", "").strip()
        if not date_str:
            error = "Please enter a race date."
        else:
            try:
                race_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                error = "Invalid date format. Use YYYY-MM-DD."
            if race_date and not error:
                protocol1_bout, protocol1_maintenance = protocol1_sessions(race_date)
                protocol2_bout1, protocol2_maint, protocol2_bout2 = protocol2_sessions(race_date)

                # Build calendar data for Protocol 1 (bout + maintenance)
                p1_all = protocol1_bout + protocol1_maintenance
                p1_bout_set = sessions_to_set(protocol1_bout)
                p1_maint_set = sessions_to_set(protocol1_maintenance)
                for y, m in months_to_show(p1_all, race_date):
                    grid = month_calendar_data_protocol1(
                        y, m, p1_bout_set, p1_maint_set, race_date
                    )
                    protocol1_calendar_months.append((y, m, grid))

                # Build calendar data for Protocol 2
                p2_bout1_set = sessions_to_set(protocol2_bout1)
                p2_maint_set = sessions_to_set(protocol2_maint)
                p2_bout2_set = sessions_to_set(protocol2_bout2)
                p2_all = protocol2_bout1 + protocol2_maint + protocol2_bout2
                for y, m in months_to_show(p2_all, race_date):
                    grid = month_calendar_data_protocol2(
                        y, m, p2_bout1_set, p2_maint_set, p2_bout2_set, race_date
                    )
                    protocol2_calendar_months.append((y, m, grid))

    return render_template(
        "index.html",
        race_date=race_date,
        protocol1_bout=protocol1_bout,
        protocol1_maintenance=protocol1_maintenance,
        protocol2_bout1=protocol2_bout1,
        protocol2_maintenance=protocol2_maint,
        protocol2_bout2=protocol2_bout2,
        protocol1_calendar_months=protocol1_calendar_months,
        protocol2_calendar_months=protocol2_calendar_months,
        error=error,
        month_name=month_name,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
