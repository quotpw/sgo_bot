import json
from typing import Iterable, Any

import aiomysql


class AnswerType:
    none = 0
    array = 1
    dict = 2
    last_row_id = 3


class Sql:
    def __init__(self, host, port, user, password, db_name):
        self.database = {"host": host, "port": port, "user": user, "password": password, "db": db_name}

    async def query(self, query: str, params: Iterable[Any] = None, _return: int = AnswerType.dict, where: dict = None,
                    fetchone=False):
        if where:
            if 'where' not in query.lower():
                query += " WHERE "
            else:
                query += ' AND '
            if params is None:
                params = []
            where_strs = []
            for item in where:
                where_strs.append(f"`{item}` = ?")
                params.append(where[item])
            query += " AND ".join(where_strs)
        query = query.replace("?", "%s")
        async with aiomysql.connect(**self.database) as conn:
            await conn.autocommit(True)
            if _return == AnswerType.dict:
                cur = await conn.cursor(aiomysql.DictCursor)
            else:
                cur = await conn.cursor()
            await cur.execute(query, params)
            if _return is AnswerType.none:
                return
            elif _return == AnswerType.last_row_id:
                return cur.lastrowid
            else:
                if fetchone:
                    return await cur.fetchone()
                return await cur.fetchall()

    async def get_user(self, **kwargs):
        return await self.query(
            "SELECT * FROM users",
            where=kwargs,
            fetchone=True
        )

    async def get_users(self, **kwargs):
        return await self.query(
            "SELECT * FROM users",
            where=kwargs
        )

    async def create_user(self, user_id):
        await self.query(
            "INSERT INTO users(user_id) VALUES(?)",
            [user_id],
            _return=AnswerType.none
        )

    async def update_user_account_id(self, user_id, account_id):
        await self.query(
            "UPDATE users SET account_id = ? WHERE user_id = ?",
            [account_id, user_id],
            _return=AnswerType.none
        )

    async def create_account(self, name, state_id, city_id, org_type, org_id, username, password, session=None):
        return await self.query(
            "INSERT INTO accounts(name, state_id, city_id, org_type, org_id, username, password, session) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            [
                name,
                state_id, city_id, org_type, org_id,
                username, password,
                session if isinstance(session, str) else json.dumps(session)
            ],
            _return=AnswerType.last_row_id
        )

    async def get_accounts(self, **kwargs):
        return await self.query(
            "SELECT * FROM accounts",
            where=kwargs
        )

    async def update_account_session(self, account_id, session):
        await self.query(
            "UPDATE accounts SET session = ? WHERE id = ?",
            [session if isinstance(session, str) else json.dumps(session), account_id],
            _return=AnswerType.none
        )

    async def get_account(self, **kwargs):
        return await self.query(
            "SELECT * FROM accounts",
            where=kwargs,
            fetchone=True
        )

    async def delete_account(self, **kwargs):
        await self.query(
            "DELETE FROM accounts",
            where=kwargs,
            _return=AnswerType.none
        )

    async def get_homework(self, **kwargs):
        return await self.query(
            "SELECT * FROM homeworks",
            where=kwargs,
            fetchone=True
        )

    async def delete_homeworks(self, **kwargs):
        await self.query(
            "DELETE FROM homeworks",
            where=kwargs,
            _return=AnswerType.none
        )

    async def create_homework(self, classmeetingId, value, date):
        await self.query(
            "INSERT INTO homeworks(class_meeting_id, value, date) VALUES(?, ?, ?)",
            [classmeetingId, value, date],
            _return=AnswerType.none
        )

    async def update_homework_value(self, homework_id, value):
        await self.query(
            "UPDATE homeworks SET value = ? WHERE id = ?",
            [value, homework_id],
            _return=AnswerType.none
        )
