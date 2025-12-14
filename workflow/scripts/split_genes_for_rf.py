#!/usr/bin/env python3
"""
Split genes into batches for parallel Random Forest execution.
"""

import pandas as pd
import os
import sys
import math


def split_genes_for_rf(matrix_file, output_dir, n_batches, log_file):
    """
    Split genes from matrix into batches for parallel processing.
    
    Args:
        matrix_file: Path to collapsed matrix CSV
        output_dir: Directory to write batch files
        n_batches: Number of batches to create
        log_file: Path to log file
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read matrix to get gene list
    print(f"Reading matrix from {matrix_file}...")
    matrix = pd.read_csv(matrix_file, header=0, index_col=[0, 1, 2], dtype=str)
    
    # Get gene names (column names)
    genes = list(matrix.columns)
    n_genes = len(genes)
    
    print(f"Total genes: {n_genes}")
    print(f"Creating {n_batches} batches...")
    
    # Calculate batch size
    batch_size = math.ceil(n_genes / n_batches)
    
    # Split genes into batches
    batches_created = 0
    for batch_idx in range(n_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, n_genes)
        
        # Get genes for this batch
        batch_genes = genes[start_idx:end_idx]
        
        # Write batch file
        batch_file = os.path.join(output_dir, f"batch_{batch_idx}.txt")
        with open(batch_file, 'w') as f:
            for gene in batch_genes:
                f.write(gene + '\n')
        
        batches_created += 1
        print(f"  Batch {batch_idx}: {len(batch_genes)} genes ({start_idx}-{end_idx-1})")
    
    # Write log
    with open(log_file, 'w') as f:
        f.write(f"=== Gene Splitting for Random Forest ===\n\n")
        f.write(f"Total genes: {n_genes}\n")
        f.write(f"Number of batches: {n_batches}\n")
        f.write(f"Genes per batch: ~{batch_size}\n")
        f.write(f"Batches created: {batches_created}\n\n")
        f.write(f"Batch files written to: {output_dir}\n")
    
    print(f"\n✓ Successfully created {batches_created} batches")
    print(f"  Output directory: {output_dir}")


# Snakemake entry point
if __name__ == "__main__":
    try:
        # Running from Snakemake
        snakemake
        split_genes_for_rf(
            matrix_file=snakemake.input.matrix,
            output_dir=snakemake.output[0],
            n_batches=snakemake.params.n_batches,
            log_file=snakemake.log[0]
        )
    except NameError:
        # Running from command line
        if len(sys.argv) != 4:
            print("Usage: split_genes_for_rf.py <matrix_file> <output_dir> <n_batches>")
            sys.exit(1)
        
        matrix_file = sys.argv[1]
        output_dir = sys.argv[2]
        n_batches = int(sys.argv[3])
        log_file = os.path.join(output_dir, "split_genes.log")
        
        split_genes_for_rf(matrix_file, output_dir, n_batches, log_file)
