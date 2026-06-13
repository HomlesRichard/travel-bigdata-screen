from flask import Flask, render_template, send_from_directory, request, jsonify
from pyecharts.charts import Radar
from pyecharts import options as opts
import os
import sys

# 启动前检验数据库连接
from mysql.db_checker import verify_and_setup_database
success, db_config = verify_and_setup_database()

if not success:
    print("\n数据库配置失败，应用无法启动。")
    print("请检查 MySQL 是否已启动，并确保配置正确。")
    print("您可以:")
    print("  1. 修改 mysql/config.ini 文件中的数据库配置")
    print("  2. 运行 python mysql/import_to_mysql.py 导入数据")
    sys.exit(1)

# 导入数据库操作模块
from mysql.db_loader import get_cities_list, get_city_by_id, get_all_cities, get_cities_by_ids
from scripts.route_planner import *

app = Flask(__name__, template_folder='templates')

def create_radar():
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
    cities = get_all_cities()
    return render_template("explore.html", cities=cities)

@app.route("/city/<city_id>")
def city_detail(city_id):
    city = get_city_by_id(city_id)
    if not city:
        return "城市未找到", 404
    return render_template("city_detail.html", city=city)

@app.route("/compare")
def compare():
    ids_param = request.args.get('ids', '')
    city_ids = [cid.strip() for cid in ids_param.split(',') if cid.strip()]
    if len(city_ids) > 5:
        city_ids = city_ids[:5]
    
    cities_data = []
    for cid in city_ids:
        city = get_city_by_id(cid)
        if city:
            trait_cols = ['culture', 'adventure', 'nature', 'beaches', 'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion']
            scores = [float(city.get(col, 0)) for col in trait_cols]
            city['avg_score'] = round(sum(scores) / len(scores), 2) if scores else 0
            cities_data.append(city)
    
    all_cities = get_cities_list()
    return render_template("compare.html", cities=cities_data, all_cities=all_cities)

@app.route("/planner")
def planner():
    cities = get_all_cities()
    cities_list = []
    for city in cities:
        cities_list.append({
            'id': city['id'],
            'city': city['city'],
            'country': city['country'],
            'budget_level': city['budget_level'],
            'traits': {
                'culture': city.get('culture', 0),
                'adventure': city.get('adventure', 0),
                'nature': city.get('nature', 0),
                'beaches': city.get('beaches', 0),
                'nightlife': city.get('nightlife', 0),
                'cuisine': city.get('cuisine', 0)
            }
        })
    return render_template("planner.html", cities=cities_list)

@app.route('/api/plan_route', methods=['POST'])
def api_plan_route():
    data = request.get_json()
    start_id = data.get('start_id')
    end_id = data.get('end_id')
    total_cities = data.get('total_cities', 4)

    if not start_id or not end_id or start_id == end_id:
        return jsonify({'error': '请选择不同的起点和终点'}), 400

    routes = plan_routes(start_id, end_id, total_cities=total_cities)
    if not routes:
        return jsonify({'error': '无法生成任何路线'}), 400

    for route in routes:
        if len(route['city_ids']) > total_cities:
            truncated_ids = route['city_ids'][:total_cities]
            truncated_dist = sum(
                get_distance(truncated_ids[i], truncated_ids[i + 1]) for i in range(len(truncated_ids) - 1))
            route['city_ids'] = truncated_ids
            route['cities'] = route['cities'][:total_cities]
            route['total_distance_km'] = round(truncated_dist, 1)

    return jsonify({'routes': routes})

@app.route('/route_planner')
def route_planner():
    cities = get_cities_list()
    return render_template('route_planner.html', cities=cities)

if __name__ == "__main__":
    app.run(debug=True)