import asyncio
import json
import re
from asyncio import sleep
from hashlib import md5
from time import time

import pendulum
from aiohttp_proxy import ProxyConnector
from async_class import AsyncObject

from utils.sgo_api.proxy import Proxy
from utils.db_api import database
from aiohttp import CookieJar, ClientSession
from .exceptions import LoginError
from data.config import SGO

SGO_URL = 'https://sgo.rso23.ru/'


class Sgo(AsyncObject):
    year_id = None
    user = None
    connector = None

    async def __ainit__(self, account: dict, proxy=None, proxy_scheme='http'):
        self.account = account
        if isinstance(self.account.get('session'), str):
            self.account['session'] = json.loads(self.account['session'])
        if proxy is None:
            proxy = SGO.PROXY
            proxy_scheme = SGO.PROXY_SCHEME

        if proxy is not None:
            self.proxy = Proxy()
            self.proxy.parse(proxy, proxy_scheme)
            self.connector = ProxyConnector.from_url(self.proxy.url)

        # init session
        cookie_jar = None
        if self.account.get('session') is not None:
            if self.account['session'].get('cookies') is not None:
                cookie_jar = CookieJar(quote_cookie=False)
                cookie_jar.update_cookies(self.account['session']['cookies'])

        self.session = ClientSession(
            SGO_URL,
            headers={"Referer": SGO_URL},
            connector=self.connector,
            cookie_jar=cookie_jar
        )

        if self.account.get('session') is not None:
            await self.set_auth_session(self.account['session'])
            login_required = not await self.check_sess()
        else:
            login_required = True
        if login_required:
            if not await self.login():
                await self.session.close()
                if account['id']:
                    await database.delete_account(id=account['id'])
                raise LoginError('Login error while init SGO object.')

    async def set_auth_session(self, auth_session: dict, update_database=False):
        self.user = auth_session['accountInfo']['user']
        self.session.headers.update({'at': auth_session['at']})
        self.account['session'] = auth_session
        if update_database:
            await database.update_account_session(self.account['id'], auth_session)

    async def get_auth_data(self):
        return await (await self.session.post('/webapi/auth/getdata')).json()

    async def login(self):
        password = self.account['password']
        if len(password) != 32:
            password = md5(password.encode()).hexdigest()

        auth_data = await self.get_auth_data()
        encrypted_password = md5((str(auth_data['salt']) + password).encode()).hexdigest()

        auth_resp = await self.session.post(
            '/webapi/login',
            data={
                'LoginType': '1',
                'cid': '2',
                'sid': '23',
                'pid': self.account['state_id'],
                'cn': self.account['city_id'],
                'sft': self.account['org_type'],
                'scid': self.account['org_id'],
                'UN': self.account['username'],
                'PW': encrypted_password[:8],
                'lt': auth_data['lt'],
                'pw2': encrypted_password,
                'ver': auth_data['ver']
            }
        )

        if auth_resp.status != 200:
            return False

        tmp_session = await auth_resp.json()
        tmp_session['cookies'] = {}
        for cookie in self.session.cookie_jar:
            tmp_session['cookies'][cookie.key] = cookie.value
        await self.set_auth_session(tmp_session, True)
        return True

    async def SecurityWarning_fix(self, warnType, at):
        self.account['session']['at'] = at
        await self.set_auth_session(self.account['session'], True)
        return await(await self.session.post(
            '/asp/SecurityWarning.asp',
            data={"warnType": "2", "at": self.account['session']['at']}
        )).text()

    async def school_student_diary(self):
        resp = await (await self.session.post(
            '/angular/school/studentdiary/',
            data={'LoginType': '0', 'AT': self.account['session']['at'], 'VER': time()}
        )).text()
        if '/asp/SecurityWarning.asp' in resp:
            at = re.findall('name="AT" value="(.*?)"', resp)[0]
            warn_type = re.findall('name="WarnType" value="(.*?)"', resp)[0]
            return await self.SecurityWarning_fix(warn_type, at)
        else:
            return resp

    async def check_sess(self):
        student_diary = await self.school_student_diary()
        if 'login' not in student_diary:
            if self.year_id is None:
                await self.update_year_id(student_diary)
            return True
        else:
            return False

    async def update_year_id(self, text=None):
        if text is None:
            text = await self.school_student_diary()
        self.year_id = re.findall('appContext\.yearId.*?"(.*?)"', text)[0]

    async def __timetable(self, week, year_id):
        return await (await self.session.get(
            '/webapi/student/diary',
            params={
                'studentId': self.user['id'],
                'vers': time() * 1000,
                'weekStart': week.start_of('week').format('YYYY-MM-DD'),
                'weekEnd': week.end_of('week').format('YYYY-MM-DD'),
                'withLaAssigns': 'true',
                'yearId': year_id
            }
        )).json()

    async def timetable(self, week: pendulum.DateTime = None, year_id=None, check=False):
        if not week:
            week = pendulum.now()
        if week.format('dddd') == 'Sunday':
            week = week.add(days=1)
        if year_id is None:
            if self.year_id is None:
                await self.update_year_id()
            year_id = self.year_id

        resp = await self.__timetable(week, year_id)
        if check:
            last_week_day = resp['weekDays'][-1]
            date_of_last_week_day = pendulum.parse(
                f"{last_week_day['date'].split('T')[0]}T{last_week_day['lessons'][-1]['endTime']}"
            )
            if week > date_of_last_week_day:
                week = week.add(days=2)
                return await self.timetable(week, year_id, check)
            else:
                return resp
        else:
            return resp

    async def information_letter_for_parents(self):
        req_data = re.findall(
            'name="PCLID" value="(\d*?)".*?TERMID.*?"(\d*?)" selected.*?name="SID" value="(\d*?)"',
            await (await self.session.post(
                '/asp/Reports/ReportParentInfoLetter.asp',
                data={
                    'AT': self.account['session']['at'],
                    'VER': time(),
                    'RPNAME': 'Информационное письмо для родителей',
                    'RPTID': 'ParentInfoLetter'
                }
            )).text(),
            re.DOTALL
        )[0]

        date = pendulum.now().format('DD.MM.YY')
        parent_info_resp = await(await self.session.post(
            '/asp/Reports/ParentInfoLetter.asp',
            data={
                'LoginType': '0',
                'AT': self.account['session']['at'],
                'VER': time(),
                'PP': '/asp/Reports/ReportParentInfoLetter.asp',
                'BACK': '/asp/Reports/ReportParentInfoLetter.asp',
                'ThmID': '',
                'RPTID': 'ParentInfoLetter',
                'A': '',
                'NA': '',
                'TA': '',
                'RT': '',
                'RP': '',
                'dtWeek': date,
                'PCLID': req_data[0],
                'ReportType': '1',
                'TERMID': req_data[1],
                'DATE': date,
                'SID': req_data[2]
            }
        )).text()

        return re.findall(
            'cell-text">(.*?)<.*?td.*?td.*?td.*?td.*?td.*?td.*?td.*?td.*?td.*?td>(.*?)<',
            parent_info_resp
        )

    async def __adel__(self):
        await sleep(0.5)
        await self.session.close()
