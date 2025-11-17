# ============================================
# NETWORK ANALYSIS RULES
# ============================================
# Create and analyze gene networks

rule convert_to_cytoscape:
    """
    Convert importance matrix to network format (edge list).
    """
    input:
        importance = "results/networks/simplified_imp.csv"
    output:
        network = "results/networks/cytoscape_network.csv"
    log:
        "logs/networks/convert_cytoscape.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/convert_to_cytoscape.py"

rule direct_network:
    """
    Determine interaction direction (positive/negative).
    Classify as mutualism (pp) or competition (nn).
    """
    input:
        network = "results/networks/cytoscape_network.csv",
        matrix = "data/interim/collapsed_matrix.csv"
    output:
        directed = "results/networks/directed_network.csv"
    log:
        "logs/networks/direct_network.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/direct_network.py"

rule filter_network:
    """
    Filter network by D statistic and F1 score.
    Keep only genes with good predictability and phylogenetic signal.
    """
    input:
        network = "results/networks/directed_network.csv",
        nodes = "results/database/nodes_table.csv"
    output:
        filtered = "results/networks/filtered_network.csv"
    params:
        d_threshold = config["filtering"]["d_threshold"],
        f1_threshold = config["filtering"]["f1_threshold"]
    log:
        "logs/networks/filter_network.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/filter_network.py"

rule extract_clusters:
    """
    Extract gene clusters from network.
    """
    input:
        network = "results/networks/directed_network.csv"
    output:
        clusters_dir = directory("results/clusters"),
        flag = "results/clusters/.done"
    params:
        method = config["clustering"]["method"],
        edge_type = config["clustering"]["edge_type"]
    log:
        "logs/networks/extract_clusters.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/extract_clusters.py"

rule expand_non_unique:
    """
    Expand collapsed gene families in the network.
    """
    input:
        network = "results/networks/directed_network.csv",
        groups = "data/interim/non_unique_genes.csv",
        d_table = "results/phylogeny/d_statistics.tsv"
    output:
        expanded = "results/networks/expanded_network.csv"
    params:
        d_min = config["filtering"]["d_threshold"]
    log:
        "logs/networks/expand_non_unique.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/expand_non_unique.py"
