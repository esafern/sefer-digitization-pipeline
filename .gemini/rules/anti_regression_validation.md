---
description: Enforce snapshot testing for validated states and prevent releasing pipeline passes that cause regressions against known-good data.
---
# Anti-Regression and Snapshot Validation

Always guard against regression by capturing known-good, validated states (such as the verified first sentences or exact text bounds of previously processed items). Before finalizing any pipeline update, run an automated pass to verify that no previously validated outputs have been broken or altered. Never commit or release a change without confirming zero regressions against the captured ground truth.
