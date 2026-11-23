from audit_test_utils import load_module, find_function, call_function, report

TEST_URL = "https://example.com"

def main():
    module = load_module("five_feature_extractor")
    fn = find_function(module, ['extract_webpage_features', 'extract_stage_five_features', 'extract_stage5_features'])
    reference_data = None
    result = call_function(fn, TEST_URL, reference_data)
    report("STAGE 5", result)

if __name__ == "__main__":
    main()
