# app.py

import os
import json
import io
import base64
from datetime import datetime

import numpy as np
import pandas as pd
from flask import (
    Flask, render_template, request, jsonify,
    make_response
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pdfkit

# ── 비즈니스 로직은 model.py에 위임 ──
from model import (
    load_dataframes,
    predict_rul,
    status_grade,
    get_shap_importance,
    load_inspection_logs,
    history,
    performance,
    shap_data,
    schedule_events,
    get_all_unit_ids
)
app = Flask(__name__)

# ── 기본 디렉터리 설정 ──
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ── 센서 데이터 로드 ──
train_dfs, test_dfs = load_dataframes()

# -----------------------------------------------------------------------------  
# Route: Main Dashboard
@app.route('/monitoring')
def monitoring():
    fd = int(request.args.get('fd', 1))
    df_te = test_dfs.get(fd, pd.DataFrame())
    latest = df_te.groupby('unit').last().reset_index()
    return render_template(
        'monitoring.html',  # 템플릿도 monitoring.html 로 변경
        fd=fd,
        units=latest.to_dict(orient='records')
    )

# -----------------------------------------------------------------------------  
# Route: Compare view
@app.route('/compare')
def compare():
    fd = int(request.args.get('fd', 1))
    df_te = test_dfs.get(fd, pd.DataFrame())
    scatter = df_te[['unit','RUL']].assign(
        y_true=df_te['RUL'], y_pred=df_te['RUL']
    ).to_dict(orient='records')
    heatmap = df_te.groupby('unit')\
                   .apply(lambda g: np.mean(np.abs(g.RUL - g.RUL)))\
                   .reset_index().values.tolist()
    return render_template(
        'compare.html',
        fd=fd,
        scatter_data=json.dumps(scatter),
        heatmap_data=json.dumps(heatmap)
    )

# -----------------------------------------------------------------------------  
# Route: Sensor trends page (HTML)
@app.route('/sensors/view')
def sensors_view():
    fd   = int(request.args.get('fd', 1))
    unit = int(request.args.get('unit', 1))
    units = sorted(train_dfs.get(fd, pd.DataFrame())['unit'].unique().tolist())
    return render_template(
        'sensors.html',
        fd=fd,
        unit=unit,
        units=units
    )

# -----------------------------------------------------------------------------  
# Route: Sensor trends API (JSON)


@app.route('/sensors')
def sensors_api():
    fd   = int(request.args.get('fd', 1))
    unit = int(request.args.get('unit', 1))
    df_u = train_dfs.get(fd, pd.DataFrame())
    df_u = df_u[df_u.unit == unit]
    times  = df_u.time.tolist()
    values = {col: df_u[col].tolist() for col in df_u.columns[3:]}
    return jsonify({'time': times, 'values': values})

# -----------------------------------------------------------------------------  
# Route: Explain (SHAP)
@app.route('/explain/<int:unit>')
def explain(unit):
    data  = shap_data.get(unit, {})
    units = sorted(shap_data.keys())
    return render_template(
        'explain.html',
        unit=unit,
        units=units,
        feature_names=data.get('feature_names', []),
        shap_values=data.get('values', [])
    )

# -----------------------------------------------------------------------------  
# Route: Scheduler UI
@app.route('/schedule')
def schedule():
    # 🔧 unit ID 정수형으로 맞춰주기 (문자열 대비 필터 오작동 방지)
    for evt in schedule_events:
        if 'unit' in evt:
            evt['unit'] = int(evt['unit'])

    unit_ids = get_all_unit_ids()
    return render_template(
        'schedule.html',
        events=schedule_events,
        unit_ids=unit_ids
    )

@app.route('/schedule/create', methods=['POST'])
def create_event():
    event = request.get_json()
    schedule_events.append(event)
    json.dump(schedule_events, open(os.path.join(DATA_DIR,'schedule_events.json'),'w'))
    return jsonify(success=True), 201

# -----------------------------------------------------------------------------  
# Route: Performance dashboard
@app.route('/performance')
def performance_view():
    perf = performance.reset_index().to_dict(orient='records')
    return render_template(
        'performance.html',
        performance_data=perf,
        history=history
    )

# -----------------------------------------------------------------------------  
# Route: Grid dashboard
@app.route('/')
@app.route('/grid')
def grid_dashboard():
    # 1) 공통 파라미터
    fd   = int(request.args.get('fd', 1))
    unit = int(request.args.get('unit', 1))

    # 2) Performance widget 데이터
    perf = performance.reset_index().to_dict(orient='records')
    hist = history  # { 'metric1': [..], 'metric2': [..], ... }

    # 3) Schedule widget 데이터
    events = schedule_events  # list of {title, start, end}

    # 4) Compare widget 데이터
    df_te = test_dfs[fd]
    scatter = df_te[['unit','RUL']].assign(
        y_true=df_te['RUL'], y_pred=df_te['RUL']
    ).to_dict(orient='records')
    heatmap = df_te.groupby('unit').apply(
        lambda g: np.mean(np.abs(g.RUL - g.RUL))
    ).reset_index().values.tolist()

    # 5) Sensors widget 데이터
    df_u = train_dfs[fd]
    df_u = df_u[df_u.unit == unit]
    times  = df_u.time.tolist()
    values = {col: df_u[col].tolist() for col in df_u.columns[3:]}

    # 6) Explain (SHAP) widget 데이터
    #    partials/widget_explain.html 안에서 feature_names, shap_values 호출
    shap_info      = shap_data.get(unit, {})
    feature_names  = shap_info.get('feature_names', [])
    shap_values    = shap_info.get('values', [])

    # 7) PDF Report 버튼에도 쓰일 예측/등급
    rul           = predict_rul(fd, unit)
    status        = status_grade(rul)

    return render_template(
        'grid.html',
        # layout.html 네비에도 쓰인 공통
        fd=fd,
        unit=unit,

        # 각 위젯별 데이터
        performance_data=perf,
        history=hist,
        events=events,
        scatter_data=json.dumps(scatter),
        heatmap_data=json.dumps(heatmap),
        times=json.dumps(times),
        values=json.dumps(values),
        feature_names=json.dumps(feature_names),
        shap_values=json.dumps(shap_values),

        # PDF 리포트용
        predicted_rul=rul,
        status_grade=status,
    )

# -----------------------------------------------------------------------------  
# Route: PDF Report 다운로드/보기
@app.route('/report/<int:unit>')
def report(unit):
    fd    = int(request.args.get('fd', 1))
    rul   = predict_rul(fd, unit)
    grade = status_grade(rul)
    shap_list = get_shap_importance(unit)
    logs      = load_inspection_logs(unit)

    html = render_template(
        'report.html',
        unit_name       = f"FD{fd} Unit {unit}",
        created_at      = datetime.now().strftime("%Y-%m-%d %H:%M"),
        unit_id         = unit,
        status_grade    = grade,
        rul             = rul,
        shap_importance = shap_list,
        inspection_log  = logs
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )
    pdf  = pdfkit.from_string(html, False, configuration=config)
    resp = make_response(pdf)
    resp.headers['Content-Type']        = 'application/pdf'
    resp.headers['Content-Disposition'] = f'inline; filename=report_FD{fd}_U{unit}.pdf'
    return resp

if __name__ == '__main__':
    app.run(debug=True)
