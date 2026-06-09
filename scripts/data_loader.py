import pandas as pd
import os

# 获取项目根目录（假设 app.py 在根目录，且此模块被 app.py 调用）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'final_cleaned_travel_data.csv')
ORIGIN_DATA_PATH = os.path.join(BASE_DIR, 'data', 'Worldwide Travel Cities Dataset (Ratings and Climate).csv')

_cities_df = None
_origin_df = None

def load_cities_data(force_reload=False):
    global _cities_df
    if _cities_df is None or force_reload:
        _cities_df = pd.read_csv(DATA_PATH)
        # 去重
        _cities_df = _cities_df.drop_duplicates(subset=['city', 'latitude', 'longitude'], keep='first')
    return _cities_df

def load_origin_data(force_reload=False):
    global _origin_df
    if _origin_df is None or force_reload:
        _origin_df = pd.read_csv(ORIGIN_DATA_PATH)
    return _origin_df

def get_cities_list():
    df = load_cities_data()
    return df[['id', 'city', 'country', 'region', 'latitude', 'longitude',
               'budget_level', 'top_trait']].to_dict('records')