#!/usr/bin/env python3
"""
Merge Random Forest results from multiple batches.
"""

import pandas as pd
import os
import sys


def merge_rf_results(importance_files, performance_files, output_imp, output_perf, log_file):
    """
    Merge Random Forest batch results into complete matrices.
    
    Args:
        importance_files: List of batch importance CSV files
        performance_files: List of batch performance CSV files
        output_imp: Path to output importance matrix
        output_perf: Path to output performance table
        log_file: Path to log file
    """
    print(f"Merging {len(importance_files)} importance batches...")
    
    # Read and concatenate importance matrices
    imp_dfs = []
    for imp_file in sorted(importance_files):
        print(f"  Reading {os.path.basename(imp_file)}...")
        df = pd.read_csv(imp_file, index_col=0)
        imp_dfs.append(df)
    
    # Concatenate along rows (each batch has different genes as rows)
    importance = pd.concat(imp_dfs, axis=0)
    
    print(f"\nMerging {len(performance_files)} performance batches...")
    
    # Read and concatenate performance tables
    perf_dfs = []
    for perf_file in sorted(performance_files):
        print(f"  Reading {os.path.basename(perf_file)}...")
        df = pd.read_csv(perf_file, index_col=0)
        perf_dfs.append(df)
    
    # Concatenate along rows
    performance = pd.concat(perf_dfs, axis=0)
    
    # Verify no duplicates
    if importance.index.duplicated().any():
        raise ValueError("Duplicate genes found in importance matrix!")
    
    if performance.index.duplicated().any():
        raise ValueError("Duplicate genes found in performance table!")
    
    # Sort by index for consistency
    importance = importance.sort_index()
    performance = performance.sort_index()
    
    # Write outputs
    print(f"\nWriting merged results...")
    importance.round(5).to_csv(output_imp)
    performance.round(5).to_csv(output_perf)
    
    # Write log
    with open(log_file, 'w') as f:
        f.write(f"=== Random Forest Batch Merge ===\n\n")
        f.write(f"Batches merged: {len(importance_files)}\n")
        f.write(f"Total genes: {len(importance)}\n")
        f.write(f"Importance matrix shape: {importance.shape}\n")
        f.write(f"Performance table shape: {performance.shape}\n\n")
        f.write(f"Output files:\n")
        f.write(f"  - {output_imp}\n")
        f.write(f"  - {output_perf}\n")
    
    print(f"\n✓ Successfully merged {len(importance_files)} batches")
    print(f"  Total genes: {len(importance)}")
    print(f"  Importance matrix: {importance.shape}")
    print(f"  Performance table: {performance.shape}")


# Snakemake entry point
if __name__ == "__main__":
    try:
        # Running from Snakemake
        snakemake
        merge_rf_results(
            importance_files=snakemake.input.importance,
            performance_files=snakemake.input.performance,
            output_imp=snakemake.output.importance,
            output_perf=snakemake.output.performance,
            log_file=snakemake.log[0]
        )
    except NameError:
        # Running from command line
        print("This script is designed to be run from Snakemake")
        print("Usage: snakemake merge_rf_results")
        sys.exit(1)
