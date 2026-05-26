import pandas as pd
import numpy as np
import json

# 1. 基础清理
df = pd.read_csv('../data/Worldwide Travel Cities Dataset (Ratings and Climate).csv')
df.drop_duplicates(inplace=True)
df.columns = df.columns.str.strip()

# 2. 坐标与评分过滤
df = df[(df['latitude'].between(-90, 90)) & (df['longitude'].between(-180, 180))]

# 3. 映射预算等级为数值
budget_map = {'Budget': 1, 'Mid-range': 2, 'Luxury': 3}
df['budget_score'] = df['budget_level'].map(budget_map)

# 4. 统计每个城市的"性格标签"
rating_cols = ['culture', 'adventure', 'nature', 'beaches', 'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion']

def get_top_trait(row):
    max_val = row[rating_cols].max()
    max_cols = [col for col in rating_cols if row[col] == max_val]
    return np.random.choice(max_cols)

df['top_trait'] = df.apply(get_top_trait, axis=1)

# 5. 预处理 ideal_durations 为简单的字符串格式，避免复杂的 JSON 引用问题
def process_durations(dur):
    if pd.isna(dur):
        return ''
    try:
        # 尝试解析 JSON 数组
        arr = json.loads(dur)
        # 用逗号连接成字符串
        return ','.join(arr)
    except:
        # 如果解析失败，直接返回原始字符串
        return dur

df['ideal_durations'] = df['ideal_durations'].apply(process_durations)

# 6. 选择需要的字段，保留 ideal_durations
df_clean = df[['id', 'city', 'country', 'region', 'latitude', 'longitude', 
               'budget_level', 'culture', 'adventure', 'nature', 'beaches', 
               'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion', 
               'budget_score', 'top_trait', 'ideal_durations']]

# 7. 保存为清洗后的版本，使用默认的引号处理
df_clean.to_csv('../data/final_cleaned_travel_data.csv', index=False)

# 输出统计结果
print("各特质分布统计：")
print(df_clean['top_trait'].value_counts())