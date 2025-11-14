
"""Download genomes from NCBI using dehydrated datasets (for large downloads)"""
import subprocess
import sys
from pathlib import Path
import shutil
import json

def main():
    # Params from Snakemake
    taxid = snakemake.params.taxid
    assembly_levels = snakemake.params.assembly_levels
    outdir = snakemake.params.outdir
    flag_file = snakemake.output.flag
    metadata_file = snakemake.output.metadata
    
    print(f"Downloading genomes (taxid: {taxid}, levels: {assembly_levels})...")
    
    # Create output directory
    Path(outdir).mkdir(parents=True, exist_ok=True)
    
    zip_file = Path(outdir) / "genomes.zip"
    extract_dir = Path(outdir) / "extracted"
    
    # ========================================
    # STEP 1: Download DEHYDRATED package
    # ========================================
    print("Step 1/3: Downloading dehydrated package...")
    cmd = [
        "datasets", "download", "genome", "taxon", taxid,
        "--assembly-level", ",".join(assembly_levels),
        "--include", "gff3,genome",
        "--dehydrated",  # Metadata only
        "--filename", str(zip_file)
    ]
    subprocess.run(cmd, check=True)
    
    # ========================================
    # STEP 2: Unzip
    # ========================================
    print("Step 2/3: Extracting zip archive...")
    subprocess.run([
        "unzip", "-q", "-o", str(zip_file), 
        "-d", str(extract_dir)
    ], check=True)
    
    # ========================================
    # STEP 3: Rehydrate (download actual data)
    # ========================================
    print("Step 3/3: Rehydrating (downloading sequence data)...")
    subprocess.run([
        "datasets", "rehydrate",
        "--directory", str(extract_dir)
    ], check=True)
    
    # ========================================
    # Organize GFF files
    # ========================================
    print("Organizing files...")
    data_dir = extract_dir / "ncbi_dataset" / "data"
    gff_files = []
    
    for accession_dir in sorted(data_dir.iterdir()):
        if not accession_dir.is_dir():
            continue
        
        # Find GFF file
        gff_candidates = list(accession_dir.glob("*.gff*"))
        if not gff_candidates:
            print(f"Warning: No GFF found for {accession_dir.name}")
            continue
        
        # Copy to final location
        accession = accession_dir.name
        dest_dir = Path(outdir) / "genomes" / accession
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_gff = dest_dir / f"{accession}.gff"
        shutil.copy2(gff_candidates[0], dest_gff)
        gff_files.append(dest_gff)
    
    # ========================================
    # Cleanup temporary files
    # ========================================
    print("Cleaning temporary files...")
    shutil.rmtree(extract_dir)
    zip_file.unlink()  # Delete zip
    
    # ========================================
    # Write metadata
    # ========================================
    with open(metadata_file, 'w') as f:
        f.write("accession\tpath\n")
        for gff in gff_files:
            f.write(f"{gff.parent.name}\t{gff}\n")
    
    # Write flag
    Path(flag_file).touch()
    
    # ========================================
    # Final report
    # ========================================
    print(f"\n✓ Downloaded {len(gff_files)} genomes to {outdir}/genomes/")
    
    if len(gff_files) == 0:
        sys.exit("ERROR: No genomes downloaded")

if __name__ == "__main__":
    main()