# Copyright 2015-2026 Earth Sciences Department, BSC-CNS
#
# This file is part of Autosubmit.
#
# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.


"""Unit tests for the ``autosubmit.scripts._entry_points`` module."""

import pytest

# noinspection PyProtectedMember
from autosubmit.scripts._entry_points import (
    execute_cmd,
    get_commands,
    iter_commands,
    iter_entry_points,
    parse_docstring,
)


def test_execute_cmd_missing_dependency(capsys, mocker):
    """Test a command that requires a missing optional dependency."""
    entry_point = mocker.Mock()
    entry_point.name = "scooby"
    entry_point.dist.name = "autosubmit-scooby"
    entry_point.extras = []

    entry_point.load.side_effect = ModuleNotFoundError("No module named 'scoobydoo'")

    result = execute_cmd(entry_point)

    assert result == 1
    assert capsys.readouterr().err == (
        '"autosubmit scooby" requires "autosubmit-scooby"\n\n'
        "ModuleNotFoundError: No module named 'scoobydoo'\n"
    )


@pytest.mark.parametrize(
    "docstring, expected",
    [
        (
            "run\nStarts an experiment workflow.",
            ("run", "Starts an experiment workflow."),
        ),
        (
            "configure\n",
            ("configure", None),
        ),
        (
            "",
            (None, None),
        ),
    ],
    ids=[
        "name-and-description",
        "name-only",
        "empty",
    ],
)
def test_parse_docstring(docstring, expected):
    """Test parsing a command docstring."""
    assert parse_docstring(docstring) == expected


def test_iter_entry_points(mocker):
    """Test iterating over Autosubmit entry points."""
    entry_point_1 = mocker.Mock(name="clean")
    entry_point_2 = mocker.Mock(name="run")

    mock_entry_points = mocker.patch(
        "importlib.metadata.entry_points",
        return_value=[entry_point_1, entry_point_2],
    )

    result = list(iter_entry_points("autosubmit.command"))

    assert result == [entry_point_1, entry_point_2]
    mock_entry_points.assert_called_once_with(group="autosubmit.command")


def test_get_commands(mocker):
    """Test retrieving Autosubmit commands from entry points."""
    clean = mocker.Mock()
    clean.name = "clean"

    run = mocker.Mock()
    run.name = "run"

    mocker.patch(
        "autosubmit.scripts._entry_points.iter_entry_points",
        return_value=[clean, run],
    )

    assert get_commands() == {
        "clean": clean,
        "run": run,
    }


def test_iter_commands(mocker):
    """Test iterating over available commands."""
    entry_point = mocker.Mock()
    entry_point.module = "autosubmit.scripts.run"

    module = mocker.Mock()
    module.INTERNAL = False
    module.__doc__ = "run\nStarts an experiment workflow."

    mocker.patch(
        "builtins.__import__",
        return_value=module,
    )

    commands = {
        "run": entry_point,
    }

    assert list(iter_commands(commands)) == [
        (
            "run",
            "Starts an experiment workflow.",
            "run",
            module,
        )
    ]


def test_iter_commands_skips_internal_command(mocker):
    """Test that internal commands are not returned."""
    entry_point = mocker.Mock()
    entry_point.module = "autosubmit.scripts.internal"

    module = mocker.Mock()
    module.INTERNAL = True

    mocker.patch(
        "builtins.__import__",
        return_value=module,
    )

    assert list(iter_commands({"internal": entry_point})) == []


def test_iter_commands_skips_missing_dependency(mocker):
    """Test that commands with missing dependencies are skipped."""
    entry_point = mocker.Mock()
    entry_point.module = "autosubmit.scripts.scooby"
    entry_point.name = "scooby"
    entry_point.dist.name = "autosubmit-scooby"
    entry_point.extras = []

    mocker.patch(
        "builtins.__import__",
        side_effect=ModuleNotFoundError("No module named 'scoobydoo'"),
    )

    assert list(iter_commands({"scooby": entry_point})) == []


def test_handle_missing_dependency(mocker):
    """Test the missing dependency error message."""
    entry_point = mocker.Mock()
    entry_point.name = "scooby"
    entry_point.dist.name = "autosubmit-scooby"
    entry_point.extras = ["plot", "stats"]

    error = ModuleNotFoundError("No module named 'scoobydoo'")

    # noinspection PyProtectedMember
    from autosubmit.scripts._entry_points import _handle_missing_dependency

    assert _handle_missing_dependency(entry_point, error) == (
        '"autosubmit scooby" requires "autosubmit-scooby[plot,stats]"\n\n'
        "ModuleNotFoundError: No module named 'scoobydoo'"
    )
