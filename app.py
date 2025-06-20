# app.py

import os
import joblib
import json
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify

# ── oneDNN 로그 끄기 & TF INFO 로그 숨기기 ──
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL']  = '1'

app = Flask(__name__)

# ── 기본 디렉터리 설정 ──
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, 'data')
ORIGIN_DIR = os.path.join(BASE_DIR, 'origin')
os.makedirs(DATA_DIR, exist_ok=True)

# ── 공통 경로 패턴 ──
SCENARIOS = [1,2,3,4]
COLNAMES  = ['unit','time','op1','op2','op3'] + [f's{i}' for i in range(1,22)]

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

# ── 1) 모델·스케일러·기타 정적 파일 ──
model_path      = os.path.join(DATA_DIR, 'model.pkl')
scaler_path     = os.path.join(DATA_DIR, 'scaler.pkl')
history_path    = os.path.join(DATA_DIR, 'history.json')
perf_csv        = os.path.join(DATA_DIR, 'performance_metrics.csv')
val_csv         = os.path.join(DATA_DIR, 'val_results.csv')
test_csv        = os.path.join(DATA_DIR, 'test_results.csv')
shap_path       = os.path.join(DATA_DIR, 'shap_values.pkl')
schedule_path   = os.path.join(DATA_DIR, 'schedule_events.json')

model      = joblib.load(model_path) if os.path.exists(model_path) else None
scaler     = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
history    = json.load(open(history_path)) if os.path.exists(history_path) else {}
performance= pd.read_csv(perf_csv, index_col=0) if os.path.exists(perf_csv) else pd.DataFrame()
val_results= pd.read_csv(val_csv) if os.path.exists(val_csv) else pd.DataFrame()
test_results=pd.read_csv(test_csv) if os.path.exists(test_csv) else pd.DataFrame()
shap_data  = joblib.load(shap_path) if os.path.exists(shap_path) else {}
if os.path.exists(schedule_path):
    schedule_events = json.load(open(schedule_path))
else:
    schedule_events = []
    json.dump([], open(schedule_path,'w'))

# ── 2) 시나리오별 Sensor DataFrame 미리 로드 ──
train_dfs = {}
test_dfs  = {}
for fd in SCENARIOS:
    paths = make_cleaned_paths(fd)
    # Train
    if os.path.exists(paths['train_csv']):
        df_tr = pd.read_csv(paths['train_csv'])
    else:
        df_raw = pd.read_csv(paths['train_txt'], sep='\s+', header=None, names=COLNAMES)
        mc = df_raw.groupby('unit')['time'].max().to_dict()
        df_raw['RUL'] = df_raw.apply(lambda r: mc[r.unit] - r.time, axis=1)
        df_tr = df_raw
        df_tr.to_csv(paths['train_csv'], index=False)
    train_dfs[fd] = df_tr

    # Test
    if os.path.exists(paths['test_csv']):
        df_te = pd.read_csv(paths['test_csv'])
    else:
        df_raw = pd.read_csv(paths['test_txt'], sep='\s+', header=None, names=COLNAMES)
        rul_vals = pd.read_csv(paths['rul_txt'], header=None, names=['RUL'])['RUL'].values
        mapping  = dict(zip(sorted(df_raw.unit.unique()), rul_vals))
        df_raw['RUL'] = df_raw.unit.map(mapping)
        df_te = df_raw
        df_te.to_csv(paths['test_csv'], index=False)
    test_dfs[fd] = df_te

# -----------------------------------------------------------------------------  
# Route: Main Dashboard
@app.route('/')
def dashboard():
    # 기본 FD=1 사용
    fd = int(request.args.get('fd', 1))
    df_te = test_dfs.get(fd, pd.DataFrame())
    latest = df_te.groupby('unit').last().reset_index()
    return render_template('dashboard.html',
                           fd=fd,
                           units=latest.to_dict(orient='records'))

# -----------------------------------------------------------------------------  
# Route: Compare view
@app.route('/compare')
def compare():
    fd = int(request.args.get('fd', 1))
    df_te = test_dfs.get(fd, pd.DataFrame())
    scatter = df_te[['unit','RUL']].assign(y_true=df_te['RUL'], y_pred=df_te['RUL']).to_dict(orient='records')
    heatmap = df_te.groupby('unit').apply(lambda g: np.mean(np.abs(g.RUL - g.RUL))).reset_index().values.tolist()
    return render_template('compare.html',
                           fd=fd,
                           scatter_data=json.dumps(scatter),
                           heatmap_data=json.dumps(heatmap))
# Route: Sensor trends page (HTML)# Route: Sensor trends page (HTML)
@app.route('/sensors/view')
def sensors_view():
    fd   = int(request.args.get('fd', 1))
    unit = int(request.args.get('unit', 1))

    # units 리스트 생성: 해당 FD의 모든 unit 번호
    units = sorted(train_dfs.get(fd, pd.DataFrame())['unit'].unique().tolist())

    return render_template('sensors.html',
                           fd=fd,
                           unit=unit,
                           units=units)   # 이 줄 추가!


# 기존 /sensors는 JSON API로 그대로 유지
@app.route('/sensors')
def sensors_api():
    fd   = int(request.args.get('fd', 1))
    unit = int(request.args.get('unit', 1))
    df_u = train_dfs.get(fd, pd.DataFrame())
    df_u = df_u[df_u.unit==unit]
    times  = df_u.time.tolist()
    values = {col: df_u[col].tolist() for col in COLNAMES[3:]}
    return jsonify({'time': times, 'values': values})

# -----------------------------------------------------------------------------  
# Route: Explain (SHAP)
@app.route('/explain/<int:unit>')
def explain(unit):
    # shap_data 불러오기
    data = shap_data.get(unit, {})
    # 현재 shap_data에 들어 있는 모든 unit 번호 목록
    units = sorted(shap_data.keys())
    return render_template('explain.html',
                           unit=unit,
                           units=units,  # 여기!
                           feature_names=data.get('feature_names', []),
                           shap_values=data.get('values', []))
# -----------------------------------------------------------------------------  
# Route: Scheduler UI
@app.route('/schedule')
def schedule():
    # ✔ events는 Python list of dicts 그대로
    return render_template('schedule.html',
                           events=schedule_events)


@app.route('/schedule/create', methods=['POST'])
def create_event():
    event = request.get_json()
    schedule_events.append(event)
    json.dump(schedule_events, open(schedule_path,'w'))
    return jsonify(success=True), 201

# -----------------------------------------------------------------------------  
# Route: Performance dashboard
@app.route('/performance')
def performance_view():
    perf = performance.reset_index().to_dict(orient='records')
    return render_template('performance.html',
                           performance_data=perf,
                           history=history)

# -----------------------------------------------------------------------------  
if __name__ == '__main__':
    app.run(debug=True)
