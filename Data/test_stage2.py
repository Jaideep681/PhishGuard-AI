from audit_test_utils import load_module, find_function, call_function, report
TEST_URL = "https://example.com"

def main():
    module = load_module("two_feature_extractor")
    fn = find_function(module, ['extract_stage_two_features', 'extract_stage2_features', 'extract_url_features', 'extract_features'])
    reference_data = None
    result = call_function(fn, TEST_URL, reference_data)
    report("STAGE 2", result)

if __name__ == "__main__":
    main()
