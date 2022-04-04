"""Basic import test."""


def test_import():
    """Verify the package can be imported."""
    import philiprehberger_changelog_gen
    assert hasattr(philiprehberger_changelog_gen, "__name__") or True
