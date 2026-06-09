from flask import Flask, render_template, send_from_directory, request, jsonify
from pyecharts.charts import Radar
from pyecharts import options as opts
import pandas as pd
import os
from scripts.data_loader import get_cities_list
from scripts.route_planner import plan_routes

app = Flask(__name__, template_folder='templates')

def create_radar():
    # 假设这是你清洗后的全球旅游数据
    c = (
        Radar()
        .add_schema(schema=[
            {"name": "文化", "max": 5}, {"name": "美食", "max": 5},
            {"name": "夜生活", "max": 5}, {"name": "冒险", "max": 5}
        ])
        .add("米兰", [[5, 4, 4, 2]])
        .set_global_opts(title_opts=opts.TitleOpts(title="城市特质分析"))
    )
    return c

@app.route("/")
def index():
    chart = create_radar()
    # 关键点：使用 chart.render_embed() 获取 HTML 片段
    return render_template("dashboard.html", chart_html=chart.render_embed())

@app.route("/data/<filename>")
def serve_data(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return send_from_directory(data_dir, filename)

@app.route("/static/images/travel_images/<filename>")
def serve_images(filename):
    image_dir = os.path.join(os.path.dirname(__file__), 'travel_images')
    return send_from_directory(image_dir, filename)

@app.route("/explore")
def explore():
    df = pd.read_csv('data/final_cleaned_travel_data.csv')
    # 转换为字典列表供前端使用
    cities = df.to_dict(orient='records')
    return render_template("explore.html", cities=cities)


@app.route("/city/<city_id>")
def city_detail(city_id):
    # 读取清洗后的数据（没有描述）
    df_clean = pd.read_csv('data/final_cleaned_travel_data.csv')
    city_row = df_clean[df_clean['id'] == city_id]
    if city_row.empty:
        return "城市未找到", 404
    city = city_row.iloc[0].to_dict()

    # 从原始 CSV 中补充 short_description
    df_original = pd.read_csv('data/Worldwide Travel Cities Dataset (Ratings and Climate).csv')
    # 只取 id 和 short_description 两列，避免覆盖其他字段
    desc_df = df_original[['id', 'short_description']].drop_duplicates(subset='id')
    desc_dict = desc_df.set_index('id')['short_description'].to_dict()

    # 补充描述，如果没有则使用默认文本
    city['short_description'] = desc_dict.get(city_id, '暂无详细描述，欢迎探索这座魅力城市。')

    return render_template("city_detail.html", city=city)


@app.route("/compare")
def compare():
    # 从查询参数获取城市id列表，例如 ?ids=id1,id2,id3
    ids_param = request.args.get('ids', '')
    city_ids = [cid.strip() for cid in ids_param.split(',') if cid.strip()]
    # 限制最多5个城市
    if len(city_ids) > 5:
        city_ids = city_ids[:5]

    # 读取清洗后的数据
    df = pd.read_csv('data/final_cleaned_travel_data.csv')

    # 读取原始数据获取 short_description（可选）
    df_orig = pd.read_csv('data/Worldwide Travel Cities Dataset (Ratings and Climate).csv')
    desc_dict = df_orig.set_index('id')['short_description'].fillna('').to_dict()

    cities_data = []
    for cid in city_ids:
        row = df[df['id'] == cid]
        if not row.empty:
            city = row.iloc[0].to_dict()
            city['short_description'] = desc_dict.get(cid, '')
            # 计算综合评分（9项特质平均）
            trait_cols = ['culture', 'adventure', 'nature', 'beaches', 'nightlife', 'cuisine', 'wellness', 'urban',
                          'seclusion']
            scores = [float(city.get(col, 0)) for col in trait_cols]
            city['avg_score'] = round(sum(scores) / len(scores), 2) if scores else 0
            cities_data.append(city)

    # 准备所有城市列表供选择器使用（用于添加城市）
    all_cities = df[['id', 'city', 'country', 'region']].to_dict('records')

    return render_template("compare.html", cities=cities_data, all_cities=all_cities)


@app.route("/planner")
def planner():
    # 读取城市列表供下拉选择
    df = pd.read_csv('data/final_cleaned_travel_data.csv')
    # 读取原始描述
    df_orig = pd.read_csv('data/Worldwide Travel Cities Dataset (Ratings and Climate).csv')
    desc_dict = df_orig.set_index('id')['short_description'].fillna('').to_dict()

    cities_list = []
    for _, row in df.iterrows():
        cities_list.append({
            'id': row['id'],
            'city': row['city'],
            'country': row['country'],
            'budget_level': row['budget_level'],
            'traits': {
                'culture': row.get('culture', 0),
                'adventure': row.get('adventure', 0),
                'nature': row.get('nature', 0),
                'beaches': row.get('beaches', 0),
                'nightlife': row.get('nightlife', 0),
                'cuisine': row.get('cuisine', 0)
            }
        })

    return render_template("planner.html", cities=cities_list)

@app.route('/api/plan_route', methods=['POST'])
def api_plan_route():
    data = request.get_json()
    start_id = data.get('start_id')
    end_id = data.get('end_id')
    total_cities = int(data.get('total_cities', 3))
    if not start_id or not end_id or start_id == end_id:
        return jsonify({'error': '请选择不同的起点和终点'}), 400
    routes = plan_routes(start_id, end_id, total_cities, num_routes=5)
    if not routes:
        return jsonify({'error': '无法生成足够路线'}), 400
    return jsonify({'routes': routes})

@app.route('/route_planner')
def route_planner():
    cities = get_cities_list()
    return render_template('route_planner.html', cities=cities)


if __name__ == "__main__":
    app.run(debug=True)