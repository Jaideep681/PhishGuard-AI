from audit_test_utils import load_module, find_function, call_function, report

TEST_URL = "https://example.com"

def main():
    module = load_module("six_feature_extractor")
    fn = find_function(module, ['extract_stage6_features', 'extract_stage_six_features'])
    reference_data = None
    result = call_function(fn, TEST_URL, reference_data)
    report("STAGE 6", result)

if __name__ == "__main__":
    main()
