## ADDED Requirements

### Requirement: Configurable answer backend

The system SHALL expose an answer-backend setting in configuration with the
values `engine` and `agent`, defaulting to `engine`. The CLI and the HTTP server
SHALL resolve their answer backend through a single shared factory so that both
entry points use the same backend for a given configuration.

#### Scenario: Engine is the default backend
- **WHEN** the configuration contains no explicit backend setting
- **THEN** the CLI and HTTP server answer requests using the deterministic engine

#### Scenario: Agent backend is selected
- **WHEN** the configuration sets the answer backend to `agent`
- **THEN** the CLI and HTTP server answer requests using the pydantic-ai agent

#### Scenario: Engine remains available as a fallback
- **WHEN** the backend is set to `engine`
- **THEN** the answer is produced without constructing the agent

### Requirement: Invalid backend value is rejected

The system MUST reject an unknown answer-backend value at configuration load with
an error naming the valid options (`engine`, `agent`) rather than silently
falling back.

#### Scenario: Unknown backend is rejected
- **WHEN** the configuration sets the answer backend to an unsupported value
- **THEN** configuration loading fails with an error naming `engine` and `agent`

### Requirement: Shared backend abstraction

Both backends SHALL implement one shared interface exposing `ask`, `ask_async`,
`get_related_chunks`, and a `default_mode` attribute. The CLI and the HTTP server
MUST depend only on this interface, not on a concrete backend class.

#### Scenario: Both backends satisfy the interface
- **WHEN** the factory returns either the engine or the agent backend
- **THEN** the returned object provides `ask`, `ask_async`, `get_related_chunks`,
  and a mutable `default_mode`

#### Scenario: Entry points are backend-agnostic
- **WHEN** a request is served through the CLI or the HTTP server
- **THEN** the same interface methods are used regardless of the configured
  backend

### Requirement: Backend independence

The engine and the agent SHALL be independent implementations such that using
one does not require loading or constructing the other.

#### Scenario: Engine does not require the agent
- **WHEN** the backend is `engine`
- **THEN** the agent module is not needed to answer a request

#### Scenario: Agent does not require the engine
- **WHEN** the backend is `agent`
- **THEN** the engine is not constructed to answer a request
