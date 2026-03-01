# General
* You shall not write any code for the tool withot a corresponding task
* You shall not write any task description without a corresponding feature
* You shall not write a feature which is not consistent with the spec
* You shall not close off a feature unless there is a complete suite of tests and they run

# features
* new features get a feature id like f01-create-process-folder
* each feature has a markdown file in the process/features/done or /notdonw folder
* inside features folder there is a file called template.md which shows the format

# tasks
* Before any design is done or code is written, a set of tasks must be developed
* All the tasks for a feature can be found in a file in the tasks/done or tasks/notdone folders
* inside tasks folder there is a file called template.md which shows the format
* Every feature must include a task for writing tests; this task must always be proposed along with the other tasks
* When the last task for a feature is marked done, move the task file from tasks/notdone/ to tasks/done/
* Then update the feature file: set Done to yes, and Tests Written and Test Passing to yes if applicable
* Then move the feature file from features/notdone/ to features/done/

# github
* Whenever asked you will create a new commit with a good message
* Whenever asked you will push to github

# bugs and testing
* Whenever a bug is discovered, and fixed, write a new test for it
* Whenever we see a regression bug, and fix it, write a new test for it.




