
"""
Get metadata from NCBI without downloading genomes.
Saves metadata JSON with all candidate genomes.
"""
import subprocess
import json
from pathlib import Path

def main():
    taxid = snakemake.params.taxid
    assembly_levels = snakemake.params.assembly_levels
    metadata_file = snakemake.output.metadata
    
    print(f"Querying NCBI for taxid {taxid}...")
    
    # Get summary (metadata only, no download)
    cmd = [
        "datasets", "summary", "genome", "taxon", taxid,
        "--annotated", "--assembly-level", ",".join(assembly_levels),
        "--as-json-lines"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    # Save metadata
    Path(metadata_file).write_text(result.stdout)
    
    # Count genomes
    n_genomes = len([line for line in result.stdout.strip().split('\n') if line])
    print(f"Found {n_genomes} candidate genomes (may include GCA/GCF duplicates)")

if __name__ == "__main__":
    main()