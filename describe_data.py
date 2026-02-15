"""Prints summary statistics for the CTFtime archive dataset."""

import csv
import os


def describe(filepath: str):
    """Print row count, column count, and key distributions for a CSV."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames

    print(f"*  File: {os.path.basename(filepath)}")
    print(f"*  Rows: {len(rows)}")
    print(f"*  Columns: {len(columns)}")
    print(f"*  Column names: {', '.join(columns)}")
    print()

    # Events per year
    if 'year' in columns:
        year_counts = {}
        for r in rows:
            y = r['year']
            year_counts[y] = year_counts.get(y, 0) + 1
        print("*  Events per year:")
        for y in sorted(year_counts.keys()):
            print(f"*    {y}: {year_counts[y]}")
        print()

    # Format distribution
    if 'format' in columns:
        fmt_counts = {}
        for r in rows:
            f = r['format']
            fmt_counts[f] = fmt_counts.get(f, 0) + 1
        print("*  Format distribution:")
        for f, c in sorted(fmt_counts.items(), key=lambda x: -x[1]):
            print(f"*    {f}: {c}")
        print()

    # Location distribution
    if 'location' in columns:
        loc_counts = {}
        for r in rows:
            l = r['location']
            loc_counts[l] = loc_counts.get(l, 0) + 1
        print("*  Location distribution:")
        for l, c in sorted(loc_counts.items(), key=lambda x: -x[1]):
            print(f"*    {l}: {c}")
        print()


def main():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')

    raw = os.path.join(data_dir, 'ctftime_archive_all.csv')
    enriched = os.path.join(data_dir, 'ctftime_archive_all_enriched.csv')

    print("*" * 60)
    print("*  CTFtime Archive Dataset -- Summary Stats")
    print("*" * 60)
    print()

    if os.path.exists(raw):
        describe(raw)
        print("*" + "-" * 59)
        print()

    if os.path.exists(enriched):
        describe(enriched)


if __name__ == "__main__":
    main()