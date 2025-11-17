#!/usr/bin/env python3
"""
Build phylogenetic tree with IQ-TREE.
"""
import subprocess
import sys
from pathlib import Path

def run_iqtree(alignment, prefix, model, bootstrap, threads):
    """Execute IQ-TREE with parameters from config"""
    
    cmd = [
        "iqtree2",
        "-s", str(alignment),
        "-m", model,
        "-bb", str(bootstrap),
        "-nt", str(threads),
        "-pre", str(prefix)
    ]
    
    print("=" * 70)
    print("IQ-TREE - Phylogenetic Tree Construction")
    print("=" * 70)
    print(f"\nAlignment: {alignment}")
    print(f"Model: {model}")
    print(f"Bootstrap replicates: {bootstrap}")
    print(f"Threads: {threads}")
    print(f"\nCommand: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        print("\n IQ-TREE completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"\n ERROR: IQ-TREE failed", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        print(f"\nSTDERR:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

def validate_output(tree_file):
    """Validate tree file was created"""
    
    if not Path(tree_file).exists():
        print(f"\n ERROR: Tree file not created: {tree_file}", file=sys.stderr)
        sys.exit(1)
    
    if Path(tree_file).stat().st_size == 0:
        print(f"\n ERROR: Tree file is empty", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n Tree file created: {tree_file}")

def main():
    # get parameters from smk
    alignment = snakemake.input.alignment
    tree_output = snakemake.output.tree
    prefix = snakemake.params.prefix
    model = snakemake.params.model
    bootstrap = snakemake.params.bootstrap
    threads = snakemake.threads
    
    # run IQ-TREE
    run_iqtree(alignment, prefix, model, bootstrap, threads)
    
    # validations
    validate_output(tree_output)
    
    print("\n" + "=" * 70)
    print(" PHYLOGENETIC TREE CONSTRUCTION COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    main()