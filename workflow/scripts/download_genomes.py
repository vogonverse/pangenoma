
#!/usr/bin/env python3
"""
Download only the deduplicated genomes.
Uses accession list from deduplication.
"""
import subprocess
import shutil
from pathlib import Path

def main():
    accessions_file = snakemake.input.accessions
    outdir = snakemake.params.outdir
    flag_file = snakemake.output.flag
    metadata_file = snakemake.output.metadata
    
    Path(outdir).mkdir(parents=True, exist_ok=True)
    
    zip_file = Path(outdir) / "genomes.zip"
    extract_dir = Path(outdir) / "extracted"
    
    # Count accessions
    with open(accessions_file) as f:
        n_accessions = len([line for line in f if line.strip()])
    
    print(f"Downloading {n_accessions} deduplicated genomes...")
    
    # ========================================
    # STEP 1: Download DEHYDRATED data
    # ========================================
    print("Step 1/3: Downloading dehydrated package...")
    cmd = [
        "datasets", "download", "genome", "accession",
        "--inputfile", str(accessions_file),
        "--include", "gff3,genome",
        "--dehydrated",
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
    # STEP 3: Rehydrate
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
        
        gff_candidates = list(accession_dir.glob("*.gff*"))
        if not gff_candidates:
            print(f"Warning: No GFF found for {accession_dir.name}")
            continue
        
        accession = accession_dir.name
        dest_dir = Path(outdir) / "genomes" / accession
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_gff = dest_dir / f"{accession}.gff"
        shutil.copy2(gff_candidates[0], dest_gff)
        gff_files.append(dest_gff)
    
    # Cleanup
    print("Cleaning up...")
    shutil.rmtree(extract_dir)
    zip_file.unlink()
    
    
    Path(flag_file).touch()
    
    print(f"\nDownloaded {len(gff_files)} genomes to {outdir}/genomes/")

if __name__ == "__main__":
    main()
