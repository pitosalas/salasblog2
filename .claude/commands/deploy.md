* Do this when user types /deploy
* This command will deploy the currently checked out branch to try.io
* First determine what the currently checked out branch is, call it current-branch
* Prompt for permission to proceed: "About to deploy branch currenr-branch, ok"
* If yes, then Type this, and subsitute current-branch

fly deploy --build-arg GIT_BRANCH=current-branch --no-cache


