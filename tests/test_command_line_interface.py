"""Tests for the command-line interface argument parsing."""

import pytest

from knows import __version__
from knows.command_line_interface import CommandLineInterface
from knows.graph import NODE_PROPERTIES, SAME_EDGE_PROPS, EDGE_PROPERTIES


def test_cli_default_args(monkeypatch):
    """Test if the CLI sets default arguments correctly.

    Checks if the CommandLineInterface sets default values correctly when
    no optional arguments are provided, but only mandatory ones.

    Args:
        monkeypatch: A pytest fixture for monkey-patching.
    """
    monkeypatch.setattr('sys.argv', ['prog', '-n', '5', '-e', '4'])
    cli = CommandLineInterface()
    assert cli.args.nodes == 5
    assert cli.args.edges == 4
    assert cli.args.format == 'yarspg'
    assert not cli.args.draw
    assert cli.args.node_props == ['firstName', 'lastName']
    assert cli.args.edge_props == ['strength', 'lastMeetingDate']
    assert cli.args.seed is None
    assert cli.args.output is None


@pytest.mark.parametrize(
    "args, expected_nodes, expected_edges, expected_format, expected_draw, node_props, edge_props",
    [
        (['prog', '-n', '10', '-e', '8'], 10, 8, 'yarspg', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog'], None, None, 'yarspg', False, ['firstName', 'lastName'], ['strength', 'lastMeetingDate']),
        (['prog', '-n', '10', '-e', '8', '--format', 'yarspg'], 10, 8, 'yarspg', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'csv'], None, None, 'csv', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'cypher'], None, None, 'cypher', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'json'], None, None, 'json', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'gexf'], None, None, 'gexf', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'gml'], None, None, 'gml', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'svg'], None, None, 'svg', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'png'], None, None, 'png', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'jpg'], None, None, 'jpg', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'pdf'], None, None, 'pdf', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'adjacency_list'], None, None, 'adjacency_list', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'multiline_adjacency_list'], None, None, 'multiline_adjacency_list', False,
         ['firstName', 'lastName'], ['strength', 'lastMeetingDate']),
        (['prog', '--format', 'edge_list'], None, None, 'edge_list', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
        (['prog', '-d'], None, None, 'yarspg', True, ['firstName', 'lastName'], ['strength', 'lastMeetingDate']),
        (['prog', '--node-props', 'favoriteColor', 'job'], None, None, 'yarspg', False, ['favoriteColor', 'job'],
         ['strength', 'lastMeetingDate']),
        (['prog', '--edge-props', 'lastMeetingCity'], None, None, 'yarspg', False, ['firstName', 'lastName'],
         ['lastMeetingCity']),
        (['prog', '-np', 'company', 'job'], None, None, 'yarspg', False, ['company', 'job'],
         ['strength', 'lastMeetingDate']),
        (['prog', '-ep', 'strength'], None, None, 'yarspg', False, ['firstName', 'lastName'], ['strength']),
        (
                ['prog', '--node-props', 'postalAddress', 'friendCount', 'preferredContactMethod'],
                None,
                None,
                'yarspg',
                False,
                ['postalAddress', 'friendCount', 'preferredContactMethod'],
                ['strength', 'lastMeetingDate'],
        ),
        (
                ['prog', '--edge-props', *SAME_EDGE_PROPS],
                None,
                None,
                'yarspg',
                False,
                ['firstName', 'lastName'],
                list(SAME_EDGE_PROPS),
        ),
        (
                ['prog', '--all-props'],
                None,
                None,
                'yarspg',
                False,
                # Use NODE_PROPERTIES directly to avoid order dependency
                NODE_PROPERTIES,
                EDGE_PROPERTIES,
        ),
        (['prog', '--seed', '42'], None, None, 'yarspg', False, ['firstName', 'lastName'],
         ['strength', 'lastMeetingDate']),
    ],
)
def test_cli_various_args(monkeypatch, args, expected_nodes, expected_edges, expected_format, expected_draw, node_props,
                          edge_props):
    """Test parsing of various command-line argument combinations.

    Checks if the CommandLineInterface correctly interprets different
    combinations of command-line arguments, including default values,
    optional flags, and their absence.

    Args:
        monkeypatch: A pytest fixture for monkey-patching.
        args (list): The list of command line arguments to test.
        expected_nodes (int): Expected number of nodes parsed.
        expected_edges (int): Expected number of edges parsed.
        expected_format (str): Expected format parsed.
        expected_draw (bool): Expected state of the draw flag.
    """
    monkeypatch.setattr('sys.argv', args)
    cli = CommandLineInterface()
    assert cli.args.nodes == expected_nodes
    assert cli.args.edges == expected_edges
    assert cli.args.format == expected_format
    assert cli.args.draw == expected_draw
    assert cli.args.node_props == node_props
    assert cli.args.edge_props == edge_props
    if '--seed' in args or '-s' in args:
        assert cli.args.seed == 42
    else:
        assert cli.args.seed is None


def test_cli_output_file(monkeypatch, tmp_path):
    """Test if CLI correctly parses optional output file path.

    Args:
        monkeypatch: A pytest fixture for monkey-patching.
        tmp_path (pathlib.Path): Temporary directory for output files.
    """
    output_file = tmp_path / "graph.yarspg"
    monkeypatch.setattr('sys.argv', ['prog', str(output_file)])
    cli = CommandLineInterface()
    assert cli.args.output == str(output_file)


def test_cli_seed_short_option(monkeypatch):
    """Ensure short seed option is parsed."""
    monkeypatch.setattr('sys.argv', ['prog', '-s', '123'])
    cli = CommandLineInterface()
    assert cli.args.seed == 123


def test_cli_all_props_short_option(monkeypatch):
    """Ensure short all-props option is parsed."""
    monkeypatch.setattr('sys.argv', ['prog', '-ap'])
    cli = CommandLineInterface()
    assert cli.args.node_props == NODE_PROPERTIES
    assert cli.args.edge_props == EDGE_PROPERTIES


def test_cli_version_option(monkeypatch, capsys):
    """Ensure version option outputs current version and exits."""
    monkeypatch.setattr('sys.argv', ['prog', '--version'])
    with pytest.raises(SystemExit) as excinfo:
        CommandLineInterface()

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == f"knows {__version__}"


def test_cli_default_limit(monkeypatch):
    """Ensure default limit is 50."""
    monkeypatch.setattr('sys.argv', ['prog'])
    cli = CommandLineInterface()
    assert cli.args.limit == 50


def test_cli_custom_limit(monkeypatch):
    """Ensure custom limit is parsed."""
    monkeypatch.setattr('sys.argv', ['prog', '--limit', '100'])
    cli = CommandLineInterface()
    assert cli.args.limit == 100


def test_cli_limit_short_option(monkeypatch):
    """Ensure short limit option is parsed."""
    monkeypatch.setattr('sys.argv', ['prog', '-l', '75'])
    cli = CommandLineInterface()
    assert cli.args.limit == 75


def test_cli_no_limit_option(monkeypatch):
    """Ensure --no-limit sets limit to 0."""
    monkeypatch.setattr('sys.argv', ['prog', '--no-limit'])
    cli = CommandLineInterface()
    assert cli.args.limit == 0


def test_cli_hide_info_option(monkeypatch):
    """Ensure --hide-info sets show_info to False."""
    monkeypatch.setattr('sys.argv', ['prog', '--hide-info'])
    cli = CommandLineInterface()
    assert cli.args.show_info is False


def test_cli_default_show_info(monkeypatch):
    """Ensure show_info defaults to True."""
    monkeypatch.setattr('sys.argv', ['prog'])
    cli = CommandLineInterface()
    assert cli.args.show_info is True