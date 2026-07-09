import os


def get_xoras_langgraph_engine():
    mode = os.environ.get("XORAS_TEST_MODE", "mock")
    if mode == "real":
        try:
            import Source.xoras_langgraph_engine as m
            return m
        except ImportError:
            import Source.tests.e2e.mocks.xoras_langgraph_engine as m
            return m
    else:
        import Source.tests.e2e.mocks.xoras_langgraph_engine as m
        return m


def get_xoras_vector_db():
    mode = os.environ.get("XORAS_TEST_MODE", "mock")
    if mode == "real":
        try:
            import Source.xoras_vector_db as m
            return m
        except ImportError:
            import Source.tests.e2e.mocks.xoras_vector_db as m
            return m
    else:
        import Source.tests.e2e.mocks.xoras_vector_db as m
        return m


def get_xoras_sandbox():
    mode = os.environ.get("XORAS_TEST_MODE", "mock")
    if mode == "real":
        try:
            import Source.xoras_sandbox as m
            return m
        except ImportError:
            import Source.tests.e2e.mocks.xoras_sandbox as m
            return m
    else:
        import Source.tests.e2e.mocks.xoras_sandbox as m
        return m
