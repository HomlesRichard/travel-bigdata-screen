"""CSV数据导入MySQL模块 - 支持自动检验与完善"""
import pandas as pd
import pymysql
from pymysql import Error
import configparser
import os
import sys

# 从配置文件读取数据库配置
def load_db_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if os.path.exists(config_path):
        config.read(config_path, encoding='utf-8')
        return {
            'host': config.get('database', 'host', fallback='localhost'),
            'user': config.get('database', 'user', fallback='root'),
            'password': config.get('database', 'password', fallback='123456'),
            'database': config.get('database', 'database', fallback='travel_db'),
            'port': config.getint('database', 'port', fallback=3306),
            'cursorclass': pymysql.cursors.DictCursor
        }
    else:
        print("警告: 配置文件 config.ini 不存在，使用默认配置")
        return {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',
            'database': 'travel_db',
            'port': 3306,
            'cursorclass': pymysql.cursors.DictCursor
        }

DB_CONFIG = load_db_config()

def create_database():
    """创建数据库（如果不存在）"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✓ 数据库 {DB_CONFIG['database']} 创建成功或已存在")
    except Error as e:
        print(f"✗ 创建数据库时出错: {e}")
        raise
    finally:
        conn.close()

def create_tables():
    """创建数据表（如果不存在）"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 创建城市表
            create_city_table = """
            CREATE TABLE IF NOT EXISTS cities (
                id VARCHAR(36) PRIMARY KEY,
                city VARCHAR(100) NOT NULL,
                country VARCHAR(100) NOT NULL,
                region VARCHAR(50),
                latitude DECIMAL(10,7),
                longitude DECIMAL(10,7),
                budget_level VARCHAR(20),
                culture INT,
                adventure INT,
                nature INT,
                beaches INT,
                nightlife INT,
                cuisine INT,
                wellness INT,
                urban INT,
                seclusion INT,
                budget_score INT,
                top_trait VARCHAR(50),
                ideal_durations TEXT,
                short_description TEXT,
                avg_temp_monthly TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_city_table)
            conn.commit()
            print("✓ cities 表创建成功或已存在")
    except Error as e:
        print(f"✗ 创建表时出错: {e}")
        raise
    finally:
        conn.close()

def check_and_auto_fix():
    """自动检验并完善数据库"""
    print("\n" + "=" * 50)
    print("自动检验数据库状态...")
    print("=" * 50)
    
    # 1. 检查MySQL连接
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        print("✓ MySQL连接成功")
        conn.close()
    except Error as e:
        print(f"✗ MySQL连接失败: {e}")
        print("  请检查 config.ini 中的数据库配置是否正确")
        return False
    
    # 2. 检查数据库是否存在
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{DB_CONFIG['database']}'")
            result = cursor.fetchone()
            if result:
                print(f"✓ 数据库 {DB_CONFIG['database']} 存在")
            else:
                print(f"✗ 数据库 {DB_CONFIG['database']} 不存在，正在自动创建...")
                create_database()
        conn.close()
    except Error as e:
        print(f"✗ 检查数据库失败: {e}")
        return False
    
    # 3. 检查表是否存在
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'cities'")
            result = cursor.fetchone()
            if result:
                print("✓ cities 表存在")
            else:
                print("✗ cities 表不存在，正在自动创建...")
                create_tables()
        conn.close()
    except Error as e:
        print(f"✗ 检查表失败: {e}")
        return False
    
    # 4. 检查数据是否存在
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM cities")
            count = cursor.fetchone()['COUNT(*)']
            if count > 0:
                print(f"✓ cities 表中有 {count} 条记录")
            else:
                print("✗ cities 表中没有数据，正在自动导入...")
                import_csv_to_mysql()
        conn.close()
    except Error as e:
        print(f"✗ 检查数据失败: {e}")
        return False
    
    print("=" * 50)
    print("数据库检验完成，一切正常！")
    print("=" * 50)
    return True

def import_csv_to_mysql():
    """导入CSV数据到MySQL"""
    try:
        # 检查CSV文件是否存在
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'final_cleaned_travel_data.csv')
        if not os.path.exists(csv_path):
            print(f"✗ CSV文件不存在: {csv_path}")
            return 0
        
        # 读取清洗后的主数据
        df_clean = pd.read_csv(csv_path)
        
        # 读取原始数据获取描述信息
        original_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Worldwide Travel Cities Dataset (Ratings and Climate).csv')
        df_original = pd.read_csv(original_csv_path)
        desc_dict = df_original.set_index('id')[['short_description', 'avg_temp_monthly']].to_dict('index')
        
        # 合并数据
        df_clean['short_description'] = df_clean['id'].apply(
            lambda x: desc_dict.get(x, {}).get('short_description', '')
        )
        df_clean['avg_temp_monthly'] = df_clean['id'].apply(
            lambda x: desc_dict.get(x, {}).get('avg_temp_monthly', '')
        )
        
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 清空表
            cursor.execute("TRUNCATE TABLE cities")
            
            # 插入数据
            insert_query = """
            INSERT INTO cities (
                id, city, country, region, latitude, longitude, budget_level,
                culture, adventure, nature, beaches, nightlife, cuisine,
                wellness, urban, seclusion, budget_score, top_trait,
                ideal_durations, short_description, avg_temp_monthly
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            rows_inserted = 0
            for _, row in df_clean.iterrows():
                values = (
                    row['id'],
                    row['city'],
                    row['country'],
                    row['region'],
                    row['latitude'],
                    row['longitude'],
                    row['budget_level'],
                    int(row['culture']) if pd.notna(row['culture']) else 0,
                    int(row['adventure']) if pd.notna(row['adventure']) else 0,
                    int(row['nature']) if pd.notna(row['nature']) else 0,
                    int(row['beaches']) if pd.notna(row['beaches']) else 0,
                    int(row['nightlife']) if pd.notna(row['nightlife']) else 0,
                    int(row['cuisine']) if pd.notna(row['cuisine']) else 0,
                    int(row['wellness']) if pd.notna(row['wellness']) else 0,
                    int(row['urban']) if pd.notna(row['urban']) else 0,
                    int(row['seclusion']) if pd.notna(row['seclusion']) else 0,
                    int(row['budget_score']) if pd.notna(row['budget_score']) else 0,
                    row['top_trait'],
                    row['ideal_durations'],
                    row['short_description'],
                    row['avg_temp_monthly']
                )
                cursor.execute(insert_query, values)
                rows_inserted += 1
            
            conn.commit()
            print(f"✓ 成功插入 {rows_inserted} 条记录")
        
        return rows_inserted
    except Error as e:
        print(f"✗ 导入数据时出错: {e}")
        raise
    except Exception as e:
        print(f"✗ 处理数据时出错: {e}")
        raise
    finally:
        if conn:
            conn.close()

def verify_data():
    """验证导入的数据"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 查询记录数
            cursor.execute("SELECT COUNT(*) FROM cities")
            count = cursor.fetchone()['COUNT(*)']
            print(f"数据库中共有 {count} 条城市记录")
            
            # 查询前3条记录
            cursor.execute("SELECT id, city, country FROM cities LIMIT 3")
            print("前3条记录:")
            for row in cursor.fetchall():
                print(f"  {row['city']}, {row['country']}")
    except Error as e:
        print(f"验证数据时出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  MySQL 数据库自动检验与完善工具")
    print("=" * 60)
    
    # 显示当前配置
    print(f"\n当前数据库配置:")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print(f"  端口: {DB_CONFIG['port']}")
    
    # 自动检验并完善
    if check_and_auto_fix():
        verify_data()
        print("\n" + "=" * 60)
        print("  数据库已准备就绪，可以启动应用！")
        print("  运行: python app.py")
        print("=" * 60)
    else:
        print("\n请修改 mysql/config.ini 中的数据库配置后重试")
        sys.exit(1)