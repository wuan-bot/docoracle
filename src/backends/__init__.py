"""Answer backends for Home Q&A.

Houses the two interchangeable answer paths behind the shared
:class:`~src.backends.protocol.AnswerBackend` interface:

- :mod:`src.backends.engine` — deterministic retrieve-then-answer pipeline.
- :mod:`src.backends.agent` — pydantic-ai agent that decides when to retrieve.

Use :func:`~src.backends.factory.create_answer_backend` to build the backend
selected by configuration.
"""
