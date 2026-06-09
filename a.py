import pandas as pd
df = pd.read_csv("data\Worldwide Travel Cities Dataset (Ratings and Climate).csv")
print(df['short_description'].isna().sum())          # 真正 NaN 的数量
print(df['short_description'].str.strip().eq('').sum()) # 空字符串的数量