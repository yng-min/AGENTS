# Repository Agent Instructions

## 1. Scope

These instructions apply to the entire repository.

Before analyzing, reviewing, modifying, or generating code, read and follow the required documents defined in this file.

Do not begin implementation before completing the required document review.

## 2. Required Agent Documents

The following documents are mandatory for every task:

- `docs/agents/python-style-guide.ko.md`
- `docs/agents/decision-making-principles.ko.md`

The required documents are written in Korean.

Read and interpret them directly in Korean without translating, simplifying, summarizing, or weakening their requirements.

Read both documents in full before making implementation or design decisions.

These documents define the repository's general standards for:

- Python coding style and formatting
- naming and type-hint policies
- import organization
- result objects and exception handling
- architecture and responsibility boundaries
- maintainability and operational-cost priorities
- abstraction and automation criteria
- implementation trade-offs and decision-making

Do not rely on a remembered, inferred, summarized, or abbreviated version of these documents.

The full documents are authoritative.

When reporting completed work, explicitly confirm that both required documents were reviewed.

## 3. Project Documentation

The `docs/` directory contains project-specific documentation, including architecture, configuration, database, deployment, operation, and historical decision records.

Before modifying code:

1. Inspect the directory structure and filenames under `docs/`.
2. Identify documents related to the requested task and affected modules.
3. Read the relevant documents before implementation.
4. Use them to understand the existing architecture, terminology, operational constraints, known limitations, and historical decisions.

Do not mechanically read every document under `docs/` when it has no reasonable relationship to the task.

When uncertain whether a document is relevant, prefer reading it before modifying the associated code.

Documents under `docs/agents/` are governed by the mandatory rules in the previous section and must always be read.

In the final report, list the project documents that materially influenced the implementation.

## 4. Instruction Priority

Apply instructions in the following order:

1. Direct instructions in the current task
2. More deeply nested `AGENTS.md` files that apply to the modified files
3. This root `AGENTS.md`
4. Required documents under `docs/agents/`
5. Relevant project documents under `docs/`
6. Existing code patterns and conventions
7. General industry conventions and the agent's learned preferences

A direct task instruction may override a repository rule only when the conflict is explicit.

Existing code patterns are descriptive evidence, not authoritative style rules.

When existing code conflicts with `docs/agents/python-style-guide.ko.md`, new or modified code must follow the style guide unless:

- preserving the existing pattern is necessary for compatibility
- a more specific project document explicitly requires the existing pattern
- the current task explicitly requires otherwise

General industry conventions may be used only when the repository documents do not address the relevant case.

When repository documents conflict:

- prefer a specific project rule over a general rule
- preserve existing externally observable behavior unless a change was explicitly requested
- prefer the option with lower maintenance and operational risk
- avoid expanding the requested scope unnecessarily
- document material conflicts and the selected interpretation in the final report

Do not silently resolve material conflicts.

## 5. Working Principles

### 5.1 Preserve Existing Behavior

Unless the task explicitly requests a behavior change:

- preserve externally observable behavior
- preserve public interfaces
- preserve return structures and data formats
- preserve configuration compatibility
- preserve localization keys and message semantics
- preserve logging and error-handling behavior where practical

A refactoring request is not permission to redesign unrelated behavior.

### 5.2 Control the Change Scope

Modify only the files required to complete the task safely and consistently.

Do not:

- perform unrelated cleanup
- rename unrelated symbols
- reorganize unrelated modules
- replace established patterns only because another pattern is preferred
- introduce dependencies without a concrete requirement
- broaden the task without a repository-supported reason

When a required change affects callers, tests, configuration, documentation, localization resources, or related modules, update all affected locations consistently.

Do not leave the repository in an intermediate state where an interface changed but its callers were not updated.

### 5.3 Inspect Before Editing

Before implementation:

1. Locate the primary implementation.
2. Search for all relevant callers and references.
3. Inspect related dependencies and data flows.
4. Inspect existing tests and validation configuration.
5. Read the required agent documents.
6. Read relevant project documentation.
7. Determine the expected behavior and affected surface area.
8. Plan the smallest coherent change.

Do not modify an interface before locating its call sites.

Do not infer the behavior of a module from its filename alone.

### 5.4 Prefer Evidence Over Assumption

Base decisions on:

- current task instructions
- repository code
- tests
- configuration
- required agent documents
- relevant project documentation
- version-control history when available and relevant

Do not invent requirements that are not supported by repository evidence.

When repository evidence is incomplete:

- preserve current behavior
- choose the least destructive implementation
- state the uncertainty in the final report

### 5.5 Keep the Implementation Proportionate

Prefer the simplest implementation that satisfies:

- the requested behavior
- existing compatibility requirements
- reasonable maintainability
- known operational constraints
- likely near-term changes supported by repository evidence

Do not introduce abstraction solely for theoretical future reuse.

Do not reduce necessary reliability merely to make the implementation shorter.

### 5.6 Treat Failure Paths as Part of the Design

When modifying code that interacts with external services, storage, configuration, user input, deployment, or background operations, inspect:

- invalid input
- duplicate execution
- partial success
- timeout behavior
- retry behavior
- logging
- recovery behavior
- idempotency
- operational visibility

Do not consider the implementation complete after validating only the success path.

## 6. Python Requirements

For all Python code, read and follow:

- `docs/agents/python-style-guide.ko.md`

The full document is authoritative.

The following summary does not replace reading the original document.

### 6.1 Style Authority and Precedence

The repository-specific style guide is authoritative for all Python code.

When the repository style guide differs from:

- common Python conventions
- PEP 8 recommendations
- Black defaults
- Ruff defaults
- isort defaults
- formatter or linter defaults
- framework conventions
- popular open-source practices
- existing non-compliant repository code
- the agent's learned preferences

follow the repository style guide.

Do not replace an explicitly documented repository convention with an industry-standard convention merely because the industry-standard convention is more common.

In particular:

- do not normalize code toward Black, Ruff, isort, PEP 8, or another tool's default output
- do not rewrite repository-specific spacing rules into conventional Python spacing
- do not rewrite repository-specific import grouping into conventional import grouping
- do not remove intentional blank lines required by the style guide
- do not add conventional blank lines that conflict with the style guide
- do not reinterpret documented requirements as optional recommendations
- do not prefer an existing local pattern when it conflicts with the required style guide
- do not describe a documented repository convention as incorrect solely because it differs from common practice

Industry standards may be used only when the repository style guide does not address the relevant case.

When the style guide is ambiguous:

1. Inspect its examples.
2. Inspect its stated design intent.
3. Inspect similar code that clearly complies with the guide.
4. Choose the interpretation that best preserves the guide's intent.
5. Report any material ambiguity in the final response.

Before completing the task, compare every changed Python block directly against the repository style guide rather than against general Python conventions.

### 6.2 Write in the Required Style from the Beginning

Write code in the required style from the beginning.

Do not write non-compliant code with the expectation that a formatter, linter, or later cleanup step will convert it into the required style.

Do not use the theoretical output of an unconfigured formatter as a style reference.

Do not assume that Black, Ruff, isort, or another common tool defines the intended repository style unless the repository explicitly configures and requires that tool for the relevant rule.

While implementing, manually preserve the documented conventions for:

- string and docstring quotes
- dictionary key access
- indentation
- blank-line placement
- logical-stage separation
- return spacing
- line breaking
- function-call formatting
- trailing commas
- naming
- type hints
- result objects
- exception handling
- architecture boundaries
- import grouping and ordering

At minimum:

- organize code by responsibility and reason for change
- use explicit and descriptive naming
- use type hints according to the documented policy
- prefer named arguments where appropriate
- follow the documented import grouping and ordering
- follow the documented blank-line and logical-stage rules
- distinguish recoverable result states from exceptional failures
- use structured result objects when their benefits justify the cost
- avoid unnecessary dynamic structures
- keep simple wrappers and direct execution flows compact
- preserve readability, maintainability, and consistency over generic conventions

Do not apply isolated style rules while ignoring the design intent described in the document.

Do not introduce formatting changes outside the task scope merely to make unrelated files conform to the style guide.

When modifying an existing block, make the changed block consistent with the required style without unnecessarily reformatting unrelated surrounding code.

### 6.3 Tooling Interpretation

A formatter or linter rule applies only when that tool is actually configured in the repository and is explicitly required for the current project or task.

When no formatter is configured or the current task does not require one:

- apply the style guide directly while writing code
- do not infer a formatter configuration from industry conventions
- do not simulate Black, Ruff, isort, or another tool's defaults
- do not treat generic formatter behavior as higher priority than the style guide

When an actually configured tool conflicts with the style guide:

1. Verify that the tool and conflicting rule are intentionally configured.
2. Check whether the style guide explicitly delegates that category to the tool.
3. Follow the more specific repository instruction.
4. Report unresolved conflicts before claiming full completion.

A tool's default behavior is not a repository rule unless the repository adopts that default explicitly.

## 7. Decision-Making Requirements

For design and implementation decisions, read and follow:

- `docs/agents/decision-making-principles.ko.md`

Evaluate decisions based on:

- future modification cost
- responsibility and reason for change
- development cost
- operational cost
- failure and recovery paths
- user and operator mistakes
- retry and duplicate-execution safety
- unnecessary abstraction
- implementation complexity
- automation value
- observability
- current project constraints
- known limitations
- migration and compatibility costs

A technically sophisticated solution is not automatically preferable.

Choose the solution that is most reasonable under the repository's actual requirements and constraints.

Do not optimize for theoretical completeness when a smaller and safer change satisfies the task.

## 8. Documentation Changes

Update documentation when the implementation changes:

- public or internal interfaces
- configuration
- environment variables
- data structures
- deployment behavior
- operational procedures
- architecture boundaries
- known limitations
- recovery procedures

Do not rewrite unrelated documentation.

When the implementation intentionally differs from an existing documented design, update the relevant document or explicitly report the discrepancy.

## 9. Validation

After making changes:

1. Review the final diff.
2. Confirm that every changed file is within the intended scope.
3. Search again for affected call sites and stale references.
4. Compare all changed Python code directly against `docs/agents/python-style-guide.ko.md`.
5. Verify that no general industry convention was applied in place of an explicit repository rule.
6. Run targeted tests for the changed behavior.
7. Run the repository's relevant type checker when available.
8. Run the repository's relevant test suite when available.
9. Run relevant linters only when they are already configured and useful for the task.
10. Verify that no unrelated generated files or artifacts were added.

A formatter is not required unless the current task explicitly requests it or the repository explicitly requires it.

Do not rely on formatter output as a substitute for writing code in the required style.

Do not run a formatter across unrelated files.

Do not run Black, Ruff formatting, isort, or another formatting tool merely because it is common in Python projects.

Use validation commands already defined by the repository, including commands found in:

- `pyproject.toml`
- workflow files
- task runners
- scripts
- Makefiles
- developer documentation

Do not invent replacement validation commands when the repository already defines them.

Do not modify code solely to satisfy an incorrectly configured tool without first verifying the repository's intended configuration.

When a validation command cannot run because of an environment, dependency, credential, network, permission, or external-service limitation:

- do not claim that it passed
- report the exact command
- report why it could not run
- report which alternative checks were completed
- identify any resulting uncertainty

## 10. Final Report

The final response must contain the following sections.

### Documents reviewed

Include:

- confirmation that `docs/agents/python-style-guide.ko.md` was read
- confirmation that `docs/agents/decision-making-principles.ko.md` was read
- relevant project documents read from `docs/`

Do not claim that a document was reviewed unless it was actually read.

### Changes

Include:

- a concise summary of the implementation
- the files or areas changed
- why each affected area required modification

### Behavior and compatibility

State:

- whether externally observable behavior changed
- whether public or internal interfaces changed
- whether call sites changed
- whether configuration changed
- whether data structures or stored data changed
- whether localization keys or message semantics changed

### Style compliance

Include:

- confirmation that changed Python code was compared directly against `docs/agents/python-style-guide.ko.md`
- any repository-specific conventions that differed from common Python practice
- confirmation that industry-standard defaults were not substituted for explicit repository rules
- any ambiguities or conflicts found in the style guide

### Validation

Include:

- manual style checks performed against `docs/agents/python-style-guide.ko.md`
- commands executed
- pass or fail status for each command
- manual or static checks performed
- checks that could not be executed and the reason

### Risks and follow-up

Include:

- remaining uncertainty
- known limitations
- compatibility risks
- manual checks still recommended

Do not claim full completion while hiding incomplete validation or unresolved risks.
