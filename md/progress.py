class NoBar:
    """Does nothing; same shape as mo.status.progress_bar (context manager with update)."""

    def __init__(self, total, title):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def update(self, increment=1, title=None, subtitle=None):
        pass
