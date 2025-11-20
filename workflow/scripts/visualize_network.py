
"""
Automatic network visualization using Cytoscape and py4cytoscape.
Generates network images from gene interaction data.
"""

import sys
import pandas as pd
import time
import logging
import os

# Configure logging 
logger = logging.getLogger(__name__)

try:
    import py4cytoscape as p4c

    # disable py4cytoscape's file logging after import
    p4c_logger_temp = logging.getLogger('py4cytoscape')
    for handler in p4c_logger_temp.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        p4c_logger_temp.removeHandler(handler)

except ImportError:
    logger.error("py4cytoscape not installed. Install with: pip install py4cytoscape")
    sys.exit(1)


def setup_logging(log_file=None):
    """
    Configure logging to write to both console and file.
    Also configures py4cytoscape logging to use the same handlers.
    Also redirects py4cytoscape's default log file to the visualization folder.
    """
    # Create formatters and handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure py4cytoscape logger to use the same handlers and disable its own file logging
    p4c_logger = logging.getLogger('py4cytoscape')
    p4c_logger.setLevel(logging.INFO)

    # Remove all existing handlers (including any file handlers py4cytoscape created)
    for handler in p4c_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        p4c_logger.removeHandler(handler)

    # Make py4cytoscape use root logger's handlers instead
    p4c_logger.propagate = True

    return root_logger


def _cleanup_p4c_file_handlers():
    """
    Remove any FileHandlers from py4cytoscape logger to prevent it from creating log files.
    Also ensures py4cytoscape propagates logs to root logger.
    """
    p4c_logger = logging.getLogger('py4cytoscape')

    # Remove all FileHandlers
    handlers_to_remove = []
    for handler in p4c_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handlers_to_remove.append(handler)

    for handler in handlers_to_remove:
        handler.close()
        p4c_logger.removeHandler(handler)

    # Ensure propagation is enabled
    p4c_logger.propagate = True


def _move_p4c_log_to_visualization():
    """
    Move py4cytoscape's log file from logs/ to logs/visualization/ after execution.
    """
    import shutil

    p4c_default_log = os.path.join('logs', 'py4cytoscape.log')
    p4c_target_log = os.path.join('logs', 'visualization', 'py4cytoscape.log')

    if os.path.exists(p4c_default_log) and not os.path.islink(p4c_default_log):
        try:
            # Close all file handlers first to release the file
            _cleanup_p4c_file_handlers()
            time.sleep(0.1)  # Wait for handles to release

            # Create target directory if needed
            os.makedirs(os.path.dirname(p4c_target_log), exist_ok=True)

            # Move the file
            shutil.move(p4c_default_log, p4c_target_log)
        except Exception as e:
            # If move fails, try to at least log it
            pass


def check_cytoscape_running(max_retries=3, retry_delay=2):
    """
    Check if Cytoscape Desktop is running and accessible.
    """
    # Clean up any file handlers that py4cytoscape might have created
    _cleanup_p4c_file_handlers()

    for attempt in range(max_retries):
        try:
            version = p4c.cytoscape_version_info()
            # Clean up again after first API call 
            _cleanup_p4c_file_handlers()
            logger.info(f" Connected to Cytoscape {version['cytoscapeVersion']}")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: Cytoscape not responding, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f" Cannot connect to Cytoscape Desktop after {max_retries} attempts")
                logger.error(f"  Error: {str(e)}")
                logger.error("\n  Please ensure:")
                logger.error("  1. Cytoscape Desktop is installed and running")
                logger.error("  2. CyREST is enabled (should be by default)")
                logger.error("  3. Cytoscape is listening on localhost:1234")
                return False
    return False


def load_network_data(network_file, performance_file=None):
    """
    Load network and optional performance data.
    """
    logger.info(f"Loading network from: {network_file}")
    network_df = pd.read_csv(network_file)

    # normalize column names
    column_mapping = {}
    for col in network_df.columns:
        col_lower = col.lower()
        if col_lower == 'interactiontype':
            column_mapping[col] = 'InteractionType'

    if column_mapping:
        network_df.rename(columns=column_mapping, inplace=True)
        logger.info(f"  Normalized column names: {list(column_mapping.keys())}")

    # validate required columns
    required_cols = ['Source', 'Target', 'InteractionType', 'Weight']
    missing_cols = [col for col in required_cols if col not in network_df.columns]
    if missing_cols:
        raise ValueError(f"Network file missing required columns: {missing_cols}")

    logger.info(f"  Nodes: ~{len(set(network_df['Source']) | set(network_df['Target']))}")
    logger.info(f"  Edges: {len(network_df)}")

    performance_df = None
    if performance_file:
        logger.info(f"Loading performance metrics from: {performance_file}")
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
        logger.error(f"Failed to load network data: {e}")
        sys.exit(1)

    # import network into cytoscape
    try:
        logger.info("Importing network into Cytoscape...")

        # Clean up any file handlers before heavy py4cytoscape operations
        _cleanup_p4c_file_handlers()

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
        logger.info(f" Network imported: {network_name} (SUID: {network_suid})")

        # Clean up any file handlers that were created during import
        _cleanup_p4c_file_handlers()

    except Exception as e:
        logger.error(f"Failed to import network: {e}")
        sys.exit(1)

    # apply layout
    try:
        logger.info(f"Applying {layout} layout...")
        p4c.layout_network(layout)
        logger.info(" Layout applied")
    except Exception as e:
        logger.warning(f"Layout '{layout}' failed, trying 'force-directed': {e}")
        try:
            p4c.layout_network('force-directed')
        except:
            logger.warning("Using default layout")

    # apply visual styles
    try:
        logger.info("Applying visual styles...")

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
            logger.info("  ✓ Edge colors: pp=green, nn=red")

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
            logger.info(f"  ✓ Edge width: {min_weight:.2f} → {max_weight:.2f}")

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

            logger.info("  Node sizes based on gene frequency")

        # apply style
        p4c.set_visual_style(style_name)
        logger.info(f"✓ Visual style '{style_name}' applied")

    except Exception as e:
        logger.warning(f"Failed to apply some visual styles: {e}")
        logger.warning("Continuing with default style...")

    # export image
    try:
        logger.info(f"Exporting image to: {output_image}")

        # fit content to window
        p4c.fit_content()

        # export as PNG
        p4c.export_image(
            filename=output_image,
            type='PNG',
            resolution=resolution
        )

        logger.info(f"✓ Image exported successfully (resolution: {resolution} DPI)")

    except Exception as e:
        logger.error(f"Failed to export image: {e}")
        sys.exit(1)

    # cleanup
    try:
        # keep the network open just in case manual inspection if needed
        logger.info(f" Network '{network_name}' is still open in Cytoscape for inspection")
        logger.info("  (You can manually close it or leave it open)")
    except:
        pass

    logger.info("=" * 60)
    logger.info(" Network visualization completed successfully!")
    logger.info("=" * 60)

    # Move py4cytoscape's log file to visualization folder if it exists
    _move_p4c_log_to_visualization()


# ============================================
# Snakemake INTEGRATION
# ============================================

if __name__ == "__main__":
    # check if running from Snakemake
    if 'snakemake' in globals():
        # Setup logging with Snakemake's log file
        log_file = snakemake.log[0] if snakemake.log else None
        setup_logging(log_file)

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
        parser.add_argument('--log', help='Log file path (optional)', default=None)

        args = parser.parse_args()

        # Setup logging
        setup_logging(args.log)

        create_network_visualization(
            network_file=args.network,
            output_image=args.output,
            performance_file=args.performance,
            layout=args.layout,
            resolution=args.resolution
        )
