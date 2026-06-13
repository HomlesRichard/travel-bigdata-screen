"""数据库配置检验模块 - 启动前检验并允许用户重新输入"""
import pymysql
from pymysql import Error
import configparser
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')

def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding='utf-8')
        return {
            'host': config.get('database', 'host', fallback='localhost'),
            'user': config.get('database', 'user', fallback='root'),
            'password': config.get('database', 'password', fallback='123456'),
            'database': config.get('database', 'database', fallback='travel_db'),
            'port': config.getint('database', 'port', fallback=3306)
        }
    return None

def save_config(host, user, password, database, port):
    """保存配置文件"""
    config = configparser.ConfigParser()
    config['database'] = {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': str(port)
    }
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        config.write(f)

def test_connection(host, user, password, port=3306):
    """测试数据库连接"""
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            connect_timeout=5
        )
        conn.close()
        return True, "连接成功"
    except Error as e:
        return False, str(e)

def check_database_exists(host, user, password, database, port):
    """检查数据库是否存在"""
    try:
        conn = pymysql.connect(host=host, user=user, password=password, port=port)
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{database}'")
            result = cursor.fetchone()
            exists = result is not None
        conn.close()
        return exists
    except Error as e:
        return False

def create_database(host, user, password, database, port):
    """创建数据库"""
    try:
        conn = pymysql.connect(host=host, user=user, password=password, port=port)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()
        return True
    except Error as e:
        return False

def check_table_exists(config_dict):
    """检查表是否存在"""
    try:
        conn = pymysql.connect(
            host=config_dict['host'],
            user=config_dict['user'],
            password=config_dict['password'],
            database=config_dict['database'],
            port=config_dict['port'],
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'cities'")
            result = cursor.fetchone()
            exists = result is not None
        conn.close()
        return exists
    except Error:
        return False

def get_table_count(config_dict):
    """获取表记录数"""
    try:
        conn = pymysql.connect(
            host=config_dict['host'],
            user=config_dict['user'],
            password=config_dict['password'],
            database=config_dict['database'],
            port=config_dict['port'],
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM cities")
            result = cursor.fetchone()
            count = result['count']
        conn.close()
        return count
    except Error:
        return 0

def prompt_for_credentials():
    """提示用户输入数据库凭据"""
    print("\n" + "=" * 60)
    print("  数据库连接失败，请重新输入MySQL配置信息")
    print("=" * 60)
    
    current_config = load_config()
    
    print("\n当前配置 (直接回车保持原值):")
    if current_config:
        print(f"  主机: {current_config['host']}")
        print(f"  用户: {current_config['user']}")
        print(f"  数据库: {current_config['database']}")
        print(f"  端口: {current_config['port']}")
    
    print()
    
    # 获取用户输入
    host = input(f"请输入MySQL主机地址 [默认: {current_config['host'] if current_config else 'localhost'}]: ").strip()
    if not host:
        host = current_config['host'] if current_config else 'localhost'
    
    user = input(f"请输入MySQL用户名 [默认: {current_config['user'] if current_config else 'root'}]: ").strip()
    if not user:
        user = current_config['user'] if current_config else 'root'
    
    password = input("请输入MySQL密码: ").strip()
    if not password and current_config:
        password = current_config['password']
    
    database = input(f"请输入数据库名 [默认: {current_config['database'] if current_config else 'travel_db'}]: ").strip()
    if not database:
        database = current_config['database'] if current_config else 'travel_db'
    
    port = input(f"请输入MySQL端口 [默认: {current_config['port'] if current_config else 3306}]: ").strip()
    if not port:
        port = current_config['port'] if current_config else 3306
    else:
        port = int(port)
    
    return host, user, password, database, port

def verify_and_setup_database():
    """检验并设置数据库 - 应用启动前调用"""
    print("\n" + "=" * 60)
    print("  Travel BigData Screen - 数据库检验")
    print("=" * 60)
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        config = load_config()
        
        if config:
            print(f"\n尝试连接数据库 (第 {attempt} 次)...")
            print(f"  主机: {config['host']}")
            print(f"  用户: {config['user']}")
            print(f"  数据库: {config['database']}")
            print(f"  端口: {config['port']}")
            
            success, message = test_connection(config['host'], config['user'], config['password'], config['port'])
            
            if success:
                print("  ✓ MySQL连接成功")
                
                # 检查数据库是否存在
                db_exists = check_database_exists(config['host'], config['user'], config['password'], config['database'], config['port'])
                if not db_exists:
                    print(f"  数据库 {config['database']} 不存在，正在创建...")
                    create_database(config['host'], config['user'], config['password'], config['database'], config['port'])
                    print(f"  ✓ 数据库 {config['database']} 创建成功")
                else:
                    print(f"  ✓ 数据库 {config['database']} 存在")
                
                # 检查表是否存在
                table_exists = check_table_exists(config)
                if not table_exists:
                    print("  cities 表不存在，请先运行: python mysql/import_to_mysql.py")
                    return False, "表不存在，需要导入数据"
                else:
                    print("  ✓ cities 表存在")
                
                # 检查数据是否存在
                count = get_table_count(config)
                if count == 0:
                    print("  cities 表中没有数据，请先运行: python mysql/import_to_mysql.py")
                    return False, "数据不存在，需要导入数据"
                else:
                    print(f"  ✓ cities 表中有 {count} 条记录")
                
                print("\n" + "=" * 60)
                print("  数据库检验完成，准备启动应用...")
                print("=" * 60 + "\n")
                
                return True, config
            else:
                print(f"  ✗ 连接失败: {message}")
                
                if attempt < max_attempts:
                    # 提示用户重新输入
                    host, user, password, database, port = prompt_for_credentials()
                    
                    # 测试新配置
                    success, message = test_connection(host, user, password, port)
                    if success:
                        # 保存新配置
                        save_config(host, user, password, database, port)
                        print("  ✓ 新配置已保存，连接成功!")
                        
                        # 检查并创建数据库
                        db_exists = check_database_exists(host, user, password, database, port)
                        if not db_exists:
                            create_database(host, user, password, database, port)
                            print(f"  ✓ 数据库 {database} 创建成功")
                        
                        # 返回新配置
                        new_config = {
                            'host': host,
                            'user': user,
                            'password': password,
                            'database': database,
                            'port': port,
                            'cursorclass': pymysql.cursors.DictCursor
                        }
                        
                        # 检查表和数据
                        table_exists = check_table_exists(new_config)
                        if not table_exists:
                            print("  cities 表不存在，请先运行: python mysql/import_to_mysql.py")
                            return False, "表不存在"
                        
                        count = get_table_count(new_config)
                        if count == 0:
                            print("  cities 表中没有数据，请先运行: python mysql/import_to_mysql.py")
                            return False, "数据不存在"
                        
                        print(f"  ✓ cities 表中有 {count} 条记录")
                        print("\n数据库检验完成!")
                        
                        return True, new_config
                    else:
                        print(f"  ✗ 新配置连接失败: {message}")
                        print("  请检查MySQL是否已启动，以及账号密码是否正确")
        else:
            print("  配置文件不存在，请输入MySQL配置信息")
            host, user, password, database, port = prompt_for_credentials()
            save_config(host, user, password, database, port)
    
    print("\n" + "=" * 60)
    print("  数据库连接失败次数过多，请检查MySQL配置")
    print("  您可以手动修改 mysql/config.ini 文件")
    print("=" * 60)
    
    return False, None

if __name__ == "__main__":
    success, config = verify_and_setup_database()
    if success:
        print("数据库配置完成!")
    else:
        sys.exit(1)