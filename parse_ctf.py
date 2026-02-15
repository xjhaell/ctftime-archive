"""Parses raw CTFtime tab-separated text files into structured CSV format."""

import csv
import sys
import argparse
from pathlib import Path


class CTFParser:
    """Parser for tab-separated data copied from CTFtime event listings."""

    def __init__(self, year: int):
        self.year = year
        self.event_counter = 1

    def standardize_format(self, format_text: str) -> str:
        """
        Map format field to one of: Jeopardy, Attack-Defense, Hack-Quest, or REVIEW.
        CTFtime uses inconsistent casing and spelling (e.g. "Attack-defence").
        """
        if not format_text or format_text.strip() == "":
            return "REVIEW"

        lower = format_text.lower().strip()

        if "jeopardy" in lower:
            return "Jeopardy"
        if "attack" in lower and ("defense" in lower or "defence" in lower):
            return "Attack-Defense"
        if "hack" in lower and "quest" in lower:
            return "Hack-Quest"

        return "REVIEW"

    def standardize_location(self, location_text: str) -> str:
        """
        Map location to On-line or In-person.
        Any non-empty, non-online value is treated as in-person (city, country, etc).
        """
        if not location_text or location_text.strip() == "":
            return "REVIEW"

        lower = location_text.lower().strip()

        if "on-line" in lower or "online" in lower:
            return "On-line"

        return "In-person"

    def clean_weight(self, weight_text: str) -> str:
        """Return numeric weight as string, or '0' if blank/invalid."""
        if not weight_text or weight_text.strip() == "":
            return "0"

        clean = weight_text.strip()
        try:
            float(clean)
            return clean
        except ValueError:
            return "0"

    def parse_line(self, line: str) -> dict:
        """
        Parse a single tab-separated line into an event dictionary.
        Expected column order: Name, Date, Format, Location, Weight, Notes.
        """
        columns = line.split('\t')

        name = columns[0].strip() if len(columns) > 0 else ""
        date_raw = columns[1].strip() if len(columns) > 1 else ""
        format_raw = columns[2].strip() if len(columns) > 2 else ""
        location_raw = columns[3].strip() if len(columns) > 3 else ""
        weight_raw = columns[4].strip() if len(columns) > 4 else ""
        notes_raw = columns[5].strip() if len(columns) > 5 else ""

        event = {
            'event_id': self.event_counter,
            'name': name,
            'year': self.year,
            'date_raw': date_raw,
            'format': self.standardize_format(format_raw),
            'location': self.standardize_location(location_raw),
            'weight': self.clean_weight(weight_raw),
            'notes': notes_raw if notes_raw else "N/A"
        }

        self.event_counter += 1
        return event

    def parse_file(self, input_file: str) -> list:
        """Read and parse all lines from a raw .txt file."""
        events = []

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        event = self.parse_line(line)
                        events.append(event)
                    except Exception as e:
                        print(f"*  Warning: Error parsing line {line_num}: {e}")
                        continue

        except FileNotFoundError:
            print(f"*  Error: File '{input_file}' not found")
            sys.exit(1)

        return events

    def save_to_csv(self, events: list, output_file: str):
        """Write parsed events to a CSV file."""
        if not events:
            print("*  No events to save.")
            return

        fieldnames = ['event_id', 'name', 'year', 'date_raw',
                      'format', 'location', 'weight', 'notes']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events)

        print(f"*  Saved {len(events)} events to '{output_file}'")

    def print_summary(self, events: list):
        """Print format/location distribution and flag items needing review."""
        if not events:
            return

        print(f"\n{'*' * 60}")
        print(f"*  Summary for {self.year}")
        print(f"{'*' * 60}")
        print(f"*  Total events: {len(events)}")

        # Format distribution
        print("*")
        print("*  Format distribution:")
        format_counts = {}
        for event in events:
            fmt = event['format']
            format_counts[fmt] = format_counts.get(fmt, 0) + 1

        for fmt, count in sorted(format_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(events)) * 100
            print(f"*    {fmt}: {count} ({pct:.1f}%)")

        # Location distribution
        print("*")
        print("*  Location distribution:")
        location_counts = {}
        for event in events:
            loc = event['location']
            location_counts[loc] = location_counts.get(loc, 0) + 1

        for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(events)) * 100
            print(f"*    {loc}: {count} ({pct:.1f}%)")

        # Items needing review
        review_items = [e for e in events
                        if e['format'] == 'REVIEW' or e['location'] == 'REVIEW']
        if review_items:
            print("*")
            print(f"*  WARNING: {len(review_items)} events need manual review:")
            for event in review_items[:5]:
                print(f"*    - ID {event['event_id']}: {event['name']}")
                if event['format'] == 'REVIEW':
                    print(f"*      Format needs review")
                if event['location'] == 'REVIEW':
                    print(f"*      Location needs review")
            if len(review_items) > 5:
                print(f"*    ... and {len(review_items) - 5} more")

        # Weight stats
        weights = [float(e['weight']) for e in events if e['weight'] != '0']
        if weights:
            print("*")
            print(f"*  Weight stats:")
            print(f"*    Events with weight > 0: {len(weights)}/{len(events)}")
            print(f"*    Average: {sum(weights) / len(weights):.2f}")
            print(f"*    Max: {max(weights):.2f}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse CTFtime tab-separated data into CSV format'
    )
    parser.add_argument('input_file', help='Input .txt file (tab-separated)')
    parser.add_argument('--year', type=int, required=True, help='Year of events')
    parser.add_argument('--output', type=str, help='Output CSV filename')
    parser.add_argument('--no-summary', action='store_true', help='Skip summary')

    args = parser.parse_args()

    if args.output is None:
        args.output = f"{args.year}_ctf_data.csv"

    print(f"*  Parsing CTFtime data for {args.year}")
    print(f"*  Input:  {args.input_file}")
    print(f"*  Output: {args.output}")

    ctf_parser = CTFParser(args.year)
    events = ctf_parser.parse_file(args.input_file)

    if not events:
        print("*  No events found in input file.")
        sys.exit(1)

    ctf_parser.save_to_csv(events, args.output)

    if not args.no_summary:
        ctf_parser.print_summary(events)


if __name__ == "__main__":
    main()