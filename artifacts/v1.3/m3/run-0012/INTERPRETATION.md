# Preserved failed harness attempt

The full pytest run recorded 430 passed tests and two setup/teardown errors for one oversized raw-store case. Automatic parameter naming embedded a roughly65 KB byte-string rendering into PYTEST_CURRENT_TEST, exceeding Windows'32767-character environment-variable limit before the test body ran. This is a harness error, not evidence that the product accepted the malformed store or that a model failed.

Explicit short parameter IDs were added to all six raw-store cases; run-0013 reran the complete suite and passed431 tests. No malformed input values or intended acceptance conditions were changed. This run remains failed; the JUnit file is preserved rather than rewritten. Parameter naming was the only test-source repair.
