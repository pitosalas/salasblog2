## Technology and Framework Requirements
    * You shall write code in Python
    * You should prefer async/await over threading when there is a choice
    * You must look for existing libraries instead of reinventing solutions
    * You will always have a shebang line
    * The first comment will give the name of the module and in one line say what it is
    * The second comment will say "Author: Pito Salas and Claude Code"
    * The third comment will say "Open Souce Under MIT license"

## Code Structure and Organization
    * You shall ensure functions and methods are no longer than 50 lines
    * You shall ensure no files have more than about 300 lines
    * You shall use classes and put them in separate files
    * You shall put data classes in the file where they are constructed
    * You shall name files after the class defined in the file
    * You shall give classes, methods and functions intention-revealing names but be willing to use obvious abbreviations or truncations to keep identifiers no more than ~ 15 chars
    * You shall avoid if/else statements that are nested more than 1 deep. If tempted to do so, look for another design
    * You shall not have if statements with more than 3 branches. If tempted to do so, look for another design
    * You shall avoid 2 line methods
    * You shall avoid 1 line functions and methods
    * You shall avoid simple wrappers
    * You should look for code duplication and make the code DRY if it makes sense
    * You shall avoid functions with more than 3 arguments
    * You shall use absolute imports with module aliases rather than relative imports
    * You shall put all imports at the top of the file

## Packaging
    * You shall use Python latest and standard package management (uv) 
    * You shall use the uv package manager at all times
    * You shall call the directory containing the source code with the same name as the project directory
    * You shall create the correct .toml file to ensure that the target program can be launched with uv run

## Code Quality and Best Practices
    * You shall write idiomatic Python
    * You should not go overboard on error checking
    * You shall never have bare except Exception: you shall be specific, and also put something in the alert box
    * You shall not assign the result of a function to a variable just to use that variable one time only; you shall use the function call directly
    * You shall put a comment with each method or function ONLY if the name of the function is not sufficient by itself
    * You should almost always use double quotes; you shall only use single quotes if there is a specific requirement to do so
    * You shall undertake multi-step implementation or refactoring in a way that after each step a running program is retained so that testing can be done to ensure progress is on the right track
    * You shall not provide default parameters to functions; make the caller provide all required values explicitly
    * You shall not code defensively; let exceptions bubble up rather than handling every possible error case
    * You shall follow YAGNI (You Aren't Gonna Need It): only add functions, methods, or classes that are explicitly required by current requirements; do not add code for anticipated future needs