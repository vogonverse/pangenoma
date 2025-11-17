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
    
    Path(outdir).mkdir(parents=True, exist_ok=True)
    
    zip_file = Path(outdir) / "genomes.zip"
    extract_dir = Path(outdir) / "extracted"
    
    # count accessions
    with open(accessions_file) as f:
        n_accessions = len([line for line in f if line.strip()])
    
    print(f"Downloading {n_accessions} deduplicated genomes...")
    
    # download dehydrated data
    print("Step 1/3: Downloading dehydrated package...")
    cmd = [
        "datasets", "download", "genome", "accession",
        "--inputfile", str(accessions_file),
        "--include", "gff3,genome",
        "--dehydrated",
        "--filename", str(zip_file)
    ]
    subprocess.run(cmd, check=True)
    
    # unzip
    print("Step 2/3: Extracting zip archive...")
    subprocess.run([
        "unzip", "-q", "-o", str(zip_file), 
        "-d", str(extract_dir)
    ], check=True)
    
    # rehydrate
    print("Step 3/3: Rehydrating (downloading sequence data)...")
    subprocess.run([
        "datasets", "rehydrate",
        "--directory", str(extract_dir)
    ], check=True)
    
    # organize files
    print("Organizing files...")
    data_dir = extract_dir / "ncbi_dataset" / "data"
    
    copied_genomes = []
    
    for accession_dir in sorted(data_dir.iterdir()):
        if not accession_dir.is_dir():
            continue
        
        accession = accession_dir.name
        
        # search for GFF and FNA
        gff_candidates = list(accession_dir.glob("*.gff"))
        fna_candidates = list(accession_dir.glob("*.fna"))
        
        # verify that both exist
        if not gff_candidates:
            print(f"Warning: No GFF found for {accession}")
            continue
        
        if not fna_candidates:
            print(f"Warning: No FNA found for {accession}")
            continue
        
        # create destination directory
        dest_dir = Path(outdir) / "genomes" / accession
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # copy GFF
        dest_gff = dest_dir / f"{accession}.gff"
        shutil.copy2(gff_candidates[0], dest_gff)
        
        # copy FNA
        dest_fna = dest_dir / f"{accession}.fna"
        shutil.copy2(fna_candidates[0], dest_fna)
        
        copied_genomes.append(accession)
    

    # clean
    print("Cleaning up...")
    shutil.rmtree(extract_dir)
    zip_file.unlink()
    
    # flag
    Path(flag_file).touch()
    
    print(f"\nDownloaded {len(copied_genomes)} genomes to {outdir}/genomes/")
    print(f"  - GFF files: {len(copied_genomes)}")
    print(f"  - FNA files: {len(copied_genomes)}")

if __name__ == "__main__":
    main()