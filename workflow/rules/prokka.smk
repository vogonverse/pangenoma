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
        ffn = "results/prokka/{accession}/{accession}.ffn"
    params:
        outdir = "results/prokka/{accession}",
        prefix = "{accession}",
        genus = config["prokka"]["genus"],
        species = config["prokka"]["species"],
        kingdom = config["prokka"].get("kingdom", "Bacteria")

    log:
        "logs/prokka/{accession}.log"
    threads: 4

    conda:
        "../../envs/prokka.yml"
    script:
        "../scripts/prokka.py"

# ============================================
#  Collect GFFs
# ============================================
rule collect_prokka_gffs:
    """Create list of GFFs for Panaroo"""
    input:
        gffs = expand(
            "results/prokka/{accession}/{accession}.gff",
            accession=get_downloaded_genomes()
        )
    output:
        gff_list = "results/prokka/gff_files.txt"
    conda:
        "../../envs/prokka.yml"
    log:
        "logs/prokka/collect_gffs.log"
    script:
        "../scripts/collect_gffs.py"