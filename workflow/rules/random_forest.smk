# ============================================
# RANDOM FOREST RULES
# ============================================
# Train Random Forest models to predict genes

rule run_random_forest:
    """
    Train Random Forest for each gene in the pangenome.
    Generate importance matrix and performance table.
    """
    input:
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        importance = "results/random_forest/imp.csv",
        performance = "results/random_forest/performance.csv"
    params:
        n_trees = config["random_forest"]["n_trees"],
        depth = config["random_forest"]["max_depth"],
        min_present = config["random_forest"]["min_present"],
        min_absent = config["random_forest"]["min_absent"],
        n_threads = config["random_forest"]["n_threads"],
        purity = config["random_forest"]["purity"],
        output_dir = "results/random_forest"
    log:
        "logs/random_forest/panforest.log"
    benchmark:
        "benchmarks/random_forest/run_random_forest.tsv"
    threads: config["random_forest"]["n_threads"]
    resources:
        mem_mb = 128000,  # 128 GB for large matrices
        runtime = 2880    # 48 hours (inflated for first run with many genomes)
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/PanForest.py"

rule simplify_importance_matrix:
    """
    Filter weak relationships from importance matrix.
    """
    input:
        importance = "results/random_forest/imp.csv"
    output:
        simplified = "results/networks/simplified_imp.csv"
    params:
        threshold = config["network"]["importance_threshold"]
    log:
        "logs/random_forest/simplify_imp.log"
    benchmark:
        "benchmarks/random_forest/simplify_importance_matrix.tsv"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/simplify_imp.py"
