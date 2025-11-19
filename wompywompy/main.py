"""main function for argparse."""

import argparse
import json
import sys
from .__init__ import __version__
from .wompwomp import plot_alluvial

# Custom formatter for help messages that preserved the text formatting and adds the default value to the end of the help message
class CustomHelpFormatter(argparse.RawTextHelpFormatter):
    def _get_help_string(self, action):
        help_str = action.help if action.help else ""
        if (
            "%(default)" not in help_str
            and action.default is not argparse.SUPPRESS
            and action.default is not None
            # default information can be deceptive or confusing for boolean flags.
            # For example, `--quiet` says "Does not print progress information. (default: True)" even though
            # the default action is to NOT be quiet (to the user, the default is False).
            and not isinstance(action, argparse._StoreTrueAction)
            and not isinstance(action, argparse._StoreFalseAction)
        ):
            help_str += " (default: %(default)s)"
        return help_str


def main():  # noqa: C901
    """
    CLI entry point for wompwomp's alluvial plotting function.
    """

    parent_parser = argparse.ArgumentParser(description=f"wompwomp v{__version__}", add_help=False)
    parent_subparsers = parent_parser.add_subparsers(dest="command")
    parent = argparse.ArgumentParser(add_help=False)

    # Add custom help/version
    parent_parser.add_argument("-h", "--help", action="store_true", help="Print manual.")
    parent_parser.add_argument("-v", "--version", action="store_true", help="Print version.")

    # Description
    plot_alluvial_desc = "Plot alluvial diagram using wompwomp."

    parser_plot_alluvial = parent_subparsers.add_parser(
        "plot_alluvial",
        parents=[parent],
        description=plot_alluvial_desc,
        help=plot_alluvial_desc,
        add_help=True,
        formatter_class=CustomHelpFormatter,
    )

    # Required
    parser_plot_alluvial.add_argument(
        "--df",
        type=str,
        help="Path to dataframe (.csv or .tsv) containing data to plot."
    )

    # ---------- Graphing ----------
    parser_plot_alluvial.add_argument(
        "--graphing_columns",
        nargs="+",
        default=None,
        help="Columns to include in the alluvial plot (e.g. tissue cluster sex)."
    )
    parser_plot_alluvial.add_argument(
        "--column_weights",
        type=str,
        default=None,
        help="Column name used as weights (like 'value' from group counts)."
    )

    # ---------- Sorting Algorithms ----------
    parser_plot_alluvial.add_argument(
        "--sorting_algorithm",
        type=str,
        default="neighbornet",
        choices=["neighbornet", "tsp", "greedy_wolf", "greedy_wblf"],
        help="Sorting algorithm to use for determining stratum order."
    )
    parser_plot_alluvial.add_argument(
        "--optimize_column_order",
        action="store_true",
        help="Enable column order optimization for neighbornet."
    )
    parser_plot_alluvial.add_argument(
        "--optimize_column_order_per_cycle",
        action="store_true",
        help="Run column optimization every cycle in neighbornet."
    )
    parser_plot_alluvial.add_argument(
        "--matrix_initialization_value",
        type=float,
        default=1e6,
        help="Distance matrix initialization value for neighbornet."
    )
    parser_plot_alluvial.add_argument(
        "--same_side_matrix_initialization_value",
        type=float,
        default=1e6,
        help="Initialization value for same-side distances."
    )
    parser_plot_alluvial.add_argument(
        "--weight_scalar",
        type=float,
        default=5e5,
        help="Weight multiplier for distance updates in neighbornet."
    )

    # ---------- Column Order Optimization ----------
    parser_plot_alluvial.add_argument(
        "--matrix_initialization_value_column_order",
        type=float,
        default=1e6,
        help="Matrix init value for column ordering stage."
    )
    parser_plot_alluvial.add_argument(
        "--weight_scalar_column_order",
        type=float,
        default=1,
        help="Weight scalar for column order calculation."
    )
    parser_plot_alluvial.add_argument(
        "--column_sorting_metric",
        type=str,
        default="edge_crossing",
        help="Metric used when sorting columns."
    )
    parser_plot_alluvial.add_argument(
        "--column_sorting_algorithm",
        type=str,
        default="tsp",
        choices=["tsp", "neighbornet", "greedy_wolf", "greedy_wblf"],
        help="Algorithm used for ordering columns."
    )
    parser_plot_alluvial.add_argument(
        "--cycle_start_positions",
        nargs="+",
        type=int,
        default=None,
        help="Manual start positions for column-order cycles."
    )

    # ---------- Greedy Wolf Options ----------
    parser_plot_alluvial.add_argument(
        "--fixed_column",
        type=str,
        default=None,
        help="Fix a specific column in place when using greedy wolf."
    )
    parser_plot_alluvial.add_argument(
        "--random_initializations",
        type=int,
        default=1,
        help="Number of random starts for greedy algorithms."
    )

    # ---------- User Order ----------
    parser_plot_alluvial.add_argument(
        "--order_dict",
        type=str,
        default=None,
        help="JSON dict specifying manual ordering for each column."
    )
    parser_plot_alluvial.add_argument(
        "--return_order_dict",
        action="store_true",
        help="Return only the order dict without plotting."
    )

    # ---------- Alluvium Options ----------
    parser_plot_alluvial.add_argument(
        "--alluvium_column",
        type=str,
        default=None,
        help="Column specifying alluvium grouping (if not implicit)."
    )
    parser_plot_alluvial.add_argument(
        "--color_alluvium",
        action="store_true",
        help="Color each alluvium by its group."
    )
    parser_plot_alluvial.add_argument(
        "--color_alluvium_boundary",
        action="store_true",
        help="Draw boundaries around alluvia."
    )
    parser_plot_alluvial.add_argument(
        "--alluvial_alpha",
        type=float,
        default=0.5,
        help="Alpha transparency for alluvia."
    )
    parser_plot_alluvial.add_argument(
        "--alluvial_edge_width",
        type=float,
        default=0.1,
        help="Width of alluvium boundary edges."
    )

    # ---------- Coloring Options ----------
    parser_plot_alluvial.add_argument(
        "--match_colors",
        action="store_true",
        help="Ensure identical categories across columns share colors."
    )
    parser_plot_alluvial.add_argument(
        "--coloring_algorithm",
        type=str,
        default="advanced",
        choices=["advanced", "left", "none"],
        help="How to color strata and alluvia."
    )
    parser_plot_alluvial.add_argument(
        "--coloring_algorithm_advanced_option",
        type=str,
        default="leiden",
        help="Advanced coloring option (e.g., leiden clusters)."
    )
    parser_plot_alluvial.add_argument(
        "--resolution",
        type=float,
        default=1.0,
        help="Resolution parameter for advanced coloring algorithms."
    )
    parser_plot_alluvial.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Threshold for advanced color merging."
    )
    parser_plot_alluvial.add_argument(
        "--color_dict",
        type=str,
        default=None,
        help="JSON mapping for manually assigned colors."
    )
    parser_plot_alluvial.add_argument(
        "--fill_missing_colors",
        action="store_true",
        help="Fill missing colors from colormap."
    )
    parser_plot_alluvial.add_argument(
        "--cmap_name",
        type=str,
        default="tab20",
        help="Name of Matplotlib colormap to use."
    )

    # ---------- Stratum Boxes ----------
    parser_plot_alluvial.add_argument(
        "--color_boxes",
        action="store_true",
        help="Draw colored stratum boxes."
    )
    parser_plot_alluvial.add_argument(
        "--include_labels_in_boxes",
        action="store_true",
        help="Include labels inside stratum boxes."
    )
    parser_plot_alluvial.add_argument(
        "--box_line_width",
        type=float,
        default=1,
        help="Line width of stratum boxes."
    )
    parser_plot_alluvial.add_argument(
        "--box_width",
        type=float,
        default=0.4,
        help="Width of each stratum box."
    )

    # ---------- Text Options ----------
    parser_plot_alluvial.add_argument(
        "--min_text",
        type=int,
        default=4,
        help="Minimum fraction of area required to draw text."
    )
    parser_plot_alluvial.add_argument(
        "--default_text_size",
        type=int,
        default=14,
        help="Default text size for strata labels."
    )
    parser_plot_alluvial.add_argument(
        "--default_axis_text_size",
        type=int,
        default=None,
        help="Axis label text size."
    )
    parser_plot_alluvial.add_argument(
        "--default_label_text_size",
        type=int,
        default=None,
        help="Label text size inside boxes."
    )
    parser_plot_alluvial.add_argument(
        "--autofit_text",
        action="store_true",
        help="Shrink text automatically to fit inside a box."
    )
    parser_plot_alluvial.add_argument(
        "--drop_if_min",
        action="store_true",
        help="Drop text if it fails min_text threshold."
    )

    # ---------- Axes ----------
    parser_plot_alluvial.add_argument(
        "--y_axis_label",
        action="store_true",
        help="Display y-axis label."
    )
    parser_plot_alluvial.add_argument(
        "--invert_xy",
        action="store_true",
        help="Invert X/Y axes (horizontal vs vertical plots)."
    )

    # ---------- Legend ----------
    parser_plot_alluvial.add_argument(
        "--include_stratum_legend",
        action="store_true",
        help="Add legend for stratum colors."
    )
    parser_plot_alluvial.add_argument(
        "--include_alluvium_legend",
        action="store_true",
        help="Add legend for alluvium groups."
    )
    parser_plot_alluvial.add_argument(
        "--legend_loc",
        type=str,
        default="right",
        help="Legend location."
    )

    # ---------- Figure Size ----------
    parser_plot_alluvial.add_argument(
        "--save_height",
        type=float,
        default=6,
        help="Height of saved figure."
    )
    parser_plot_alluvial.add_argument(
        "--save_width",
        type=float,
        default=6,
        help="Width of saved figure."
    )

    # ---------- I/O ----------
    parser_plot_alluvial.add_argument(
        "--savefig",
        action="store_true",
        help="Save the figure instead of displaying."
    )
    parser_plot_alluvial.add_argument(
        "--out",
        type=str,
        default="alluvial_plot.png",
        help="Output filename."
    )
    parser_plot_alluvial.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose mode."
    )

    args, unknown_args = parent_parser.parse_known_args()

    # Help/version behavior
    if args.help:
        subparsers_actions = [a for a in parent_parser._actions if isinstance(a, argparse._SubParsersAction)]
        for action in subparsers_actions:
            for choice, subparser in action.choices.items():
                print(f"Subparser '{choice}'")
                print(subparser.format_help())
        sys.exit(1)

    if args.version:
        print(f"wompwomp version: {__version__}")
        sys.exit(1)

    if len(sys.argv) == 1:
        parent_parser.print_help(sys.stderr)
        sys.exit(1)

    command_to_parser = {
        "plot_alluvial": parser_plot_alluvial,
    }

    if len(sys.argv) == 2:
        if sys.argv[1] in command_to_parser:
            command_to_parser[sys.argv[1]].print_help(sys.stderr)
        else:
            parent_parser.print_help(sys.stderr)
        sys.exit(1)

    # Run command
    if args.command == "plot_alluvial":
        # Parse JSON fields
        order_dict = json.loads(args.order_dict) if args.order_dict else None
        color_dict = json.loads(args.color_dict) if args.color_dict else None

        fig = plot_alluvial(
            df=args.df,
            graphing_columns=args.graphing_columns,
            column_weights=args.column_weights,
            sorting_algorithm=args.sorting_algorithm,
            optimize_column_order=args.optimize_column_order,
            optimize_column_order_per_cycle=args.optimize_column_order_per_cycle,
            matrix_initialization_value=args.matrix_initialization_value,
            same_side_matrix_initialization_value=args.same_side_matrix_initialization_value,
            weight_scalar=args.weight_scalar,
            matrix_initialization_value_column_order=args.matrix_initialization_value_column_order,
            weight_scalar_column_order=args.weight_scalar_column_order,
            column_sorting_metric=args.column_sorting_metric,
            column_sorting_algorithm=args.column_sorting_algorithm,
            cycle_start_positions=args.cycle_start_positions,
            fixed_column=args.fixed_column,
            random_initializations=args.random_initializations,
            order_dict=order_dict,
            return_order_dict=args.return_order_dict,
            alluvium_column=args.alluvium_column,
            color_alluvium=args.color_alluvium,
            color_alluvium_boundary=args.color_alluvium_boundary,
            alluvial_alpha=args.alluvial_alpha,
            alluvial_edge_width=args.alluvial_edge_width,
            match_colors=args.match_colors,
            coloring_algorithm=args.coloring_algorithm,
            coloring_algorithm_advanced_option=args.coloring_algorithm_advanced_option,
            resolution=args.resolution,
            threshold=args.threshold,
            color_dict=color_dict,
            fill_missing_colors=args.fill_missing_colors,
            cmap_name=args.cmap_name,
            color_boxes=args.color_boxes,
            include_labels_in_boxes=args.include_labels_in_boxes,
            box_line_width=args.box_line_width,
            box_width=args.box_width,
            min_text=args.min_text,
            default_text_size=args.default_text_size,
            default_axis_text_size=args.default_axis_text_size,
            default_label_text_size=args.default_label_text_size,
            autofit_text=args.autofit_text,
            drop_if_min=args.drop_if_min,
            y_axis_label=args.y_axis_label,
            invert_xy=args.invert_xy,
            include_stratum_legend=args.include_stratum_legend,
            include_alluvium_legend=args.include_alluvium_legend,
            legend_loc=args.legend_loc,
            save_height=args.save_height,
            save_width=args.save_width,
            verbose=args.verbose,
            savefig=args.savefig,
        )

        # fig = fig[0] if isinstance(fig, tuple) else fig
        # fig.show()
