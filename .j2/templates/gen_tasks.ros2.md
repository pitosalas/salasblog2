Output ONLY the following line and nothing else, then stop and wait for the user's input:

`Feature ID [{{default_feature}}]: `

After the user responds with a feature ID, generate or update the task list for that feature following the instructions below.

You must follow these coding principles when generating tasks:

--- PRINCIPLES BEGIN ---
{{rules}}
--- PRINCIPLES END ---

This is a ROS2 project. When generating tasks, apply these ROS2-specific conventions:

**Package structure**
- `package.xml` — declare dependencies (`rclpy`, `rclcpp`, `std_msgs`, etc.)
- `setup.py` / `CMakeLists.txt` — register entry points and install targets
- `resource/<package_name>` — ament marker file (Python packages)
- `test/` — pytest-based unit and integration tests

**Node implementation**
- Subclass `rclpy.node.Node`; declare parameters in `__init__` with `self.declare_parameter`
- Use `rclpy.spin(node)` or `rclpy.spin_until_future_complete` in `main()`
- Publishers: `self.create_publisher(MsgType, 'topic', qos)`
- Subscribers: `self.create_subscription(MsgType, 'topic', callback, qos)`
- Timers: `self.create_timer(period_sec, callback)`
- Services: `self.create_service(SrvType, 'name', callback)`

**Build and test**
- Build: `colcon build --symlink-install`
- Source: `source install/setup.bash`
- Test: `colcon test` or `pytest` directly in the package directory
- Lint: `ament_flake8`, `ament_pep8`

**Launch files**
- Use Python launch format (`launch.py`)
- Import from `launch` and `launch_ros.actions`
- Pass parameters via `parameters=[{'key': value}]` on `Node` action

Read the feature description and generate or update the task list.

If a current task list is provided below (not marked "not yet available"), treat this as an update run:
- Preserve the ID and **Status** of every existing task exactly as it appears.
- Add any tasks needed to fully implement the feature that are not already present, assigning new IDs continuing from the highest existing ID.
- Do not remove tasks that are `in progress` or `done`.
- Do not change the description or status of existing tasks unless the feature description has changed in a way that makes a task obsolete.

If no current task list exists, generate one from scratch: assign IDs starting at T01, set all statuses to `not started`.

Each task should be:
- Concrete and actionable (a developer knows exactly what to do)
- Small enough to complete in one focused session
- Listed in a logical implementation order
- Consistent with the principles above (e.g. if principles require tests, include test tasks)

For each task include:
- A short ID (T01, T02, ...)
- A one-line title
- A brief description (2-4 sentences) of what to implement and any important details

Format each task as:

### T01 — Task Title
**Status**: not started
**Description**: ...

--- SPEC BEGIN ---
{{spec}}
--- SPEC END ---

--- FEATURES BEGIN ---
{{features}}
--- FEATURES END ---

--- CURRENT TASKS BEGIN ---
{{tasks}}
--- CURRENT TASKS END ---

Generate the task list and write it directly to `.j2/tasks/{{feature_id}}.md`. Do not display the task list in the console — just confirm the file was written with a single line like: "Written: .j2/tasks/{{feature_id}}.md (N tasks)"
