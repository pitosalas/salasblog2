# Feature description for feature F35
## F35 — Fix Admin Sync Button After Token Rotation
**Priority**: Medium
**Date Created:** 2026-04-15
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: After updating GIT_TOKEN via `fly secrets set`, the running container still has the old token baked into the git remote URL. The "Sync to GitHub Now" admin button fails with 403 until the app is restarted/redeployed. The fix should either: (a) read GIT_TOKEN from the environment at sync time and reconstruct the remote URL dynamically, rather than relying on whatever URL was set at container startup, or (b) document that `fly deploy` is required after rotating the token.

## How to Demo
**Setup**: A running deployment with `GIT_TOKEN` rotated via `fly secrets set` without a redeploy.

**Steps**:
1. Rotate `GIT_TOKEN` via `fly secrets set GIT_TOKEN=<new token>` without redeploying.
2. Click "Sync to GitHub Now" in the admin panel.
3. Confirm the sync succeeds using the new token, with no 403 error.

**Expected output**: Git sync succeeds immediately after a token rotation, with no redeploy required.
