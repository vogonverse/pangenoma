# ============================================
# PHYLOGENETIC STATISTICS RULES
# ============================================
# Calculates Fritz & Purvis D statistic to measure phylogenetic signal

rule identify_coincident_genes:
    """
    Identifies genes to be analyzed for D statistic.
    Filters genes based on F1 score and error thresholds.
    """
    input:
        importance = "results/random_forest/imp.csv"
    output:
        coincident = "results/phylogeny/coincident_nodes_in.csv"
    log:
        "logs/phylogeny/identify_genes.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"

rule calculate_d_statistic:
    """
    Calculates Fritz & Purvis D statistic for all previously identified genes.
    D measures phylogenetic signal:
      - D ~  1: random/no phylogenetic signal
      - D ~  0: Brownian motion (neutral evolution)
      - D <  0: phylogenetically conserved (more than Brownian)
      - D > -1: phylogenetically overdispersed
    """
    input:
        coincident = "results/phylogeny/coincident_nodes_in.csv",
        phylogeny = lambda wildcards: (
            config["input"]["phylogeny"]
            if config["input"]["phylogeny"] is not None
            else "results/phylogeny/core_genome.treefile"
        ),
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        d_stats = "results/phylogeny/d_statistics.tsv"
    params:
        cores = config["phylogeny"]["cores"],
        output_prefix = "results/phylogeny/d"
    log:
        "logs/phylogeny/calculate_d.log"
    threads: config["phylogeny"]["cores"]
    conda:
        "../../envs/r.yml"
    script:
        "../scripts/calculate_d.R"

rule summarize_d_statistics:
    """
    Generates summary statistics from calculated D values.
    Creates a text report with distribution and interpretation.
    """
    input:
        d_stats = "results/phylogeny/d_statistics.tsv"
    output:
        summary = "results/phylogeny/d_summary.txt"
    log:
        "logs/phylogeny/summarize_d.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"
