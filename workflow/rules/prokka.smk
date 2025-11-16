# workflow/rules/prokka.smk
"""Re-anotación con Prokka usando scripts Python"""

from pathlib import Path

def get_downloaded_genomes():
    """Lista de genomas descargados"""
    genomes_dir = Path("data/raw/genomes/genomes")
    if not genomes_dir.exists():
        return []
    
    accessions = []
    for d in genomes_dir.iterdir():
        if d.is_dir() and list(d.glob("*.fna")):
            accessions.append(d.name)
    
    return accessions

# ============================================
# RULE: Prokka (1 genoma)
# ============================================
rule prokka_annotate:
    """Re-anota 1 genoma con Prokka"""
    input:
        fasta = "data/raw/genomes/genomes/{accession}/{accession}.fna"
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
    
    conda:
        "../../envs/prokka.yml"
    script:
        "../scripts/prokka.py"

# ============================================
# RULE: Recopilar GFFs
# ============================================
rule collect_prokka_gffs:
    """Crea lista de GFFs para Panaroo"""
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