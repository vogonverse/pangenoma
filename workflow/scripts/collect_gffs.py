#!/usr/bin/env python3
"""
Collect all Prokka GFF files into a list for Panaroo.
"""
from pathlib import Path

def main():
    # Get GFF files from Snakemake
    gff_files = snakemake.input.gffs
    output_list = snakemake.output.gff_list
    
    # Convert to absolute paths and sort
    gff_paths = [Path(gff).resolve() for gff in gff_files]
    gff_paths.sort()
    
    # Write to file
    with open(output_list, 'w') as f:
        for gff in gff_paths:
            f.write(f"{gff}\n")
    
    print(f"Collected {len(gff_paths)} GFF files")
    print(f"  Output: {output_list}")
    

if __name__ == "__main__":
    main()