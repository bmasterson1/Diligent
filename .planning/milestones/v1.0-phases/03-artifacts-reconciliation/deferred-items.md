# Deferred Items - Phase 03

## Pre-existing Test Failure

- **File:** `diligent/tests/test_artifact_cmd.py::TestArtifactList::test_list_shows_all_artifacts_with_status`
- **Discovered during:** 03-03 execution
- **Issue:** Test expects exit_code 0 but gets exit_code 2. Pre-existing from Plan 02 (artifact register/list/refresh). Not caused by Plan 03 changes.
- **Status:** Out of scope for Plan 03. Should be addressed in Plan 02 follow-up or Plan 04.
