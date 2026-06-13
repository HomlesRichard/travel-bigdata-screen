"""MySQL数据库操作模块"""
import pymysql
from pymysql import Error
import configparser
import os

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
        # 默认配置（配置文件不存在时使用）
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

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"数据库连接失败: {e}")
        return None

def check_database_exists():
    """检查数据库是否存在"""
    try:
        config = load_db_config()
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            port=config['port']
        )
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{config['database']}'")
            result = cursor.fetchone()
            return result is not None
    except Error as e:
        print(f"检查数据库失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_table_exists(table_name='cities'):
    """检查表是否存在"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            return result is not None
    except Error as e:
        print(f"检查表失败: {e}")
        return False
    finally:
        conn.close()

def get_table_count(table_name='cities'):
    """获取表中的记录数"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            result = cursor.fetchone()
            return result['COUNT(*)']
    except Error as e:
        print(f"获取记录数失败: {e}")
        return 0
    finally:
        conn.close()

def get_cities_list():
    """获取所有城市列表"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, city, country, region, budget_level, latitude, longitude FROM cities ORDER BY country, city")
            cities = cursor.fetchall()
            return cities
    except Error as e:
        print(f"查询城市列表失败: {e}")
        return []
    finally:
        conn.close()

def get_all_cities():
    """获取所有城市详细信息"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM cities ORDER BY country, city")
            cities = cursor.fetchall()
            return cities
    except Error as e:
        print(f"查询所有城市失败: {e}")
        return []
    finally:
        conn.close()

def get_city_by_id(city_id):
    """根据ID获取城市信息"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM cities WHERE id = %s", (city_id,))
            city = cursor.fetchone()
            return city
    except Error as e:
        print(f"查询城市失败: {e}")
        return None
    finally:
        conn.close()

def get_cities_by_ids(city_ids):
    """根据ID列表获取多个城市信息"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(city_ids))
            query = f"SELECT * FROM cities WHERE id IN ({placeholders})"
            cursor.execute(query, tuple(city_ids))
            cities = cursor.fetchall()
            return cities
    except Error as e:
        print(f"查询城市列表失败: {e}")
        return []
    finally:
        conn.close()

def search_cities(keyword=None, region=None, budget_level=None):
    """搜索城市"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM cities WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND (city LIKE %s OR country LIKE %s)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if region:
                query += " AND region = %s"
                params.append(region)
            
            if budget_level:
                query += " AND budget_level = %s"
                params.append(budget_level)
            
            query += " ORDER BY country, city"
            cursor.execute(query, tuple(params))
            cities = cursor.fetchall()
            return cities
    except Error as e:
        print(f"搜索城市失败: {e}")
        return []
    finally:
        conn.close()