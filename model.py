# model.py

import os
import joblib
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ── 1) 경로 설정 ──
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, 'data')
ORIGIN_DIR = os.path.join(BASE_DIR, 'origin')

SCENARIOS = [1, 2, 3, 4]
COLNAMES  = ['unit', 'time', 'op1', 'op2', 'op3'] + [f's{i}' for i in range(1, 22)]

def make_cleaned_paths(fd):
    """FD 번호에 맞는 cleaned CSV 경로와 origin txt 경로 딕셔너리 반환"""
    suf = f'FD00{fd}'
    return {
        'train_csv': os.path.join(DATA_DIR, f'train_{suf}_cleaned.csv'),
        'test_csv' : os.path.join(DATA_DIR, f'test_{suf}_cleaned.csv'),
        'train_txt': os.path.join(ORIGIN_DIR, f'train_{suf}.txt'),
        'test_txt' : os.path.join(ORIGIN_DIR, f'test_{suf}.txt'),
        'rul_txt'  : os.path.join(ORIGIN_DIR, f'RUL_{suf}.txt'),
    }

# ── 2) DataFrame 로드/캐시 ──
_train_dfs = {}
_test_dfs  = {}

def load_dataframes():
    """
    SCENARIOS별로 train_dfs, test_dfs를 로드하거나 생성하여
    두 딕셔너리를 반환합니다.
    """
    global _train_dfs, _test_dfs
    if _train_dfs and _test_dfs:
        return _train_dfs, _test_dfs

    for fd in SCENARIOS:
        paths = make_cleaned_paths(fd)

        # Train
        if os.path.exists(paths['train_csv']):
            df_tr = pd.read_csv(paths['train_csv'])
        else:
            df = pd.read_csv(paths['train_txt'], sep='\s+', header=None, names=COLNAMES)
            max_time = df.groupby('unit')['time'].max().to_dict()
            df['RUL'] = df.apply(lambda r: max_time[r.unit] - r.time, axis=1)
            df.to_csv(paths['train_csv'], index=False)
            df_tr = df
        _train_dfs[fd] = df_tr

        # Test
        if os.path.exists(paths['test_csv']):
            df_te = pd.read_csv(paths['test_csv'])
        else:
            df = pd.read_csv(paths['test_txt'], sep='\s+', header=None, names=COLNAMES)
            rul_vals = pd.read_csv(paths['rul_txt'], header=None, names=['RUL'])['RUL'].values
            mapping  = dict(zip(sorted(df.unit.unique()), rul_vals))
            df['RUL'] = df.unit.map(mapping)
            df.to_csv(paths['test_csv'], index=False)
            df_te = df
        _test_dfs[fd] = df_te

    return _train_dfs, _test_dfs

# ── 3) 모델·스케일러·SHAP·스케쥴·기타 정적 파일 로드 ──
_model_path      = os.path.join(DATA_DIR, 'model.pkl')
_scaler_path     = os.path.join(DATA_DIR, 'scaler.pkl')
_history_path    = os.path.join(DATA_DIR, 'history.json')
_perf_csv        = os.path.join(DATA_DIR, 'performance_metrics.csv')
_val_csv         = os.path.join(DATA_DIR, 'val_results.csv')
_test_results_csv= os.path.join(DATA_DIR, 'test_results.csv')
_shap_path       = os.path.join(DATA_DIR, 'shap_values.pkl')
_schedule_path   = os.path.join(DATA_DIR, 'schedule_events.json')

model       = joblib.load(_model_path) if os.path.exists(_model_path) else None
scaler      = joblib.load(_scaler_path) if os.path.exists(_scaler_path) else None
history     = json.load(open(_history_path)) if os.path.exists(_history_path) else {}
performance = pd.read_csv(_perf_csv, index_col=0) if os.path.exists(_perf_csv) else pd.DataFrame()
val_results = pd.read_csv(_val_csv) if os.path.exists(_val_csv) else pd.DataFrame()
test_results= pd.read_csv(_test_results_csv) if os.path.exists(_test_results_csv) else pd.DataFrame()
shap_data   = joblib.load(_shap_path) if os.path.exists(_shap_path) else {}

if os.path.exists(_schedule_path):
    schedule_events = json.load(open(_schedule_path))
else:
    schedule_events = []
    json.dump([], open(_schedule_path, 'w'))

# ── 4) RUL 예측 ──
def predict_rul(fd, unit):
    """
    FD와 unit을 받아
      - 그 unit의 마지막 50 타임스텝 센서 데이터(24차원)를 잘라
      - (1, 50, 24) 형태로 모델에 넣어 예측 RUL 반환
    """
    # 1) 시나리오별 DataFrame 로드
    train_dfs, test_dfs = load_dataframes()

    # 2) 해당 FD의 test 데이터에서 unit별 마지막 50행 추출
    df_u = test_dfs[fd]
    df_u = df_u[df_u.unit == unit]

    # 만약 타임스텝이 50개 미만이면, 앞부분을 0으로 패딩하거나
    # 마지막 50개만 자르기로 합시다.
    N = 50
    feats = COLNAMES[2:]  # op1–op3 + s1–s21 (총 24개)
    arr = df_u[feats].values  # shape: (time_steps, 24)

    if arr.shape[0] < N:
        # 앞에 (N - T)행 0으로 패딩
        pad = np.zeros((N - arr.shape[0], arr.shape[1]), dtype=arr.dtype)
        arr = np.vstack([pad, arr])
    else:
        arr = arr[-N:]  # 마지막 N행

    # 3) 스케일링: scaler는 (n_samples, 24) 입력을 기대하므로
    #    arr을 (50,24)로 스케일하고 다시 (1,50,24)로 reshape
    flat = scaler.transform(arr)           # shape: (50,24)
    X = flat.reshape((1, N, arr.shape[1])) # shape: (1,50,24)

    # 4) 모델 예측
    pred = model.predict(X)                # shape: (1, )
    return float(pred.flatten()[0])


# ── 5) 상태 등급 산정 ──
def status_grade(rul_days):
    """
    RUL(일)을 받아 등급 문자열을 반환합니다.
    """
    if rul_days is None:
        return "알 수 없음"
    if rul_days > 50:
        return "양호"
    if rul_days > 20:
        return "주의"
    return "위험"

# ── 6) SHAP 중요도 ──
def get_shap_importance(unit, top_n=10):
    """
    unit별 SHAP 값을 불러와 feature별 중요도로 리스트 반환합니다.
    """
    data = shap_data.get(unit, {})
    vals = data.get('values', [])
    fns  = data.get('feature_names', [])
    return [
        {'name': fn, 'value': float(v)}
        for fn, v in zip(fns, vals[:top_n])
    ]

# ── 7) 점검 이력 로드 (CSV 예시) ──
def load_inspection_logs(unit, filename='inspection_log.csv'):
    """
    data/inspection_log.csv 파일에서 unit별 로그만 필터링하여 반환합니다.
    컬럼명은 date, desc, staff 로 매핑되어 있어야 합니다.
    """
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    df = df[df.unit == unit]
    return df[['date', 'desc', 'staff']].to_dict(orient='records')

def get_all_unit_ids():
    """
    현재 시스템 전체에서 등장한 모든 unit ID를 집계하여 반환합니다.
    """
    unit_set = set()

    # 1. train 데이터셋
    for df in _train_dfs.values():
        unit_set.update(df['unit'].unique())

    # 2. test 데이터셋
    for df in _test_dfs.values():
        unit_set.update(df['unit'].unique())

    # 3. SHAP 결과
    unit_set.update(shap_data.keys())

    # 4. 일정 정보
    for evt in schedule_events:
        if 'unit' in evt:
            unit_set.add(evt['unit'])

    return sorted(unit_set)
#------------------------클러스터연동----

_cluster_path = os.path.join(DATA_DIR, 'cluster_labels.csv')
_cluster_df = pd.read_csv(_cluster_path) if os.path.exists(_cluster_path) else pd.DataFrame()

def get_cluster_label(unit_id, fd):
    row = _cluster_df.query("unit == @unit_id and model == 'FD00{}'".format(fd))
    return int(row['cluster'].iloc[0]) if not row.empty else None
def get_cluster_map(fd):
    df = _cluster_df.query("model == 'FD00{}'".format(fd))
    clusters = df['cluster'].unique().tolist()  # 클러스터 값을 리스트 형태로 반환
    return clusters

def get_units_by_cluster(fd, cluster_id):
    model_id = f"FD00{fd}"
    df = _cluster_df.query("`model` == @model_id and `cluster` == @cluster_id")
    return df['unit'].tolist()
