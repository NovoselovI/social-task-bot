import sqlite3


def truncate_tables(db_path):
    """Удаление всех записей из таблиц, кроме исключенных"""
    exclude_tables = ['required_channels', 'settings', 'sqlite_sequence']

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [row[0] for row in cursor.fetchall()]

    # Фильтруем таблицы для обработки
    tables_to_clean = [table for table in all_tables if table not in exclude_tables]

    print("Начинаем очистку...")
    print(f"Исключены таблицы: {', '.join(exclude_tables)}")
    print(f"Обрабатываемые таблицы: {', '.join(tables_to_clean)}\n")

    for table in tables_to_clean:
        # Удаляем все записи из таблицы
        cursor.execute(f"DELETE FROM {table}")
        print(f"Удалены все записи из таблицы '{table}'")

        # Сбрасываем автоинкрементный счетчик (если есть)
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name = '{table}'")

    conn.commit()
    conn.close()
    print("\nОперация завершена успешно!")


# Укажите путь к вашей базе данных
DB_PATH = 'bot.db'

# Выполняем очистку
truncate_tables(DB_PATH)
