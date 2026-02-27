You are helping a developer plan a ROS2 software project.

Keep these coding principles in mind when generating features — they will constrain how each feature is implemented:

--- PRINCIPLES BEGIN ---
{{rules}}
--- PRINCIPLES END ---

Read the following project specification and generate or update the feature list.

This is a ROS2 project. When generating features, consider the standard building blocks of ROS2 packages:
- **Nodes**: rclpy or rclcpp nodes with publishers, subscribers, and timers
- **Topics**: message types, QoS profiles, topic naming conventions
- **Services**: service definitions, synchronous request/response patterns
- **Actions**: long-running tasks with feedback (rclpy action server/client)
- **Launch files**: `launch.py` files using `launch_ros`, node composition, parameter passing
- **Parameters**: node parameters declared in `__init__`, overridable via YAML or launch
- **Package structure**: `package.xml`, `setup.py` or `CMakeLists.txt`, `resource/`, `test/`
- **Testing**: `pytest` with `launch_testing` or unit tests via `unittest`
- **Build**: `colcon build`, `source install/setup.bash`

If a current feature list is provided below (not marked "not yet available"), treat this as an update run:
- For each existing feature, check whether its name, description, and priority still accurately reflect the current spec. If not, update them to match.
- Preserve the status and test fields of every existing feature exactly as they are — never reset progress.
- Add any features clearly supported by the spec that are not already present, assigning them new IDs continuing from the highest existing ID.
- Remove features no longer supported by the spec only if their status is `not started`.

If no current feature list exists, generate one from scratch: assign IDs starting at F01, set all status fields to their default values.

For each feature:
- Assign a short ID (F01, F02, ...)
- Give it a concise name
- Write a 1-2 sentence description
- Assign a priority: High, Medium, or Low
- Include status fields

Begin the output with this header exactly:

```
Status values:
- **Status**: `not started` / `in progress` / `done`
- **Tests written**: `no` / `yes`
- **Tests passing**: `n/a` / `no` / `yes`
```

Then list each feature separated by `---`. Format each feature as:

## F01 — Feature Name
**Priority**: High
**Status**: not started | Tests written: no | Tests passing: n/a
**Description**: ...

Order features from most to least important. Focus on concrete, buildable features.
Do not include features that are not clearly supported by the spec.

--- SPEC BEGIN ---
{{spec}}
--- SPEC END ---

--- CURRENT FEATURES BEGIN ---
{{features}}
--- CURRENT FEATURES END ---
