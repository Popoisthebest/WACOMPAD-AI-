import pandas as pd
import numpy as np
import joblib
import glob
import os
import warnings


def _read_csv_flexible(path):
    # cp949 우선, 실패하면 utf-8로 시도
    try:
        return pd.read_csv(path, encoding='cp949')
    except Exception:
        return pd.read_csv(path, encoding='utf-8')


def preprocess_dataframe(df):
    # 컬럼 정리
    df.columns = df.columns.str.strip().str.replace('"', '')

    # 핵심 컬럼이 있는지 확인
    # 예상 컬럼: 시간, 버튼, X, Y, 압력_NORMAL
    # 안전하게 접근
    if '시간' not in df.columns:
        raise ValueError("CSV에 '시간' 컬럼이 없습니다")

    # 기본 계산
    data = df.copy()
    data['TIME_DIFF'] = data['시간'] - (data['시간'].iloc[0] + 1)
    total_time = data['TIME_DIFF'].iloc[-1]

    data['TIME_DIFF_DELTA'] = data['TIME_DIFF'].diff().replace(0, np.nan)
    data['DISTANCE'] = np.sqrt(data['X'].diff()**2 + data['Y'].diff()**2)
    data['SPEED'] = data['DISTANCE'] / data['TIME_DIFF_DELTA']

    data['ACCELERATION'] = data['SPEED'].diff() / data['TIME_DIFF_DELTA']
    data['JERK'] = data['ACCELERATION'].diff() / data['TIME_DIFF_DELTA']

    for col in ['SPEED', 'ACCELERATION', 'JERK']:
        data[col] = data[col].replace([np.inf, -np.inf], np.nan)
        data[col] = data[col].fillna(data[col].mean())

    mean_speed_on_paper = data[data['버튼'] == 1]['SPEED'].mean() if '버튼' in data.columns else None
    mean_speed_in_air = data[data['버튼'] == 0]['SPEED'].mean() if '버튼' in data.columns else None

    pressure_mean = data['압력_NORMAL'].mean() if '압력_NORMAL' in data.columns else None
    pressure_variance = data['압력_NORMAL'].var() if '압력_NORMAL' in data.columns else None

    def gmrt(subset, d=1):
        n = len(subset)
        if n <= d:
            return 0
        radii = np.sqrt(subset['X']**2 + subset['Y']**2)
        distances = np.abs(radii.diff(periods=d).dropna())
        return (1 / (n - d)) * distances.sum()

    gmrt_on_paper = gmrt(data[data['버튼'] == 1]) if '버튼' in data.columns else None
    gmrt_in_air = gmrt(data[data['버튼'] == 0]) if '버튼' in data.columns else None

    pendowns = int(data['버튼'].diff().eq(1).sum()) if '버튼' in data.columns else None

    result = {
        'air_time': int(data[data['버튼'] == 0]['TIME_DIFF'].count()) if '버튼' in data.columns else None,
        'gmrt_in_air': float(gmrt_in_air) if gmrt_in_air is not None else None,
        'gmrt_on_paper': float(gmrt_on_paper) if gmrt_on_paper is not None else None,
        'max_x_extension': float(data['X'].max()) if 'X' in data.columns else None,
        'max_y_extension': float(data['Y'].max()) if 'Y' in data.columns else None,
        'mean_acc_in_air': float(mean_speed_in_air) if mean_speed_in_air is not None else None,
        'mean_acc_on_paper': float(mean_speed_on_paper) if mean_speed_on_paper is not None else None,
        'mean_gmrt': float(((gmrt_on_paper or 0) + (gmrt_in_air or 0)) / 2),
        'mean_jerk_in_air': float(data[data['버튼'] == 0]['JERK'].mean()) if '버튼' in data.columns else None,
        'mean_jerk_on_paper': float(data[data['버튼'] == 1]['JERK'].mean()) if '버튼' in data.columns else None,
        'mean_speed_in_air': float(mean_speed_in_air) if mean_speed_in_air is not None else None,
        'mean_speed_on_paper': float(mean_speed_on_paper) if mean_speed_on_paper is not None else None,
        'num_of_pendown': pendowns,
        'paper_time': int(data[data['버튼'] == 1]['TIME_DIFF'].count()) if '버튼' in data.columns else None,
        'pressure_mean': float(pressure_mean) if pressure_mean is not None else None,
        'pressure_var': float(pressure_variance) if pressure_variance is not None else None,
        'total_time': float(total_time)
    }

    return result, data


def _numeric_suffix(fn):
    import re
    m = re.search(r"(\d+)(?!.*\d)", fn)
    return int(m.group(1)) if m else -1


def find_and_load_model():
    # Search for candidate joblib files in current and parent directories
    candidates = []
    cur = os.path.abspath('.')
    roots = []
    # walk up to filesystem root
    while True:
        roots.append(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    for r in roots:
        # 우선순위: BernoulliNB > displacement > 기타 모델
        pats = ['BernoulliNB*.joblib', 'displacement_prediction_model.joblib*', '*.joblib']
        for p in pats:
            found = glob.glob(os.path.join(r, p))
            for f in found:
                if f not in candidates:
                    candidates.append(f)

    # sort candidates by numeric suffix if possible
    candidates = sorted(candidates, key=_numeric_suffix, reverse=True)

    load_errors = []
    for cand in candidates:
        try:
            # 버전 호환성 경고 무시하고 로드
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = joblib.load(cand)
            return model, cand
        except Exception as e:
            load_errors.append((cand, str(e)))
            continue

    # if nothing loaded, return None and errors in logs
    if load_errors:
        for f, e in load_errors:
            warnings.warn(f"모델 로드 실패: {f} -> {e}")
    return None, None


def find_and_load_scaler():
    # Search upward for scaler files as well
    candidates = []
    cur = os.path.abspath('.')
    roots = []
    while True:
        roots.append(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    for r in roots:
        found = glob.glob(os.path.join(r, 'displacement_scaler.joblib*'))
        for f in found:
            if f not in candidates:
                candidates.append(f)

    for cand in candidates:
        try:
            # 버전 호환성 경고 무시하고 로드
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                scaler = joblib.load(cand)
            return scaler, cand
        except Exception as e:
            warnings.warn(f"스케일러 로드 실패: {cand} -> {e}")
            continue
    return None, None


def analyze(csv_path, debug=False):
    # 읽기
    df = _read_csv_flexible(csv_path)
    preproc_result, df_full = preprocess_dataframe(df)

    # 모델 로드 시도
    model, model_file = find_and_load_model()
    scaler, scaler_file = find_and_load_scaler()

    ml_result = None
    if model is None:
        warnings.warn('모델을 찾지 못함')
    else:
        # 실제 전처리 결과(preproc_result, df_full)를 모델 입력으로 매핑하려 시도
        n_features = getattr(model, 'n_features_in_', None)
        feature_names = None

        if hasattr(model, 'feature_names_in_'):
            try:
                feature_names = list(model.feature_names_in_)
            except Exception:
                feature_names = None

        # 파이프라인인 경우 내부 스텝에서 feature_names 추출 시도
        if feature_names is None and hasattr(model, 'named_steps'):
            for step in model.named_steps.values():
                if hasattr(step, 'feature_names_in_'):
                    try:
                        feature_names = list(step.feature_names_in_)
                        break
                    except Exception:
                        continue

        # 기본: n_features로 'col_0'.. 이름 생성
        if feature_names is None and n_features is not None:
            feature_names = [f'col_{i}' for i in range(n_features)]

        if n_features is None and feature_names is None:
            ml_result = {'warning': '모델에 필요한 feature 정보가 없어 예측을 수행하지 못함', 'model_file': model_file}
        else:
            # 단일-샘플(집계) 입력 벡터 생성: 가능한 경우 preproc_result의 값 매핑
            import re
            Xvec = []
            for fname in feature_names:
                val = None
                # 1) 정확한 키 매칭
                if isinstance(preproc_result, dict) and fname in preproc_result:
                    val = preproc_result[fname]
                # 2) 컬럼명이 모델이 기대하는 이름과 일치하면 df_full의 첫 행 사용
                elif fname in df_full.columns:
                    try:
                        val = df_full.iloc[0][fname]
                    except Exception:
                        val = 0
                else:
                    # 3) 숫자 접미사 제거해서 base 이름으로 매핑 (예: air_time1 -> air_time)
                    base = re.sub(r"\d+$", "", fname)
                    if isinstance(preproc_result, dict) and base in preproc_result:
                        val = preproc_result[base]
                    else:
                        # 4) 정규화된 키 비교(소문자, 언더스코어)
                        fname_norm = re.sub(r"\W+", "_", fname.lower())
                        mapped = None
                        if isinstance(preproc_result, dict):
                            for k in preproc_result.keys():
                                if re.sub(r"\W+", "_", k.lower()) == fname_norm or re.sub(r"\W+", "_", k.lower()) == re.sub(r"\W+", "_", base.lower()):
                                    mapped = preproc_result[k]
                                    break
                        if mapped is not None:
                            val = mapped
                        else:
                            # 기본값 0
                            val = 0

                # sanitize numeric
                try:
                    if val is None:
                        Xvec.append(0.0)
                    else:
                        Xvec.append(float(np.nan_to_num(val, nan=0.0, posinf=0.0, neginf=0.0)))
                except Exception:
                    Xvec.append(0.0)

            # Build a mapping dict and create DataFrame with feature names (some pipelines expect DataFrame)
            mapping = {fname: Xvec[i] for i, fname in enumerate(feature_names)}
            df_input = pd.DataFrame([mapping], columns=feature_names)

            # If model seems to be a pipeline (has named_steps), prefer passing DataFrame
            is_pipeline = hasattr(model, 'named_steps')

            # If external scaler exists and model is not a pipeline, attempt to apply scaler
            X_for_pred = None
            if scaler is not None and not is_pipeline:
                try:
                    scaler_n = getattr(scaler, 'n_features_in_', None)
                    arr = df_input.values
                    if scaler_n is None or scaler_n == arr.shape[1]:
                        X_for_pred = scaler.transform(arr)
                    else:
                        warnings.warn(f"스케일러 입력 차원({scaler_n})과 생성된 입력({arr.shape[1]})이 달라 스케일링을 건너뜁니다.")
                        X_for_pred = arr
                except Exception as e:
                    warnings.warn(f"스케일러 적용 중 오류: {e}")
                    X_for_pred = df_input.values
            else:
                # pass DataFrame if pipeline; otherwise values
                X_for_pred = df_input if is_pipeline else df_input.values

            # 예측 시도
            try:
                pred = model.predict(X_for_pred)
                pred_proba = None
                
                # predict_proba가 있으면 확률 추출
                if hasattr(model, 'predict_proba'):
                    try:
                        proba = model.predict_proba(X_for_pred)
                        # 이진분류(정상, 치매) 가정
                        if proba.shape[1] == 2:
                            dementia_prob = float(proba[0][1]) * 100  # 치매 확률(%)
                            normal_prob = float(proba[0][0]) * 100    # 정상 확률(%)
                            pred_proba = {
                                'dementia_probability': round(dementia_prob, 2),
                                'normal_probability': round(normal_prob, 2),
                                'diagnosis': '치매 의심' if dementia_prob >= 50 else '정상'
                            }
                    except Exception as e:
                        warnings.warn(f"predict_proba 추출 실패: {e}")
                
                try:
                    pred_list = pred.tolist()
                except Exception:
                    pred_list = [float(x) for x in np.array(pred).ravel()]
                
                ml_result = {
                    'prediction': pred_list,
                    'probability': pred_proba,
                    'model_file': model_file,
                    'scaler_file': scaler_file
                }

                # include debug info if requested
                if debug:
                    try:
                        ml_result['_debug'] = {
                            'raw_pred': pred.tolist() if hasattr(pred, 'tolist') else pred_list,
                            'predict_proba_raw': proba.tolist() if 'proba' in locals() and hasattr(proba, 'tolist') else None,
                            'input_vector': mapping,
                            'input_df': df_input.to_dict(orient='records') if isinstance(df_input, pd.DataFrame) else None
                        }
                    except Exception as e:
                        ml_result['_debug_error'] = str(e)
            except Exception as e:
                ml_result = {'error': str(e), 'model_file': model_file}

    # 결과 직렬화 안전성 확보 (NaN/Inf -> None, numpy types -> Python native)
    def _sanitize_value(v):
        if v is None:
            return None
        # numpy scalar
        if isinstance(v, (np.floating, float)):
            if np.isnan(v) or np.isinf(v):
                return None
            return float(v)
        if isinstance(v, (np.integer, int)):
            return int(v)
        if isinstance(v, (np.ndarray,)):
            return [_sanitize_value(x) for x in v.tolist()]
        if isinstance(v, (list, tuple)):
            return [_sanitize_value(x) for x in v]
        if isinstance(v, dict):
            return {str(k): _sanitize_value(val) for k, val in v.items()}
        # fallback for other types
        try:
            # handle pandas/numpy types
            if pd.isna(v):
                return None
        except Exception:
            pass
        return v

    sanitized = {
        'preprocessing': _sanitize_value(preproc_result),
        'ml': _sanitize_value(ml_result)
    }

    return sanitized
