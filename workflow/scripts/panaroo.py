#!/usr/bin/env python3
"""
Run Panaroo to infer pangenome.
"""
import subprocess
from pathlib import Path
import sys


def validate_gff_list(gff_list_file):
    """Validate that GFF list file exists and has content"""
    gff_list = Path(gff_list_file)
    
    if not gff_list.exists():
        print(f"ERROR: GFF list file not found: {gff_list_file}", file=sys.stderr)
        sys.exit(1)
    
    # Count GFF files
    with open(gff_list) as f:
        gff_files = [line.strip() for line in f if line.strip()]
    
    if len(gff_files) == 0:
        print("ERROR: GFF list is empty", file=sys.stderr)
        sys.exit(1)
    
    # Verify first GFF exists
    first_gff = Path(gff_files[0])
    if not first_gff.exists():
        print(f"ERROR: First GFF file not found: {first_gff}", file=sys.stderr)
        print(f"       Check that Prokka completed successfully", file=sys.stderr)
        sys.exit(1)
    
    print(f" Found {len(gff_files):,} GFF files to process")
    return len(gff_files)

def build_panaroo_command(gff_list, params):
    """
    Build Panaroo command from parameters.

    ALL parameters come from config.yaml via Snakemake params.
    Nothing hardcoded here.
    """
    cmd = [
        "panaroo",
        "-i", str(gff_list),
        "-o", str(params.outdir),
        "--clean-mode", params.clean_mode,
        "-c", str(params.identity_threshold),
        "-t", str(params.threads)
    ]

    # Optional: Alignment
    if params.alignment and params.alignment != "null":
        cmd.extend(["-a", params.alignment])
        cmd.extend(["--aligner", params.aligner])
        cmd.extend(["--core_threshold", str(params.core_threshold)])

    # Optional: Advanced options
    if hasattr(params, "family_threshold") and params.family_threshold:
        cmd.extend(["-f", str(params.family_threshold)])

    if hasattr(params, "len_dif_percent") and params.len_dif_percent:
        cmd.extend(["--len_dif_percent", str(params.len_dif_percent)])

    if hasattr(params, "merge_paralogs") and params.merge_paralogs:
        cmd.append("--merge_paralogs")

    if hasattr(params, "remove_invalid_genes") and params.remove_invalid_genes:
        cmd.append("--remove-invalid-genes")

    return cmd

def run_panaroo(gff_list, params):
    """Execute Panaroo pangenome inference"""
    
    # Build command from parameters
    cmd = build_panaroo_command(gff_list, params)
    
    print(f"\nPanarooing...")
    print(f"  Clean mode: {params.clean_mode}")
    print(f"  Identity threshold: {params.identity_threshold}")
    print(f"  Alignment: {params.alignment}")
    print(f"  Threads: {params.threads}")
    print(f"  Output: {params.outdir}")
    print(f"\nCommand:\n  {' '.join(cmd)}\n")
    
    # Run Panaroo
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        print("\n Panaroo completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"\n  ERROR: Panaroo failed", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        print(f"\nSTDOUT:\n{e.stdout}", file=sys.stderr)
        print(f"\nSTDERR:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

def validate_outputs(outdir):
    """Validate that Panaroo generated expected outputs"""
    
    outdir_path = Path(outdir)
    
    # Critical output
    gene_pa = outdir_path / "gene_presence_absence.csv"
    
    if not gene_pa.exists():
        print(f"\n ERROR: gene_presence_absence.csv not created", file=sys.stderr)
        sys.exit(1)
    
    if gene_pa.stat().st_size == 0:
        print(f"\n ERROR: gene_presence_absence.csv is empty", file=sys.stderr)
        sys.exit(1)
    
    # Count stats
    with open(gene_pa) as f:
        n_genes = sum(1 for _ in f) - 1  # -1 for header
    
    with open(gene_pa) as f:
        header = f.readline()
        n_genomes = len(header.split(',')) - 14  # First 14 cols are metadata
    
    size_mb = gene_pa.stat().st_size / (1024 * 1024)
    
    print(f"\nOutput validation...OK")
    print(f"  Gene families: {n_genes:,}")
    print(f"  Genomes: {n_genomes:,}")
    print(f"  Matrix size: {size_mb:.1f} MB")
    
    # List all generated files
    print(f"\n  Generated files:")
    for file in sorted(outdir_path.glob("*")):
        if file.is_file():
            print(f"    - {file.name}")
    
    return n_genes, n_genomes

def main():
    try:
        # get parameters from Snakemake
        gff_list = snakemake.input.gff_list
        params = snakemake.params

        print("=" * 70)
        print("PANAROO - Pangenome Inference")
        print("=" * 70)
    except Exception as e:
        print(f"ERROR during initialization: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 1: Validate inputs
    print("\n[1/3] Validating inputs...")
    n_input_genomes = validate_gff_list(gff_list)
    
    # Step 2: Run Panaroo
    print(f"\n[2/3] Running Panaroo on {n_input_genomes:,} genomes...")
    run_panaroo(gff_list, params)
    
    # Step 3: Validate outputs
    print("\n[3/3] Validating outputs...")
    n_genes, n_genomes = validate_outputs(params.outdir)
    
    print("\n" + "=" * 70)
    print(" PANAROO COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"  Input genomes: {n_input_genomes:,}")
    print(f"  Output genomes: {n_genomes:,}")
    print(f"  Gene families: {n_genes:,}")
    print(f"  Matrix: {params.outdir}/gene_presence_absence.csv")
    print("=" * 70)

if __name__ == "__main__":
    main()