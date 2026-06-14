# 项目配置说明

## 1. MySQL 数据库配置

配置文件路径：`mysql/config.ini`

```ini
[database]
host = localhost      # MySQL 服务器地址
user = root           # 用户名
password = 123456     # 密码（请修改为你的实际密码）
database = travel_db  # 数据库名称
port = 3306           # 端口号
```

### 修改数据库配置

1. 直接编辑 `mysql/config.ini` 文件
2. 或在首次启动时，程序会提示输入新的配置

### 导入数据

首次运行前，需导入城市数据到 MySQL：

```bash
python mysql/import_to_mysql.py
```

该脚本会：
- 创建 `travel_db` 数据库（如不存在）
- 创建 `cities` 表
- 从 `data/final_cleaned_travel_data.csv` 导入数据

---

## 2. 数据文件

| 文件 | 说明 |
|------|------|
| `data/Worldwide Travel Cities Dataset (Ratings and Climate).csv` | 原始数据集 |
| `data/final_cleaned_travel_data.csv` | 清洗后的数据（程序使用此文件） |

### 数据清洗

如需重新清洗数据：

```bash
python scripts/clean.py
```

---

## 3. Flask 应用配置

主文件：`app.py`

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `template_folder` | `templates` | HTML 模板目录 |
| `debug` | `True` | 开发模式，生产环境请改为 `False` |

### 启动应用

```bash
python app.py
```

默认访问地址：`http://127.0.0.1:5000`

---

## 4. 项目结构

```
travel-bigdata-screen/
├── app.py                 # Flask 主应用
├── .gitignore             # Git 忽略文件
├── CONFIG.md              # 本配置文件
├── data/                  # 数据文件目录
│   ├── Worldwide Travel Cities Dataset (Ratings and Climate).csv  # 原始数据
│   ├── cleaned_travel_data.csv       # 初次清洗数据
│   └── final_cleaned_travel_data.csv  # 最终清洗数据（程序使用）
├── mysql/                 # MySQL 配置与操作
│   ├── __init__.py
│   ├── config.ini         # 数据库配置文件
│   ├── db_checker.py      # 启动前数据库检验
│   ├── db_loader.py       # 数据库查询接口
│   └── import_to_mysql.py # 数据导入脚本
├── scripts/               # 数据处理脚本
│   ├── __init__.py
│   ├── clean.py           # 数据清洗
│   ├── city_utils.py      # 城市工具函数（球面距离计算）
│   ├── data_loader.py     # 数据加载
│   ├── globe.py           # 3D 地球仪生成
│   ├── recommend.py       # 城市推荐算法
│   └── route_planner.py   # 路线规划算法
└── templates/             # HTML 模板
    ├── dashboard.html     # 首页大屏
    ├── explore.html       # 城市探索
    ├── compare.html       # 城市对比
    ├── planner.html       # 旅行规划器
    ├── recommend.html     # 城市推荐
    ├── route_planner.html # 路线规划
    ├── city_detail.html   # 城市详情
    └── travel_globe.html  # 3D 地球仪可视化
```

---

## 5. 环境依赖

| 包名 | 版本 | 说明 |
|------|------|------|
| flask | 3.1.2 | Web 框架 |
| pandas | 2.2.3 | 数据处理 |
| pymysql | 1.1.1 | MySQL 连接 |
| plotly | 6.5.0 | 可视化图表 |
| pyecharts | 2.1.0 | 可视化图表 |
| numpy | 1.26.4 | 数值计算 |

安装命令：

```bash
pip install flask==3.1.2 pandas==2.2.3 pymysql==1.1.1 plotly==6.5.0 pyecharts==2.1.0 numpy==1.26.4
```

---

## 6. 常见问题

### 数据库连接失败

1. 确认 MySQL 服务已启动
2. 检查 `mysql/config.ini` 中的用户名/密码是否正确
3. 运行 `python mysql/import_to_mysql.py` 初始化数据库

### 页面无法访问

1. 确认 `templates/` 目录存在且包含对应 HTML 文件
2. 确认 Flask 应用已启动（终端显示 `Running on http://...`）