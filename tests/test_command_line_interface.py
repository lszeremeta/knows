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
    monkeypatch.setattr('sys.argv', ['prog', '5', '4'])
    cli = CommandLineInterface()
    assert cli.args.nodes == 5
    assert cli.args.edges == 4
    assert cli.args.format == 'graphml'
    assert not cli.args.draw


@pytest.mark.parametrize("args, expected_nodes, expected_edges, expected_format, expected_draw",
    [(['prog', '10', '8'], 10, 8, 'graphml', False), (['prog'], None, None, 'graphml', False),
        (['prog', '--format', 'json'], None, None, 'json', False), (['prog', '-d'], None, None, 'graphml', True),
        (['prog', '10', '8', '--format', 'yarspg'], 10, 8, 'yarspg', False), ])
def test_cli_various_args(monkeypatch, args, expected_nodes, expected_edges, expected_format, expected_draw):
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
