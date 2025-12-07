# ============================================
# DATABASE RULES
# ============================================
# Annotate nodes and edges, create SQL database

rule describe_nodes:
    """
    Annotate each node (gene) with:
    - Random Forest performance metrics
    - D statistic
    """
    input:
        performance = "results/random_forest/performance.csv",
        d_stats = "results/statistics/d_statistics.tsv",  # Fixed path
        clusters = "results/clusters/.done"  # Required: clusters must be generated first
    output:
        nodes = "results/database/nodes_table.csv"
    log:
        "logs/database/describe_nodes.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/describe_nodes.py"

rule describe_edges:
    """
    Annotate each edge (interaction) with:
    - Conditional probabilities P(B|A), P(A|B)
    - Marginal frequencies P(A), P(B)
    - Joint probability P(A,B)
    """
    input:
        matrix = "data/interim/collapsed_matrix.csv",
        network = "results/networks/directed_network.csv"
    output:
        edges = "results/database/edges_table.csv"
    log:
        "logs/database/describe_edges.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/describe_edges.py"

rule create_sql_database:
    """
    Create SQL database with nodes and edges tables.
    Allows complex queries on the pangenome.
    """
    input:
        edges = "results/database/edges_table.csv",
        nodes = "results/database/nodes_table.csv"
    output:
        database = "results/database/network.db"
    log:
        "logs/database/create_sql.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/make_sql_database.py"

rule query_database:
    """
    Execute example SQL queries on the database.
    Generate predefined reports.
    """
    input:
        database = "results/database/network.db"
    output:
        predictable = "results/database/queries/predictable_genes.csv",
        mutualistic = "results/database/queries/mutualistic_edges.csv",
        competitive = "results/database/queries/competitive_edges.csv"
    log:
        "logs/database/query_database.log"
    conda:
        "../../envs/py.yml"
    script:
        "../scripts/query_database.py"
