# ============================================
# PHYLOGENETIC TREE CONSTRUCTION
# ============================================
# Build phylogenetic tree from core genome alignment

rule build_phylogeny:
    """
    Build phylogenetic tree from core genome alignment using IQ-TREE.

    Uses model selection and bootstrap replicates for robust phylogenetic inference.
    The output tree can be used for downstream phylogenetic analyses (e.g., D statistic).
    """
    input:
        alignment = "results/panaroo/core_gene_alignment.aln"
    output:
        tree = "results/phylogeny/core_genome.treefile",
        iqtree = "results/phylogeny/core_genome.iqtree",
        log_file = "results/phylogeny/core_genome.log"
    params:
        prefix = "results/phylogeny/core_genome",
        model = config["phylogeny_build"]["model"],
        bootstrap = config["phylogeny_build"]["bootstrap"]
    log:
        "logs/phylogeny/build_tree.log"
    threads: config["phylogeny_build"]["threads"]
    conda:
        "../../envs/phylogeny.yml"
    script:
        "../scripts/phylogeny_utils.py"
