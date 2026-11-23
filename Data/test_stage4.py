from audit_test_utils import load_module, find_function, call_function, report

TEST_URL = "https://example.com"

def main():
    module = load_module("four_feature_extractor")
    fn = find_function(module, ['extract_stage_four_features', 'extract_stage4_features'])
    reference_data = None
    from reference_data_extractor import ReferenceDataExtractor
    reference_extractor = ReferenceDataExtractor(legitimate_label=0)
    reference_data = reference_extractor.extract(TEST_URL)
    result = call_function(fn, TEST_URL, reference_data)
    report("STAGE 4", result)

if __name__ == "__main__":
    main()
