import pytest

from knows.command_line_interface import CommandLineInterface


def test_cli_default_args(monkeypatch):
    """
    Test if the CLI sets default arguments correctly.

    Checks if the CommandLineInterface sets default values correctly
    when no optional arguments are provided, but only mandatory ones.

    Args:
        monkeypatch: A pytest fixture for monkey-patching.
    """
    monkeypatch.setattr('sys.argv', ['prog', '-n', '5', '-e', '4'])
    cli = CommandLineInterface()
    assert cli.args.nodes == 5
    assert cli.args.edges == 4
    assert cli.args.format == 'graphml'
    assert not cli.args.draw
    assert cli.args.node_props == ['firstName', 'lastName']
    assert cli.args.edge_props == ['createDate']


@pytest.mark.parametrize(
    "args, expected_nodes, expected_edges, expected_format, expected_draw, node_props, edge_props",
    [
        (['prog', '-n', '10', '-e', '8'], 10, 8, 'graphml', False, ['firstName', 'lastName'], ['createDate']),
        (['prog'], None, None, 'graphml', False, ['firstName', 'lastName'], ['createDate']),
        (['prog', '-n', '10', '-e', '8', '--format', 'yarspg'], 10, 8, 'yarspg', False, ['firstName', 'lastName'],
         ['createDate']),
        (['prog', '--format', 'csv'], None, None, 'csv', False, ['firstName', 'lastName'], ['createDate']),
        (['prog', '--format', 'cypher'], None, None, 'cypher', False, ['firstName', 'lastName'], ['createDate']),
        (['prog', '--format', 'json'], None, None, 'json', False, ['firstName', 'lastName'], ['createDate']),
        (['prog', '-d'], None, None, 'graphml', True, ['firstName', 'lastName'], ['createDate']),
        (['prog', '--node-props', 'favoriteColor', 'job'], None, None, 'graphml', False, ['favoriteColor', 'job'],
         ['createDate']),
        (['prog', '--edge-props', 'meetingCity'], None, None, 'graphml', False, ['firstName', 'lastName'],
         ['meetingCity']),
        (['prog', '-np', 'company', 'job'], None, None, 'graphml', False, ['company', 'job'], ['createDate']),
        (['prog', '-ep', 'strength'], None, None, 'graphml', False, ['firstName', 'lastName'], ['strength']),
        (['prog', '--all-props'], None, None, 'graphml', False,
         ['firstName', 'lastName', 'company', 'job', 'phoneNumber', 'favoriteColor'],
         ['createDate', 'meetingCity', 'strength']),
    ],
)
def test_cli_various_args(monkeypatch, args, expected_nodes, expected_edges, expected_format, expected_draw, node_props,
                          edge_props):
    """
    Test if the CLI correctly parses various argument combinations.

    Checks if the CommandLineInterface correctly interprets different combinations
    of command-line arguments, including default values, optional flags, and their absence.

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
