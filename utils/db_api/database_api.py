import json
from typing import Iterable, Any

import aiomysql
import configcatclient

import config


class AnswerType:
    none = 0
    array = 1
    dict = 2
    last_row_id = 3


class Sql:
    def __init__(self):
        self.config = configcatclient.create_client_with_auto_poll(
            config.cat_keys.MYSQL,
            on_configuration_changed_callback=self.update_login_data
        )
        self.database = None
        self.update_login_data()

    def update_login_data(self):
        self.database = {
            "host": self.config.get_value('host', 'localhost'),
            "port": self.config.get_value('port', 3306),
            "user": self.config.get_value('user', 'root'),
            "password": self.config.get_value('password', '1337'),
            "db": self.config.get_value('database', 'sgo_bot')
        }

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

    async def get_users_with_notify(self, **kwargs):
        return await self.query(
            'SELECT * FROM users WHERE homework_notifications or mark_notifications',
            where=kwargs
        )

    async def get_users_not_cached_with_notify(self, **kwargs):
        return await self.query(
            'SELECT * FROM users WHERE homework_notifications or mark_notifications',
            where=kwargs
        )

    async def get_users_with_homework_notify(self, **kwargs):
        return await self.query(
            'SELECT * FROM users WHERE homework_notifications',
            where=kwargs
        )

    async def get_users_with_mark_notify(self, **kwargs):
        return await self.query(
            'SELECT * FROM users WHERE mark_notifications',
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

    async def set_account_cached(self, cached, **kwargs):
        await self.query(
            "UPDATE accounts SET cached = ?",
            [cached],
            where=kwargs,
            _return=AnswerType.none
        )

    async def set_user_account_id_null(self, user_id):
        await self.query(
            "UPDATE users SET account_id = NULL WHERE id = ?",
            [user_id],
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

    async def create_homework(self, account_id, classmeetingId, value, date):
        await self.query(
            "INSERT INTO homeworks(account_id,class_meeting_id, value, date) VALUES(?, ?, ?, ?)",
            [account_id, classmeetingId, value, date],
            _return=AnswerType.none
        )

    async def update_homework_value(self, account_id, homework_id, value):
        await self.query(
            "UPDATE homeworks SET value = ? WHERE id = ? AND account_id = ?",
            [value, homework_id, account_id],
            _return=AnswerType.none
        )

    async def delete_user(self, user_id):
        user = await self.get_user(user_id=user_id)
        if len(await self.get_users(account_id=user['account_id'])) > 1:
            await self.set_user_account_id_null(user['id'])
            return False
        else:
            await self.delete_account(id=user['account_id'])
            return True

    async def get_marks(self, **kwargs):
        return await self.query(
            "SELECT * FROM marks",
            where=kwargs
        )

    async def delete_marks(self, **kwargs):
        await self.query(
            "DELETE FROM marks",
            where=kwargs,
            _return=AnswerType.none
        )

    async def update_mark(self, mark, **kwargs):
        await self.query(
            "UPDATE marks SET mark = ?",
            [mark],
            where=kwargs,
            _return=AnswerType.none
        )

    async def create_mark(self, account_id, class_meeting_id, assigment_id, mark):
        await self.query(
            "INSERT INTO marks(account_id, class_meeting_id, assigment_id, mark) VALUES(?, ?, ?, ?)",
            [account_id, class_meeting_id, assigment_id, mark],
            _return=AnswerType.none
        )
