import sqlite3
import os

ide_db = r'C:\Users\l\AppData\Roaming\Trae CN\ModularData\ai-agent\database.db'

if os.path.exists(ide_db):
    size_kb = os.path.getsize(ide_db) / 1024
    print(f'TRAE IDE 数据库大小: {size_kb:.2f} KB')
    print()
    
    conn = sqlite3.connect(ide_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('表列表:')
    for t in tables:
        table_name = t[0]
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        count = cursor.fetchone()[0]
        print(f'  - {table_name} ({count} 条记录)')
    
    print()
    print('=== 对话相关表详情 ===')
    
    chat_tables = [t[0] for t in tables if any(kw in t[0].lower() for kw in ['chat', 'conversation', 'message', 'session', 'agent'])]
    for table_name in chat_tables:
        print(f'\n--- {table_name} ---')
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()
        print('字段:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
    
    conn.close()
else:
    print('TRAE IDE 数据库不存在')
