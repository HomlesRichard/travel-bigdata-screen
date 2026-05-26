from flask import Flask, render_template
from pyecharts.charts import Radar
from jinja2 import Markup

app = Flask(__name__)

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
    return render_template("index.html", chart_html=chart.render_embed())

if __name__ == "__main__":
    app.run(debug=True)