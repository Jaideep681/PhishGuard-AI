import importlib
import inspect

def load_module(name):
    return importlib.import_module(name)

def find_function(module, preferred):
    for name in preferred:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    candidates = [
        obj for name, obj in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == module.__name__
    ]
    if len(candidates) == 1:
        return candidates[0]
    raise AttributeError(
        f"Cannot identify function in {module.__name__}. "
        f"Functions found: {[f.__name__ for f in candidates]}"
    )

def call_function(fn, url, reference_data=None):
    params = list(inspect.signature(fn).parameters.values())
    kwargs = {}
    for p in params:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        n = p.name.lower()
        if n in ("url", "website_url", "target_url", "input_url"):
            kwargs[p.name] = url
        elif n in ("reference_data", "ref_data"):
            kwargs[p.name] = reference_data
    if kwargs:
        return fn(**kwargs)
    if len(params) == 0:
        return fn()
    if len(params) == 1:
        return fn(url)
    return fn(url, reference_data)

def report(stage, result):
    if isinstance(result, tuple):
        result = result[0]
    if result is None:
        result = {}
    if not isinstance(result, dict):
        raise TypeError(f"Expected dict, received {type(result).__name__}: {result!r}")
    print("\\n" + "=" * 78)
    print(f"{stage} FEATURE TEST")
    print("=" * 78)
    if not result:
        print("No features returned. Check URL availability and extractor handling.")
    else:
        print(f"{'FEATURE':38} {'VALUE':25} {'TYPE'}")
        print("-" * 78)
        for key, value in result.items():
            print(f"{str(key):38.38} {str(value):25.25} {type(value).__name__}")
    print("-" * 78)
    print("Feature count:", len(result))
    print("Output type check: PASSED")
    print("Formula compatibility: NOT VERIFIED by this structural test.")
    return result
