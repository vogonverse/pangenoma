#!/usr/bin/env python3
"""
Automatic network visualization using Cytoscape and py4cytoscape.
Generates network images from gene interaction data.
"""

import sys
import pandas as pd
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    import py4cytoscape as p4c
except ImportError:
    logging.error("py4cytoscape not installed. Install with: pip install py4cytoscape")
    sys.exit(1)


def check_cytoscape_running(max_retries=3, retry_delay=2):
    """
    Check if Cytoscape Desktop is running and accessible.
    """
    for attempt in range(max_retries):
        try:
            version = p4c.cytoscape_version_info()
            logging.info(f" Connected to Cytoscape {version['cytoscapeVersion']}")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Attempt {attempt + 1}/{max_retries}: Cytoscape not responding, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logging.error(f" Cannot connect to Cytoscape Desktop after {max_retries} attempts")
                logging.error(f"  Error: {str(e)}")
                logging.error("\n  Please ensure:")
                logging.error("  1. Cytoscape Desktop is installed and running")
                logging.error("  2. CyREST is enabled (should be by default)")
                logging.error("  3. Cytoscape is listening on localhost:1234")
                return False
    return False


def load_network_data(network_file, performance_file=None):
    """
    Load network and optional performance data.
    """
    logging.info(f"Loading network from: {network_file}")
    network_df = pd.read_csv(network_file)

    # normalize column names 
    column_mapping = {}
    for col in network_df.columns:
        col_lower = col.lower()
        if col_lower == 'interactiontype':
            column_mapping[col] = 'InteractionType'

    if column_mapping:
        network_df.rename(columns=column_mapping, inplace=True)
        logging.info(f"  Normalized column names: {list(column_mapping.keys())}")

    # validate required columns
    required_cols = ['Source', 'Target', 'InteractionType', 'Weight']
    missing_cols = [col for col in required_cols if col not in network_df.columns]
    if missing_cols:
        raise ValueError(f"Network file missing required columns: {missing_cols}")

    logging.info(f"  Nodes: ~{len(set(network_df['Source']) | set(network_df['Target']))}")
    logging.info(f"  Edges: {len(network_df)}")

    performance_df = None
    if performance_file:
        logging.info(f"Loading performance metrics from: {performance_file}")
        performance_df = pd.read_csv(performance_file, index_col=0)

    return network_df, performance_df


def create_network_visualization(network_file, output_image, performance_file=None,
                                 layout='force-directed', resolution=300):
    """
    Create and export network visualization in Cytoscape.
    """

    # check cytoscape connection
    if not check_cytoscape_running():
        sys.exit(1)

    # load data
    try:
        network_df, performance_df = load_network_data(network_file, performance_file)
    except Exception as e:
        logging.error(f"Failed to load network data: {e}")
        sys.exit(1)

    # import network into cytoscape
    try:
        logging.info("Importing network into Cytoscape...")

        # Prepare dataframe for Cytoscape (needs lowercase column names for source/target)
        edges_df = network_df[['Source', 'Target', 'InteractionType', 'Weight']].copy()
        edges_df.rename(columns={
            'Source': 'source',
            'Target': 'target',
            'InteractionType': 'interaction',
            'Weight': 'weight'
        }, inplace=True)

        # create network from edge list
        network_suid = p4c.create_network_from_data_frames(
            edges=edges_df,
            title="PanForest_Network",
            collection="PanForest_Collection"
        )

        network_name = p4c.get_network_name()
        logging.info(f" Network imported: {network_name} (SUID: {network_suid})")

    except Exception as e:
        logging.error(f"Failed to import network: {e}")
        sys.exit(1)

    # apply layout
    try:
        logging.info(f"Applying {layout} layout...")
        p4c.layout_network(layout)
        logging.info(" Layout applied")
    except Exception as e:
        logging.warning(f"Layout '{layout}' failed, trying 'force-directed': {e}")
        try:
            p4c.layout_network('force-directed')
        except:
            logging.warning("Using default layout")

    # apply visual styles
    try:
        logging.info("Applying visual styles...")

        # create a new style
        style_name = 'PanForest_Network_Style'
        p4c.create_visual_style(style_name)

        # node defaults
        p4c.set_node_shape_default('ELLIPSE', style_name=style_name)
        p4c.set_node_color_default('#CCCCCC', style_name=style_name)
        p4c.set_node_size_default(40, style_name=style_name)
        p4c.set_node_border_width_default(2, style_name=style_name)
        p4c.set_node_border_color_default('#555555', style_name=style_name)
        p4c.set_node_label_color_default('#000000', style_name=style_name)
        p4c.set_node_font_size_default(10, style_name=style_name)

        # show node labels (gene names)
        p4c.set_node_label_mapping('name', style_name=style_name)

        # edge defaults
        p4c.set_edge_line_width_default(2.0, style_name=style_name)
        p4c.set_edge_target_arrow_shape_default('NONE', style_name=style_name)

        # Edge color mapping based on interaction type
        # pp (positive-positive) = green, nn (negative-negative) = red
        interaction_types = network_df['InteractionType'].unique().tolist()

        if 'pp' in interaction_types and 'nn' in interaction_types:
            p4c.set_edge_color_mapping(
                'interaction',  # Use lowercase column name
                ['pp', 'nn'],
                ['#00AA00', '#AA0000'],  # Green for pp, Red for nn
                mapping_type='discrete',
                style_name=style_name
            )
            logging.info("  ✓ Edge colors: pp=green, nn=red")

        # edge width mapping based on Weight
        if 'Weight' in network_df.columns:
            weights = network_df['Weight'].tolist()
            min_weight = min(weights)
            max_weight = max(weights)

            p4c.set_edge_line_width_mapping(
                'weight',  # lowercase column name
                [min_weight, max_weight],
                [1.0, 5.0],
                mapping_type='continuous',
                style_name=style_name
            )
            logging.info(f"  ✓ Edge width: {min_weight:.2f} → {max_weight:.2f}")

        # node size mapping based on performance (if available)
        if performance_df is not None and 'count' in performance_df.columns:
            # add count as node attribute
            node_names = p4c.get_table_columns(columns='name')['name']

            for node in node_names:
                if node in performance_df.index:
                    count = performance_df.loc[node, 'count']
                    p4c.set_node_property_bypass(
                        node_names=[node],
                        new_values=[int(count)],
                        visual_property='NODE_SIZE'
                    )

            logging.info("  Node sizes based on gene frequency")

        # apply style
        p4c.set_visual_style(style_name)
        logging.info(f"✓ Visual style '{style_name}' applied")

    except Exception as e:
        logging.warning(f"Failed to apply some visual styles: {e}")
        logging.warning("Continuing with default style...")

    # export image
    try:
        logging.info(f"Exporting image to: {output_image}")

        # fit content to window
        p4c.fit_content()

        # export as PNG 
        p4c.export_image(
            filename=output_image,
            type='PNG',
            resolution=resolution
        )

        logging.info(f"✓ Image exported successfully (resolution: {resolution} DPI)")

    except Exception as e:
        logging.error(f"Failed to export image: {e}")
        sys.exit(1)

    # cleanup 
    try:
        # keep the network open just in case manual inspection if needed
        logging.info(f" Network '{network_name}' is still open in Cytoscape for inspection")
        logging.info("  (You can manually close it or leave it open)")
    except:
        pass

    logging.info("=" * 60)
    logging.info(" Network visualization completed successfully!")
    logging.info("=" * 60)


# ============================================
# Snakemake INTEGRATION
# ============================================

if __name__ == "__main__":
    # check if running from Snakemake
    if 'snakemake' in globals():
        # Get parameters from Snakemake
        network_file = snakemake.input.network
        output_image = snakemake.output.image
        performance_file = snakemake.input.get('performance', None)
        layout = snakemake.params.get('layout', 'force-directed')
        resolution = snakemake.params.get('resolution', 300)

        # Run visualization
        create_network_visualization(
            network_file=network_file,
            output_image=output_image,
            performance_file=performance_file,
            layout=layout,
            resolution=resolution
        )
    else:
        # Standalone execution with CLI arguments
        import argparse

        parser = argparse.ArgumentParser(description='Visualize gene networks with Cytoscape')
        parser.add_argument('network', help='Network CSV file (Source,Target,InteractionType,Weight)')
        parser.add_argument('output', help='Output PNG file')
        parser.add_argument('--performance', help='Optional performance CSV file', default=None)
        parser.add_argument('--layout', default='force-directed', help='Layout algorithm')
        parser.add_argument('--resolution', type=int, default=300, help='Image resolution (DPI)')

        args = parser.parse_args()

        create_network_visualization(
            network_file=args.network,
            output_image=args.output,
            performance_file=args.performance,
            layout=args.layout,
            resolution=args.resolution
        )
