#!/usr/bin/env python3
"""Execute example SQL queries on the database."""

import sys
import argparse
import sqlite3
import subprocess
from pathlib import Path


def get_args():
    """Get arguments from Snakemake or command line."""
    # Check if running from Snakemake
    try:
        database = snakemake.input.database
        predictable = snakemake.output.predictable
        mutualistic = snakemake.output.mutualistic
        competitive = snakemake.output.competitive
        return [database, predictable, mutualistic, competitive]
    except NameError:
        # Running from command line
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--database", dest="database",
                            type=str, help="SQLite database file")
        parser.add_argument("-p", "--predictable", dest="predictable",
                            type=str, help="Output file for predictable genes")
        parser.add_argument("-m", "--mutualistic", dest="mutualistic",
                            type=str, help="Output file for mutualistic edges")
        parser.add_argument("-c", "--competitive", dest="competitive",
                            type=str, help="Output file for competitive edges")
        args = parser.parse_args()
        if None in [args.database, args.predictable, args.mutualistic, args.competitive]:
            parser.print_help(sys.stderr)
            sys.exit(0)
        return [args.database, args.predictable, args.mutualistic, args.competitive]


def execute_query(database, query, output_file):
    """Execute a SQL query and save results to CSV."""
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    # Execute query
    cursor.execute(query)

    # Get column names
    column_names = [description[0] for description in cursor.description]

    # Get results
    results = cursor.fetchall()

    # Write to CSV
    with open(output_file, 'w') as f:
        # Write header
        f.write(','.join(column_names) + '\n')
        # Write rows
        for row in results:
            f.write(','.join(str(val) for val in row) + '\n')

    conn.close()
    return len(results)


def main():
    """Execute predefined queries on the database."""
    database, predictable, mutualistic, competitive = get_args()

    # Create output directory
    Path(predictable).parent.mkdir(parents=True, exist_ok=True)

    # Query 1: Predictable genes (error < 10%, F1 > 0.9, D > 0)
    query1 = """
    SELECT NodeID, Annotation, Description, AccuracyTest, F1StatisticAverageTest, DStatistic
    FROM nodes
    WHERE ErrorRateTest <= 0.1
        AND F1StatisticClass1Test >= 0.9
        AND F1StatisticClass0Test >= 0.9
        AND DStatistic > 0
    ORDER BY AccuracyTest DESC;
    """
    n_predictable = execute_query(database, query1, predictable)
    print(f"Predictable genes: {n_predictable}")

    # Query 2: Mutualistic interactions (pp)
    query2 = """
    SELECT Target_A, Source_B, Weight, P_AAndB
    FROM edges
    WHERE InteractionType = 'pp'
        AND Target_A IN (SELECT NodeID FROM nodes WHERE DStatistic > 0)
    ORDER BY Weight DESC
    LIMIT 1000;
    """
    n_mutualistic = execute_query(database, query2, mutualistic)
    print(f"Mutualistic edges: {n_mutualistic}")

    # Query 3: Competitive interactions (nn)
    query3 = """
    SELECT Target_A, Source_B, Weight
    FROM edges
    WHERE InteractionType = 'nn'
        AND Target_A IN (SELECT NodeID FROM nodes WHERE DStatistic > 0)
    ORDER BY Weight DESC
    LIMIT 1000;
    """
    n_competitive = execute_query(database, query3, competitive)
    print(f"Competitive edges: {n_competitive}")


if __name__ == "__main__":
    main()
