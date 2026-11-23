PHISHGUARD AI - STAGE 1 TO 8 TESTS

Extract all files into the same folder as your existing extractor modules.

Run individually:
    python test_stage1.py
    python test_stage2.py
    ...
    python test_stage8.py

These tests import your existing modules; they do not replace them.
Stage 4 uses ReferenceDataExtractor(legitimate_label=0), matching your current configuration. Verify label 0 means legitimate in the dataset documentation.
Stages 5-8 may make HTTP requests to https://example.com.

The tests print returned feature names, values and types. They check output structure only;
they do not establish that formulas match the original PhiUSIIL methodology.

If a function cannot be identified, the error lists functions found in that module. Update the preferred function-name list in that stage's test file.
Stage 3 includes the reported function name extract_stage_two_features.
