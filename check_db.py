import sqlite3
import os

def check_db(path, name):
    if not os.path.exists(path):
        print(f'{name}: 不存在 - {path}')
        return
    print(f'=== {name} ===')
    print(f'路径: {path}')
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('表列表:')
    for t in tables:
        table_name = t[0]
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        count = cursor.fetchone()[0]
        print(f'  - {table_name} ({count} 条记录)')
    conn.close()
    print()

# TRAE SOLO CN
solo_db = r'c:\Users\l\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\database.db'
check_db(solo_db, 'TRAE SOLO CN - database.db')

# 详细查看 conversation 相关的表
if os.path.exists(solo_db):
    print('=== 详细查看对话相关表 ===')
    conn = sqlite3.connect(solo_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%chat%' OR name LIKE '%conversation%' OR name LIKE '%message%' OR name LIKE '%session%'")
    tables = cursor.fetchall()
    for t in tables:
        table_name = t[0]
        print(f'\n--- {table_name} ---')
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()
        print('字段:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        count = cursor.fetchone()[0]
        print(f'记录数: {count}')
        if count > 0:
            cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 2")
            rows = cursor.fetchall()
            print('前2条记录:')
            for row in rows:
                print(f'  {row}')
    conn.close()

# 检查 TRAE IDE (.trae-cn) 有没有类似的数据库
trae_ide_user = r'c:\Users\l\AppData\Roaming\TraeCode'
import os
if os.path.exists(trae_ide_user):
    for root, dirs, files in os.walk(trae_ide_user):
        for f in files:
            if f == 'database.db':
                full_path = os.path.join(root, f)
                check_db(full_path, f'TRAE IDE - {f}')

# 找找 .trae-cn 下有没有数据库
trae_cn_dir = r'c:\Users\l\.trae-cn'
for root, dirs, files in os.walk(trae_cn_dir):
    for f in files:
        if f.endswith('.db') or f.endswith('.sqlite') or f.endswith('.sqlite3'):
            full_path = os.path.join(root, f)
            check_db(full_path, f'TRAE CN - {f}')
