import asyncio
import time

import sentry_sdk

from handlers.users.start import menu_markup
from loader import bot
from utils.db_api import database
from utils.sgo_api import Sgo

sentry_sdk.init(
    "https://edf4b3eae7734e05a6309ea09d556a60@o1154088.ingest.sentry.io/6241296",
    traces_sample_rate=1.0
)

homework_typeId = 3


def normalise_date(date: str):
    return '-'.join(date.split('T')[0].split('-')[::-1])


async def new_homework(lesson: dict, account: dict, assigment: dict):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, у тебя новое домашнее задание!\n'
            f'🗓 Дата: <code>{normalise_date(lesson["day"])}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'📚 Предмет: <i>{lesson["subjectName"]}</i>\n'
            f'📕 <b>Задание</b>: <code>{assigment["assignmentName"]}</code>',
            reply_markup=menu_markup
        )
        await asyncio.sleep(0.5)


async def edited_homework(lesson: dict, account: dict, assigment: dict, old_value: str):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, учитель изменил домашнее задание!\n'
            f'🗓 Дата: <code>{normalise_date(lesson["day"])}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'📚 Предмет: <i>{lesson["subjectName"]}</i>\n'
            f'🚫 <b>Старое задание</b>: <code>{old_value}</code>\n'
            f'📕 <b>Новое задание</b>: <code>{assigment["assignmentName"]}</code>',
            reply_markup=menu_markup
        )
        await asyncio.sleep(0.5)


async def deleted_homework(lesson: dict, account: dict, old_value: str):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, домашку можно не учить!\n'
            f'👩‍🏫 Учитель по <i>{lesson["subjectName"]}</i> удалил домашнее задание :)\n'
            f'🗓 Дата: <code>{normalise_date(lesson["day"])}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'🚫 Оно было таким: <code>{old_value}</code>',
            reply_markup=menu_markup
        )
        await asyncio.sleep(0.5)


async def homework_checker(lesson: dict, account: dict):
    homework_cache = await database.get_homework(account_id=account['id'], class_meeting_id=lesson['classmeetingId'])

    have_homework = False
    if lesson.get('assignments'):
        for assigment in lesson['assignments']:
            if assigment['typeId'] == homework_typeId:
                have_homework = True
                if not homework_cache:
                    await database.create_homework(
                        account['id'],
                        lesson['classmeetingId'],
                        assigment['assignmentName'],
                        lesson['day']
                    )
                    if account['cached']:
                        await new_homework(lesson, account, assigment)  # notify
                elif assigment['assignmentName'] != homework_cache['value']:
                    await database.update_homework_value(
                        account['id'],
                        homework_cache['id'],
                        assigment['assignmentName']
                    )
                    if account['cached']:
                        await edited_homework(lesson, account, assigment, homework_cache['value'])  # notify

    if homework_cache and not have_homework:
        await database.delete_homeworks(id=homework_cache['id'])
        if account['cached']:
            await deleted_homework(lesson, account, homework_cache['value'])  # notify


async def new_mark(lesson: dict, account: dict, assigment: dict):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, у тебя новая оценка!\n'
            f'🗓 Дата: <code>{normalise_date(lesson["day"])}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'📚 Предмет: <i>{lesson["subjectName"]}</i>\n'
            f'📕 За что: <code>{assigment["assignmentName"]}</code>\n'
            f'🔰 <b>Оценка</b>: <i>{assigment["mark"]["mark"]}</i>',
            reply_markup=menu_markup
        )
        await asyncio.sleep(0.5)


async def edited_mark(lesson: dict, account: dict, assigment: dict, old_value: str):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, учитель изменил тебе оценку!\n'
            f'🗓 Дата: <code>{normalise_date(lesson["day"])}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'📚 Предмет: <i>{lesson["subjectName"]}</i>\n'
            f'📕 За что: <code>{assigment["assignmentName"]}</code>\n'
            f'🚫 <b>Старая оценка</b>: <i>{old_value}</i>\n'
            f'🔰 <b>Новая оценка</b>: <i>{assigment["mark"]["mark"]}</i>',
            reply_markup=menu_markup
        )
        await asyncio.sleep(0.5)


async def deleted_mark(lesson: dict, account: dict, old_value: int):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            f'🤖 Привет, тебе удалили оценку{" 😟" if old_value >= 4 else ".."}\n'
            f'👩‍🏫 Учитель по <i>{lesson["subjectName"]}</i> тебе оценку.\n'
            f'🗓 Дата: <code>{normalise_date(lesson["day"])}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'🚫 Она была такой: <code>{old_value}</code>',
            reply_markup=menu_markup
        )
        await asyncio.sleep(0.5)


async def mark_checker(lesson: dict, account: dict):
    marks_cache = await database.get_marks(account_id=account['id'], class_meeting_id=lesson['classmeetingId'])

    assigment_to_mark = {}
    for mark_info in marks_cache:
        assigment_to_mark[mark_info['assigment_id']] = mark_info['mark']

    if lesson.get('assignments'):
        for assigment in lesson['assignments']:
            if assigment.get('mark'):
                try:
                    cached_mark = assigment_to_mark.pop(assigment['mark']['assignmentId'])
                    # Mark in base
                    if cached_mark != assigment['mark']['mark']:
                        await database.update_mark(
                            assigment['mark']['mark'],
                            account_id=account['id'],
                            class_meeting_id=lesson['classmeetingId'],
                            assigment_id=assigment['mark']['assignmentId']
                        )
                        if account['cached']:
                            await edited_mark(lesson, account, assigment, cached_mark)
                except KeyError:
                    # Mark not in base
                    await database.create_mark(
                        account['id'],
                        lesson['classmeetingId'],
                        assigment['mark']['assignmentId'],
                        assigment['mark']['mark']
                    )
                    if account['cached']:
                        await new_mark(lesson, account, assigment)

    for assigment_id in assigment_to_mark:
        # Assignments without marks! (with deleted marks)
        await database.delete_marks(
            account_id=account['id'],
            class_meeting_id=lesson['classmeetingId'],
            assigment_id=assigment_id
        )
        if account['cached']:
            await deleted_mark(lesson, account, assigment_to_mark[assigment_id])


async def main():
    for account in await database.get_accounts():
        if not await database.get_users_with_notify(account_id=account['id']):
            continue

        try:
            obj = await Sgo(account)
            timetable = await obj.timetable(check=True)
            if timetable.get('weekDays') is not None:
                for day in timetable['weekDays']:
                    for lesson in day['lessons']:
                        # get users with homework notifications
                        account['users'] = await database.get_users_with_homework_notify(account_id=account['id'])
                        if account['users']:
                            await homework_checker(lesson, account)

                        # get users with homework notifications
                        account['users'] = await database.get_users_with_mark_notify(account_id=account['id'])
                        if account['users']:
                            await mark_checker(lesson, account)
            await obj.close()
        except Exception as err:
            print(err)

        if not account['cached']:
            await database.set_account_cached(True, id=account['id'])


# if __name__ == '__main__':
while True:
    asyncio.run(main())
    time.sleep(600)
