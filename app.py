from flask import Flask, render_template, send_from_directory
from pyecharts.charts import Radar
from pyecharts import options as opts
import pandas as pd
import os

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
    df = pd.read_csv('data/final_cleaned_travel_data.csv')
    # 根据 id 查找城市
    city_row = df[df['id'] == city_id]
    if city_row.empty:
        return "城市未找到", 404
    city = city_row.iloc[0].to_dict()
    return render_template("city_detail.html", city=city)

if __name__ == "__main__":
    app.run(debug=True)