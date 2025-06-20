# build_shap.py
import os, joblib, pandas as pd, shap
import numpy as np

BASE     = os.getcwd()
DATA_DIR = os.path.join(BASE, 'data')
MODEL    = os.path.join(DATA_DIR, 'model.pkl')
TEST_CSV = os.path.join(DATA_DIR, 'test_FD001_cleaned.csv')
OUT_PKL  = os.path.join(DATA_DIR, 'shap_values.pkl')

# 1) 파일 체크
for p in (MODEL, TEST_CSV):
    if not os.path.exists(p):
        raise FileNotFoundError(p)

# 2) 원본 시계열 로드
df = pd.read_csv(TEST_CSV)

# 3) feature 컬럼 (time,RUL 제외)
drop_cols = ['unit','time','RUL']
feat_cols = [c for c in df.columns if c not in drop_cols]
print("▶ feat_cols:", feat_cols)

# 4) 각 unit마다 마지막 50개 row 추출
window = 50
units  = sorted(df['unit'].unique())
X_seq  = []
for u in units:
    sub = df[df.unit==u].sort_values('time')
    last50 = sub.tail(window)
    if len(last50) < window:
        # 50 미만이면 앞쪽을 0으로 패딩하거나 건너뛰세요
        pad = pd.DataFrame(0, index=range(window-len(last50)), columns=feat_cols)
        last50 = pd.concat([pad, last50[feat_cols]], ignore_index=True)
    else:
        last50 = last50[feat_cols].reset_index(drop=True)
    X_seq.append(last50.values)
X_seq = np.stack(X_seq)  # shape: (n_units, 50, 24)
n_units, seq_len, n_feats = X_seq.shape
print(f"▶ X_seq.shape = {X_seq.shape}")

# 5) Flatten for explainer
X_flat = X_seq.reshape(n_units, seq_len*n_feats)
bg_size = min(20, n_units)
background = X_flat[:bg_size]

# 6) 모델 로드
model = joblib.load(MODEL)

# 7) predict_fn: flat → seq → model → scalar
def predict_fn(x):
    """
    x: np.ndarray of shape (batch, 50*24) or DataFrame
    """
    arr = x.values if hasattr(x, 'values') else x
    seq = arr.reshape(-1, seq_len, n_feats)
    return model.predict(seq).flatten()

# 8) KernelExplainer 생성
explainer = shap.KernelExplainer(predict_fn, background)

# 9) SHAP 계산
print("▶ SHAP 계산 시작 …")
shap_out = explainer.shap_values(X_flat, nsamples=100)
shap_vals = shap_out[0] if isinstance(shap_out, (list,tuple)) else shap_out
print("▶ SHAP 계산 완료:", shap_vals.shape)

# 10) 저장할 dict 정리
shap_data = {}
for i, u in enumerate(units):
    shap_data[u] = {
        'feature_names': [f"{f}_t{t}" for t in range(seq_len) for f in feat_cols],
        'values'       : shap_vals[i].tolist()
    }

joblib.dump(shap_data, OUT_PKL)
print("✔ shap_values.pkl 저장 완료")
