#!/usr/bin/env python3
"""
Merge D statistic results from multiple batches.
"""

import pandas as pd
import os
import sys


def merge_d_statistics(d_stat_files, output_file, log_file):
    """
    Merge D statistic batch results into complete table.
    
    Args:
        d_stat_files: List of batch D statistic TSV files
        output_file: Path to output merged TSV
        log_file: Path to log file
    """
    print(f"Merging {len(d_stat_files)} D statistic batches...")
    
    # Read and concatenate D statistic tables
    dfs = []
    for d_file in sorted(d_stat_files):
        print(f"  Reading {os.path.basename(d_file)}...")
        df = pd.read_csv(d_file, sep='\t')
        dfs.append(df)
    
    # Concatenate along rows
    d_stats = pd.concat(dfs, axis=0, ignore_index=True)
    
    # Verify no duplicates
    if d_stats['ID'].duplicated().any():
        raise ValueError("Duplicate genes found in D statistics!")
    
    # Sort by gene ID for consistency
    d_stats = d_stats.sort_values('ID')
    
    # Write output
    print(f"\nWriting merged results...")
    d_stats.to_csv(output_file, sep='\t', index=False)
    
    # Write log
    with open(log_file, 'w') as f:
        f.write(f"=== D Statistic Batch Merge ===\n\n")
        f.write(f"Batches merged: {len(d_stat_files)}\n")
        f.write(f"Total genes: {len(d_stats)}\n")
        f.write(f"D statistic table shape: {d_stats.shape}\n\n")
        f.write(f"Output file: {output_file}\n")
    
    print(f"\n✓ Successfully merged {len(d_stat_files)} batches")
    print(f"  Total genes: {len(d_stats)}")
    print(f"  Output: {output_file}")


# Snakemake entry point
if __name__ == "__main__":
    try:
        # Running from Snakemake
        snakemake
        merge_d_statistics(
            d_stat_files=snakemake.input.d_stats,
            output_file=snakemake.output.d_stats,
            log_file=snakemake.log[0]
        )
    except NameError:
        # Running from command line
        print("This script is designed to be run from Snakemake")
        print("Usage: snakemake merge_d_statistics")
        sys.exit(1)
