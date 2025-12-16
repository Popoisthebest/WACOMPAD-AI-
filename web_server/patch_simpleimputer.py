import joblib
import numpy as np
import types
import os

MODEL_FN = 'BernoulliNB_best.joblib'
OUT_FN = 'BernoulliNB_best_patched.joblib'

m = joblib.load(MODEL_FN)
print('Loaded model type:', type(m))

# helper to walk object graph
def iter_objs(obj, seen=None):
    if seen is None:
        seen = set()
    oid = id(obj)
    if oid in seen:
        return
    seen.add(oid)
    yield obj
    # container types
    if isinstance(obj, (list, tuple, set)):
        for v in obj:
            for x in iter_objs(v, seen):
                yield x
    if isinstance(obj, dict):
        for v in obj.values():
            for x in iter_objs(v, seen):
                yield x
    # object attributes
    for attr in dir(obj):
        if attr.startswith('__') or attr.startswith('_'):
            continue
        try:
            v = getattr(obj, attr)
        except Exception:
            continue
        if isinstance(v, (types.ModuleType, types.FunctionType, type)):
            continue
        for x in iter_objs(v, seen):
            yield x

from sklearn.impute import SimpleImputer

count = 0
for o in iter_objs(m):
    if isinstance(o, SimpleImputer):
        print('Found SimpleImputer:', repr(o))
        # if _fill_dtype missing, try to infer
        if not hasattr(o, '_fill_dtype'):
            dtype = None
            if hasattr(o, 'statistics_') and o.statistics_ is not None:
                try:
                    dtype = o.statistics_.dtype
                except Exception:
                    dtype = None
            if dtype is None:
                # fallback
                dtype = np.dtype('float64')
            setattr(o, '_fill_dtype', dtype)
            print('  set _fill_dtype ->', dtype)
            count += 1
        else:
            print('  already has _fill_dtype', o._fill_dtype)

print('Patched {} imputers'.format(count))
if count > 0:
    joblib.dump(m, OUT_FN)
    print('Wrote patched model to', OUT_FN)
else:
    print('No changes made')
