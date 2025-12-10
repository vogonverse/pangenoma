#!/usr/bin/env python3
"""
Utilities for phylogenetic analysis.
Contains functions to calculate and analyze Fritz & Purvis D statistic.
"""

import pandas as pd
import sys
import subprocess
import os


def identify_coincident_genes(importance_file, output_file, log_file):
    """
    Identify genes to be analyzed for D statistic.
    """
    # Read importance matrix
    imp = pd.read_csv(importance_file, index_col=0)

    # Identify genes with at least one importance > 0
    genes_with_importance = imp.columns[imp.sum(axis=0) > 0].tolist()

    # Save as CSV with header
    # Extract only the gene ID (first field before first comma)
    with open(output_file, 'w') as f:
        f.write('gene_id\n')  # Add header
        for gene in genes_with_importance:
            # Gene names in imp.csv are like "group_12734,nan,hypothetical protein"
            # But collapsed_matrix.csv only has "group_12734", so extract just the ID
            gene_id = gene.split(',')[0]
            f.write(gene_id + '\n')

    # Log
    message = f' {len(genes_with_importance)} genes identified\n Coincident genes identified'
    print(message)

    with open(log_file, 'w') as f:
        f.write(message + '\n')


def summarize_d_statistics(d_stats_file, output_file, log_file):
    """
    Generate summary of calculated D statistics.
    """
    # Read D statistics
    d_data = pd.read_csv(d_stats_file, sep='\t', header=0)

    # Calculate statistics
    summary = {
        'Total genes': len(d_data),
        'D > 0 (dispersed)': (d_data.iloc[:, 1] > 0).sum(),
        'D ~ 0 (Brownian)': ((d_data.iloc[:, 1] >= -0.1) & (d_data.iloc[:, 1] <= 0.1)).sum(),
        'D < 0 (conserved)': (d_data.iloc[:, 1] < 0).sum(),
        'Mean D': d_data.iloc[:, 1].mean(),
        'Median D': d_data.iloc[:, 1].median()
    }

    # Save summary
    with open(output_file, 'w') as f:
        f.write('=== D Statistic Summary ===\n\n')
        for key, value in summary.items():
            f.write(f'{key}: {value}\n')

    # Log
    print(' Summary generated')

    with open(log_file, 'w') as f:
        f.write(' Summary generated\n')
        with open(output_file, 'r') as summary_f:
            f.write(summary_f.read())


def build_phylogenetic_tree(alignment_file, prefix, model, bootstrap, threads, log_file):
    """
    Build phylogenetic tree using IQ-TREE.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(prefix)
    os.makedirs(output_dir, exist_ok=True)

    # Build IQ-TREE command
    cmd = [
        "iqtree",
        "-s", alignment_file,
        "-pre", prefix,
        "-m", model,
        "-bb", str(bootstrap),
        "-nt", str(threads)
    ]

    # Check if checkpoint exists but output files are missing
    # If so, use --redo to regenerate the complete output
    checkpoint_file = f"{prefix}.ckp.gz"
    treefile = f"{prefix}.treefile"
    if os.path.exists(checkpoint_file) and not os.path.exists(treefile):
        print(f"⚠ Warning: Found checkpoint but output files missing, using --redo")
        cmd.append("--redo")

    # Run IQ-TREE
    print(f"Building phylogenetic tree with IQ-TREE...")
    print(f"  Alignment: {alignment_file}")
    print(f"  Model: {model}")
    print(f"  Bootstrap: {bootstrap}")
    print(f"  Threads: {threads}")

    try:
        # Run command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Write output to log
        with open(log_file, 'w') as f:
            f.write("=== IQ-TREE EXECUTION LOG ===\n\n")
            f.write(f"Command: {' '.join(cmd)}\n\n")
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
            f.write("\n\n=== SUMMARY ===\n")
            f.write(" Phylogenetic tree built successfully\n")
            f.write(f"  - Tree file: {prefix}.treefile\n")
            f.write(f"  - Model: {model}\n")
            f.write(f"  - Bootstrap replicates: {bootstrap}\n")

        print(" Phylogenetic tree built successfully")
        print(f"  - Tree file: {prefix}.treefile")

    except subprocess.CalledProcessError as e:
        error_msg = f"ERROR: IQ-TREE failed with exit code {e.returncode}\n"
        error_msg += f"STDOUT:\n{e.stdout}\n"
        error_msg += f"STDERR:\n{e.stderr}\n"

        with open(log_file, 'w') as f:
            f.write(error_msg)

        print(error_msg, file=sys.stderr)
        sys.exit(1)


# ============================================
# Snakemake entry point
# ============================================

# Determine which function to call based on the rule invoking the script
if 'coincident' in snakemake.output.keys():
    # Rule: identify_coincident_genes
    identify_coincident_genes(
        importance_file=snakemake.input.importance,
        output_file=snakemake.output.coincident,
        log_file=snakemake.log[0]
    )
elif 'summary' in snakemake.output.keys():
    # Rule: summarize_d_statistics
    summarize_d_statistics(
        d_stats_file=snakemake.input.d_stats,
        output_file=snakemake.output.summary,
        log_file=snakemake.log[0]
    )
elif 'tree' in snakemake.output.keys():
    # Rule: build_phylogeny
    build_phylogenetic_tree(
        alignment_file=snakemake.input.alignment,
        prefix=snakemake.params.prefix,
        model=snakemake.params.model,
        bootstrap=snakemake.params.bootstrap,
        threads=snakemake.threads,
        log_file=snakemake.log[0]
    )
