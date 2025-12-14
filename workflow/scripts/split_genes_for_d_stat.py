#!/usr/bin/env python3
"""
Split genes into batches for parallel D statistic calculation.
"""

import pandas as pd
import os
import sys
import math


def split_genes_for_d_stat(coincident_file, output_dir, n_batches, log_file):
    """
    Split genes from coincident genes file into batches for parallel processing.
    
    Args:
        coincident_file: Path to coincident genes CSV
        output_dir: Directory to write batch files
        n_batches: Number of batches to create
        log_file: Path to log file
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read coincident genes
    print(f"Reading coincident genes from {coincident_file}...")
    genes_df = pd.read_csv(coincident_file)
    
    # Get gene list
    genes = genes_df['gene_id'].tolist()
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
        
        # Write batch file (CSV format with header)
        batch_file = os.path.join(output_dir, f"batch_{batch_idx}.csv")
        batch_df = pd.DataFrame({'gene_id': batch_genes})
        batch_df.to_csv(batch_file, index=False)
        
        batches_created += 1
        print(f"  Batch {batch_idx}: {len(batch_genes)} genes ({start_idx}-{end_idx-1})")
    
    # Write log
    with open(log_file, 'w') as f:
        f.write(f"=== Gene Splitting for D Statistic ===\n\n")
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
        split_genes_for_d_stat(
            coincident_file=snakemake.input.coincident,
            output_dir=snakemake.params.output_dir,
            n_batches=snakemake.params.n_batches,
            log_file=snakemake.log[0]
        )
    except NameError:
        # Running from command line
        if len(sys.argv) != 4:
            print("Usage: split_genes_for_d_stat.py <coincident_file> <output_dir> <n_batches>")
            sys.exit(1)
        
        coincident_file = sys.argv[1]
        output_dir = sys.argv[2]
        n_batches = int(sys.argv[3])
        log_file = os.path.join(output_dir, "split_genes.log")
        
        split_genes_for_d_stat(coincident_file, output_dir, n_batches, log_file)
