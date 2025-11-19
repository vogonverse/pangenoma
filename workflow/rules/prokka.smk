# workflow/rules/prokka.smk
"""Re-annotation with Prokka using Python scripts"""

from pathlib import Path

def get_downloaded_genomes():
    """List of downloaded genomes"""
    genomes_dir = Path("data/raw/genomes/genomes")
    if not genomes_dir.exists():
        return []

    accessions = []
    for d in genomes_dir.iterdir():
        if d.is_dir() and list(d.glob("*.fna")):
            accessions.append(d.name)

    return accessions

# ============================================
# Prokka (1 genome)
# ============================================
rule prokka_annotate:
    """Re-annotate 1 genome with Prokka"""
    input:
        fasta = "data/raw/genomes/genomes/{accession}/{accession}.fna",
        flag = "data/raw/genomes/.download_complete"
    output:
        gff = "results/prokka/{accession}/{accession}.gff",
        faa = "results/prokka/{accession}/{accession}.faa",
        ffn = "results/prokka/{accession}/{accession}.ffn",
        marker = "results/prokka/{accession}/.gff_registered"
    params:
        outdir = "results/prokka/{accession}",
        prefix = "{accession}",
        genus = config["prokka"]["genus"],
        species = config["prokka"]["species"],
        kingdom = config["prokka"].get("kingdom", "Bacteria")

    log:
        "logs/prokka/{accession}.log"
    benchmark:
        "benchmarks/prokka/{accession}.tsv"
    threads: config["prokka"]["threads"]
    resources:
        mem_mb = config["prokka"]["mem_mb"]

    conda:
        "../../envs/prokka.yml"
    script:
        "../scripts/prokka.py"

# ============================================
#  Ensure all GFFs are registered
# ============================================
rule ensure_all_gffs_registered:
    """Ensure all GFFs have been added to the list file"""
    input:
        markers = expand(
            "results/prokka/{accession}/.gff_registered",
            accession=get_downloaded_genomes()
        )
    output:
        done = "results/prokka/.all_gffs_registered"
    run:
        from pathlib import Path
        # All marker files exist, meaning all GFFs have been written to gff_files.txt
        Path(output.done).write_text("All GFF files registered\n")