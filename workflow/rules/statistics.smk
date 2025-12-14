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
        coincident = "results/statistics/coincident_nodes_in.csv"
    log:
        "logs/statistics/identify_genes.log"
    benchmark:
        "benchmarks/statistics/identify_coincident_genes.tsv"
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
        coincident = "results/statistics/coincident_nodes_in.csv",
        phylogeny = lambda wildcards: (
            config["input"]["phylogeny"]
            if config["input"]["phylogeny"] is not None
            else "results/phylogeny/core_genome.treefile"
        ),
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        d_stats = "results/statistics/d_statistics.tsv"
    params:
        cores = config["phylogeny"]["cores"],
        output_prefix = "results/statistics/d"
    log:
        "logs/statistics/calculate_d.log"
    benchmark:
        "benchmarks/statistics/calculate_d_statistic.tsv"
    threads: 32  # Máxima paralelización efectiva (R paralelo con 32 cores)
    resources:
        mem_mb = 128000,  # 128 GB para máxima holgura (miles de genes × 6,252 genomas)
        runtime = 1440    # 24 horas (muy inflado para primera ejecución)
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
        d_stats = "results/statistics/d_statistics.tsv"
    output:
        summary = "results/statistics/d_summary.txt"
    log:
        "logs/statistics/summarize_d.log"
    benchmark:
        "benchmarks/statistics/summarize_d_statistics.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/phylogeny_utils.py"
