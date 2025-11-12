"""main function for argparse."""

import argparse
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
        "df",
        type=str,
        help="Path to dataframe file (.csv or .tsv) containing the data to plot."
    )

    # Optional args
    parser_plot_alluvial.add_argument(
        "--graphing_columns",
        nargs="+",
        default=None,
        help="List of columns to include in the alluvial plot."
    )
    parser_plot_alluvial.add_argument(
        "--sorting_algorithm",
        type=str,
        default="neighbornet",
        choices=["neighbornet", "tsp", "greedy_wolf", "greedy_wblf"],
        help="Sorting algorithm to use for stratum ordering."
    )
    parser_plot_alluvial.add_argument(
        "--color_alluvium",
        action="store_true",
        help="Color alluvia according to group or stratum."
    )
    parser_plot_alluvial.add_argument(
        "--match_colors",
        action="store_true",
        help="Ensure matching colors for identical categories across strata."
    )
    parser_plot_alluvial.add_argument(
        "--savefig",
        action="store_true",
        help="Save the figure instead of displaying it."
    )
    parser_plot_alluvial.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    parser_plot_alluvial.add_argument(
        "--out",
        type=str,
        default="alluvial_plot.png",
        help="Output file name for saved plot."
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
        plot_alluvial(
            df=args.df,
            graphing_columns=args.graphing_columns,
            sorting_algorithm=args.sorting_algorithm,
            color_alluvium=args.color_alluvium,
            match_colors=args.match_colors,
            savefig=args.savefig,
            verbose=args.verbose,
            out=args.out,
        )
