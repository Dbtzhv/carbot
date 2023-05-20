import sqlite3 as sq


async def db_start():
    global db, cur

    db = sq.connect('new.db')  # экземпляр БД, имя для БД
    cur = db.cursor()  # нужен для операций с БД
    # создаём таблицу cars:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS car(user_id TEXT , brand TEXT, year TEXT, name TEXT, phone TEXT)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS profile(user_id BIGINT PRIMARY KEY , name TEXT, phone TEXT)")
    db.commit()


async def create_car(state, user_id):
    async with state.proxy() as data:
        cur.execute(
            f"INSERT INTO car VALUES({user_id}, '{data['brand']}', '{data['year']}', '{data['name']}', '{data['phone']}')")
    db.commit()
    db.commit()


async def create_profile(user_id):
    user = cur.execute("SELECT 1 FROM profile WHERE user_id == '{key}'".format(
        key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO profile VALUES(?,?,?)", (user_id, '', ''))
    db.commit()


async def edit_profile(state, user_id):
    async with state.proxy() as data:
        cur.execute(
            f"UPDATE profile SET name = '{data['name']}', phone = '{data['phone']}' WHERE user_id == '{user_id}'")
    db.commit()
