import pandas as pd
import plotly.graph_objects as go


def create_globe_from_csv(csv_file="../data/final_cleaned_travel_data.csv", output_html="../templates/travel_globe.html"):
    # 读取数据
    df = pd.read_csv(csv_file)

    # 如果城市有重复（如 Krakow 出现两次），这里按城市名去重，保留第一个
    df = df.drop_duplicates(subset=["city", "latitude", "longitude"], keep="first")

    # 构建悬停文本：城市 | 国家 | 区域 · 预算 · 顶级特征
    hover_texts = []
    for _, row in df.iterrows():
        parts = []
        parts.append(f"<b>{row['city']}</b>")
        parts.append(f"{row['country']} ({row['region']})")
        parts.append(f"Budget: {row['budget_level']}")
        parts.append(f"Top trait: {row['top_trait']}")
        parts.append(row['short_description'][:120] + "…")  # 截断长描述
        hover_texts.append("<br>".join(parts))

    # 创建 3D 地球图
    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lon=df["longitude"],
        lat=df["latitude"],
        mode="markers",
        marker=dict(
            size=6,
            color="coral",
            line=dict(width=1, color="white"),
            opacity=0.9
        ),
        text=hover_texts,
        hoverinfo="text",
        name="Cities"
    ))

    # 设置为 3D 地球仪视角
    fig.update_geos(
        projection_type="orthographic",
        showland=True,
        landcolor="rgb(243, 243, 243)",
        coastlinecolor="rgb(120, 120, 120)",
        showocean=True,
        oceancolor="rgb(0, 128, 255)",
        showcountries=True,
        countrycolor="rgb(180, 180, 180)",
    )

    fig.update_layout(
        title="🌍 全球旅行城市 · 3D 地球仪",
        geo=dict(showframe=False, showcoastlines=True),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=700
    )

    fig.write_html(output_html)
    print(f"✅ 已生成 {output_html} ，包含 {len(df)} 个城市标记")
    return fig


# 直接运行
if __name__ == "__main__":
    create_globe_from_csv()