import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

MODEL_FN = 'BernoulliNB_best.joblib'
OUT_FN = 'BernoulliNB_best_patched.joblib'

m = joblib.load(MODEL_FN)
print('Loaded model type:', type(m))

patched = 0

def patch_estimator(est):
    global patched
    # direct SimpleImputer
    if isinstance(est, SimpleImputer):
        if not hasattr(est, '_fill_dtype'):
            dtype = None
            if hasattr(est, 'statistics_') and est.statistics_ is not None:
                try:
                    dtype = est.statistics_.dtype
                except Exception:
                    dtype = None
            if dtype is None:
                dtype = np.dtype('float64')
            setattr(est, '_fill_dtype', dtype)
            patched += 1
            print('Patched SimpleImputer with _fill_dtype ->', dtype)
    # Pipeline
    if isinstance(est, Pipeline):
        for name, step in est.named_steps.items():
            patch_estimator(step)
    # ColumnTransformer
    if isinstance(est, ColumnTransformer):
        for name, transformer, cols in est.transformers_:
            # transformer might be 'drop' or 'passthrough'
            if transformer == 'drop' or transformer == 'passthrough':
                continue
            # transformer can be a Pipeline or estimator
            patch_estimator(transformer)
    # Some transformers are themselves Pipelines or have .transformer
    # handle attributes that are estimators
    for attr in dir(est):
        if attr.startswith('_'):
            continue
        try:
            v = getattr(est, attr)
        except Exception:
            continue
        # avoid recursing into large structures
        if isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, (SimpleImputer, Pipeline, ColumnTransformer)):
                    patch_estimator(item)
        # check for nested estimator-like objects
        if isinstance(v, (SimpleImputer, Pipeline, ColumnTransformer)):
            patch_estimator(v)

# start patching
patch_estimator(m)
print('Total patched imputers:', patched)
if patched > 0:
    joblib.dump(m, OUT_FN)
    print('Wrote patched model to', OUT_FN)
else:
    print('No changes needed')
