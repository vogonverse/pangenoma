#!/usr/bin/env python3
"""
Run Prokka annotation on a single genome.
"""
import subprocess
import shutil
from pathlib import Path
import sys
import fcntl

def main():
    # Get parameters from Snakemake
    fasta = snakemake.input.fasta
    outdir = snakemake.params.outdir
    prefix = snakemake.params.prefix
    genus = snakemake.params.genus
    species = snakemake.params.species
    kingdom = snakemake.params.kingdom
    cpus = snakemake.threads
    
    # Clean output directory
    outdir_path = Path(outdir)
    if outdir_path.exists():
        shutil.rmtree(outdir_path)
    outdir_path.mkdir(parents=True, exist_ok=True)
    
    # Build Prokka command
    cmd = [
        "prokka",
        "--outdir", str(outdir),
        "--prefix", prefix,
        "--genus", genus,
        "--species", species,
        "--kingdom", kingdom,
        "--cpus", str(cpus),
        "--force",
        str(fasta)
    ]
    
    print(f"Running Prokka on {prefix}...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run Prokka
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Prokka failed for {prefix}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    
    # Verify output
    gff_file = Path(snakemake.output.gff)
    if not gff_file.exists():
        print(f"ERROR: GFF file not created: {gff_file}", file=sys.stderr)
        sys.exit(1)

    print(f" Successfully annotated: {prefix}")
    print(f"  Output: {outdir}")

    # Append GFF path to the shared list file
    gff_list_file = Path("results/prokka/gff_files.txt")
    gff_list_file.parent.mkdir(parents=True, exist_ok=True)

    # Use file locking to prevent race conditions when multiple jobs write simultaneously
    with open(gff_list_file, 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(f"{gff_file.absolute()}\n")
            f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    print(f"  Added to GFF list: {gff_list_file}")

    # Create marker file to indicate this GFF has been registered
    marker_file = Path(snakemake.output.marker)
    marker_file.write_text(f"{gff_file.absolute()}\n")

if __name__ == "__main__":
    main()