# Coding Principles

These principles apply to all code written in this project.

## LLM
- Don't be verbose. No noise words. No flattery. Save tokens.

## Testing
- Each feature must have at least one test.
- Don't test every exception; let unusual situations crash.
- Test names describe expected behavior, not the method name (e.g. `test_returns_none_when_empty`)
- Use pytest fixtures sparingly — plain helper functions are clearer

## Python
- Version 3.10 or later
- Use uv for all packaging and virtual environments
- All code goes into a subfolder with the same name as the package
- Don't put on PyPi
- Prefer async/await over threading when there is a choice
- Use double quotes; single quotes only when specifically required
- No default parameters — make callers provide all values explicitly
- Don't code defensively; let exceptions bubble up
- Don't wrap code in try/except just to re-raise or log — let it crash
- YAGNI: only add what current requirements explicitly need

## File Headers
- Always include a shebang line
- First comment: module name and one-line description
- Second comment: `Author: Pito Salas and Claude Code`
- Third comment: `Open Source Under MIT license`

## Structure
- Files: no more than 500 lines
- Functions and methods: no more than 50 lines
- Functions: no more than 4 parameters
- No nested ifs more than 2 deep — redesign instead
- No if statements with more than 3 branches — redesign instead
- Avoid 1- and 2-line methods and simple wrappers
- Use classes to hold shared state; put each class in its own file
- Put data classes in the file where they are constructed
- Name files after the class defined in the file
- All imports at the top of the file; use absolute imports with module aliases

## Naming
- Obvious abbreviations are fine; keep identifiers under ~15 chars

## Comments
- Comment a function or method only if the name alone is not sufficient
- No more than 1-2 lines per comment

## Output
- No print statements except in CLI entry points
- No progress bars, spinners, or emoji in output

## Code Quality
- Don't assign a function result to a variable just to use it once — call directly

## ROS
- Use ROS2 and colcon builds for ROS2 programs
