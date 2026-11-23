from audit_test_utils import load_module, find_function, call_function, report

TEST_URL = "https://example.com"

def main():
    module = load_module("three_feature_extractor")
    fn = find_function(module, ['extract_stage_three_features', 'extract_stage_two_features', 'extract_stage3_features', 'extract_features'])
    reference_data = None
    result = call_function(fn, TEST_URL, reference_data)
    report("STAGE 3", result)

if __name__ == "__main__":
    main()
