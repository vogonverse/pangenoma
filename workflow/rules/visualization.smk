# ============================================
# Automated visualization using Cytoscape
# ============================================

rule visualize_cytoscape_network:
    """
    Generate network visualization using Cytoscape and py4cytoscape.
    - Edge colors based on InteractionType (pp=green, nn=red)
    - Edge width based on Weight
    - Node size based on gene frequency (from performance.csv)
    """
    input:
        network = "results/networks/cytoscape_network.csv",
        performance = "results/random_forest/performance.csv"
    output:
        image = "results/networks/cytoscape_network.png"
    params:
        layout = "force-directed",  #kamada-kawai, grid, hierarchical, circular
        resolution = 300  # image DPI
    log:
        "logs/visualization/cytoscape_network.log"
    conda:
        "../../envs/cytoscape.yml"
    script:
        "../scripts/visualize_network.py"


rule visualize_directed_network:
    """
    Generate directed network visualization using Cytoscape.
    """
    input:
        network = "results/networks/directed_network.csv",
        performance = "results/random_forest/performance.csv"
    output:
        image = "results/networks/directed_network.png"
    params:
        layout = "force-directed",
        resolution = 300
    log:
        "logs/visualization/directed_network.log"
    conda:
        "../../envs/cytoscape.yml"
    script:
        "../scripts/visualize_network.py"


rule visualize_all_networks:
    """ visualize all networks at once. """
    input:
        "results/networks/cytoscape_network.png",
        "results/networks/directed_network.png"
    shell:
        "All network visualizations completed!"
