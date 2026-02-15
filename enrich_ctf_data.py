"""Enriches raw CTFtime CSV data with derived temporal and event variables."""

import csv
import sys
import re
from datetime import datetime
from dateutil import parser as dateparser
import argparse
from pathlib import Path


class CTFDataEnricher:
    """Adds temporal, categorical, and event characteristic columns to CTF data."""

    def __init__(self):
        self.parse_failures = []
        self.duration_outliers = []

    def parse_ctftime_date(self, date_str: str, year: int) -> tuple:
        """
        Parse a CTFtime date string into start and end datetimes.
        Returns (start_dt, end_dt) or (None, None) on failure.

        CTFtime formats vary, e.g.:
            "27 Dec., 12:00 PST — 29 Dec. 2015, 12:00 PST"
            "05 Aug., 17:00 PDT — 09 Aug. 2015, 13:00 PDT"
        """
        if not date_str or date_str.strip() == "":
            return None, None

        try:
            parts = re.split(r'\s*[—–-]\s*', date_str)
            if len(parts) != 2:
                return None, None

            start_str, end_str = parts

            # Add year if not present
            if str(year) not in start_str:
                start_str = f"{start_str} {year}"

            start_dt = dateparser.parse(start_str, fuzzy=True)
            if start_dt and start_dt.tzinfo is not None:
                start_dt = start_dt.replace(tzinfo=None)

            # Handle cross-year events (e.g. Dec start, Jan end)
            if str(year) not in end_str and str(year + 1) not in end_str:
                if 'jan' in end_str.lower() and start_dt and start_dt.month == 12:
                    end_str = f"{end_str} {year + 1}"
                else:
                    end_str = f"{end_str} {year}"

            end_dt = dateparser.parse(end_str, fuzzy=True)
            if end_dt and end_dt.tzinfo is not None:
                end_dt = end_dt.replace(tzinfo=None)

            # Sanity check
            if start_dt and end_dt and end_dt < start_dt:
                end_dt = dateparser.parse(
                    f"{end_str.split()[0]} {end_str.split()[1]} {year + 1}",
                    fuzzy=True
                )

            return start_dt, end_dt

        except Exception:
            return None, None

    def get_duration_hours(self, start_dt: datetime, end_dt: datetime) -> float:
        """Calculate duration in hours. Returns None for invalid results."""
        if start_dt and end_dt:
            hours = (end_dt - start_dt).total_seconds() / 3600
            if hours < 0:
                return None
            return round(hours, 2)
        return None

    def get_quarter(self, month: int) -> str:
        """Map month (1-12) to quarter string (Q1-Q4)."""
        return f"Q{(month - 1) // 3 + 1}"

    def get_season(self, month: int) -> str:
        """Map month to meteorological season (Northern Hemisphere)."""
        seasons = {
            12: "Winter", 1: "Winter", 2: "Winter",
            3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer",
            9: "Fall", 10: "Fall", 11: "Fall"
        }
        return seasons.get(month)

    def get_covid_era(self, year: int, month: int) -> str:
        """
        Categorize by COVID era:
            Pre-COVID:  before March 2020
            COVID:      March 2020 through December 2021
            Post-COVID: January 2022 onward
        """
        if year < 2020 or (year == 2020 and month < 3):
            return "Pre-COVID"
        elif year <= 2021:
            return "COVID"
        return "Post-COVID"

    def get_duration_category(self, hours: float) -> str:
        """Short (<24h), Medium (24-48h), or Long (>48h)."""
        if hours is None:
            return None
        if hours < 24:
            return "Short"
        elif hours <= 48:
            return "Medium"
        return "Long"

    def get_weight_category(self, weight: float) -> str:
        """Zero (0), Low (<25), Medium (25-50), or High (>50)."""
        if weight is None or weight == 0:
            return "Zero"
        elif weight < 25:
            return "Low"
        elif weight <= 50:
            return "Medium"
        return "High"

    def standardize_location(self, location_raw: str) -> str:
        """Normalize location to Online or On-site."""
        if location_raw in ('On-line', 'Online'):
            return "Online"
        elif location_raw in ('In-person', 'On-site'):
            return "On-site"
        elif location_raw == 'Hybrid':
            return "Hybrid"
        return location_raw

    def standardize_format(self, format_raw: str) -> str:
        """Normalize format values. Hack-Quest is grouped with Jeopardy."""
        if format_raw == 'Hack-Quest':
            return "Jeopardy"
        elif format_raw in ('Jeopardy', 'Attack-Defense', 'Hybrid', 'King-of-the-Hill'):
            return format_raw
        return "Other"

    def enrich_event(self, event: dict, event_sequence: int) -> dict:
        """Add all derived columns to a single event."""
        enriched = event.copy()

        year = int(event.get('year', 0))
        date_raw = event.get('date_raw', '')
        name = event.get('name', '')
        weight = float(event.get('weight', 0))
        notes = event.get('notes', '')

        # Standardize
        enriched['location'] = self.standardize_location(event.get('location', ''))
        enriched['format'] = self.standardize_format(event.get('format', ''))

        # Parse dates
        start_dt, end_dt = self.parse_ctftime_date(date_raw, year)

        if start_dt is None or end_dt is None:
            self.parse_failures.append({
                'event_id': event.get('event_id'),
                'name': name,
                'date_raw': date_raw
            })
            # Fill with defaults for failed parsing
            enriched.update({
                'start_date': None, 'end_date': None,
                'start_datetime': None, 'end_datetime': None,
                'duration_hours': None, 'duration_days': None,
                'start_month': None, 'start_quarter': None,
                'start_day_of_week': None, 'is_weekend': None,
                'season': None,
                'covid_era': self.get_covid_era(year, 1),
                'is_multi_day': None,
                'duration_category': None,
                'weight_category': self.get_weight_category(weight),
                'is_qualifier': 1 if any(t in name.lower() for t in ['qual', 'prelim']) else 0,
                'is_finals': 1 if 'final' in name.lower() else 0,
                'is_prequalified': 1 if 'prequalified' in notes.lower() else 0,
                'year_index': year - 2015,
                'event_sequence_in_year': event_sequence
            })
            return enriched

        # Compute derived fields
        duration_hours = self.get_duration_hours(start_dt, end_dt)
        duration_days = round(duration_hours / 24, 2) if duration_hours else None

        # Track outliers (>7 days)
        if duration_hours and duration_hours > 168:
            self.duration_outliers.append({
                'event_id': event.get('event_id'),
                'name': name,
                'duration_hours': duration_hours
            })

        enriched.update({
            'start_date': start_dt.strftime('%Y-%m-%d'),
            'end_date': end_dt.strftime('%Y-%m-%d'),
            'start_datetime': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'end_datetime': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_hours': duration_hours,
            'duration_days': duration_days,
            'start_month': start_dt.month,
            'start_quarter': self.get_quarter(start_dt.month),
            'start_day_of_week': start_dt.strftime('%A'),
            'is_weekend': 1 if start_dt.weekday() >= 4 else 0,
            'season': self.get_season(start_dt.month),
            'covid_era': self.get_covid_era(year, start_dt.month),
            'is_multi_day': 1 if duration_hours and duration_hours > 24 else 0,
            'duration_category': self.get_duration_category(duration_hours),
            'weight_category': self.get_weight_category(weight),
            'is_qualifier': 1 if any(t in name.lower() for t in ['qual', 'prelim']) else 0,
            'is_finals': 1 if 'final' in name.lower() else 0,
            'is_prequalified': 1 if notes != 'N/A' and 'prequalified' in notes.lower() else 0,
            'year_index': year - 2015,
            'event_sequence_in_year': event_sequence
        })

        return enriched

    def enrich_dataset(self, input_file: str) -> list:
        """Read a CSV file and enrich all events."""
        events = []
        year_sequences = {}

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    year = int(row.get('year', 0))
                    year_sequences[year] = year_sequences.get(year, 0) + 1
                    events.append(self.enrich_event(row, year_sequences[year]))

        except FileNotFoundError:
            print(f"*  Error: File '{input_file}' not found")
            sys.exit(1)

        return events

    def save_to_csv(self, events: list, output_file: str):
        """Write enriched events to CSV with organized column order."""
        if not events:
            print("*  No events to save.")
            return

        fieldnames = [
            'event_id', 'name', 'year',
            'start_date', 'end_date', 'start_datetime', 'end_datetime',
            'duration_hours', 'duration_days', 'start_month', 'start_quarter',
            'start_day_of_week', 'is_weekend', 'season', 'covid_era',
            'format', 'location', 'weight',
            'is_multi_day', 'duration_category', 'weight_category',
            'is_qualifier', 'is_finals', 'is_prequalified',
            'year_index', 'event_sequence_in_year',
            'date_raw', 'notes'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(events)

        print(f"*  Saved {len(events)} enriched events to '{output_file}'")

    def print_summary(self, events: list):
        """Print dataset overview and data quality notes."""
        if not events:
            return

        print(f"\n{'*' * 60}")
        print(f"*  Enrichment Summary")
        print(f"{'*' * 60}")
        print(f"*  Total events: {len(events)}")

        years = sorted(set(int(e['year']) for e in events))
        print(f"*  Year range: {min(years)}-{max(years)} ({len(years)} years)")

        parsed = sum(1 for e in events if e['start_date'] is not None)
        print(f"*  Successfully parsed: {parsed}/{len(events)} ({parsed/len(events)*100:.1f}%)")

        if self.parse_failures:
            print(f"*  Failed to parse: {len(self.parse_failures)} events")

        if self.duration_outliers:
            print(f"*  Duration outliers (>7 days): {len(self.duration_outliers)} events")


def main():
    parser = argparse.ArgumentParser(
        description='Enrich CTF dataset with temporal and event characteristics'
    )
    parser.add_argument('input_file', help='Input CSV file (parsed CTF data)')
    parser.add_argument('--output', type=str, help='Output CSV filename')
    parser.add_argument('--no-summary', action='store_true', help='Skip summary')

    args = parser.parse_args()

    if args.output is None:
        input_path = Path(args.input_file)
        args.output = f"{input_path.stem}_enriched{input_path.suffix}"

    print(f"*  Input:  {args.input_file}")
    print(f"*  Output: {args.output}")

    enricher = CTFDataEnricher()
    events = enricher.enrich_dataset(args.input_file)

    if not events:
        print("*  No events found.")
        sys.exit(1)

    enricher.save_to_csv(events, args.output)

    if not args.no_summary:
        enricher.print_summary(events)


if __name__ == "__main__":
    main()