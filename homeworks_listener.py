import asyncio

from loader import bot
from utils.db_api import database
from utils.sgo_api import Sgo

homework_typeId = 3


async def new_homework(lesson: dict, account: dict, assigment: dict):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, у тебя новое домашнее задание!\n'
            f'🗓 Дата: <code>{lesson["day"].split("T")[0]}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'📚 Предмет: <i>{lesson["subjectName"]}</i>\n'
            f'📕 <b>Задание</b>: <code>{assigment["assignmentName"]}</code>'
        )
        await asyncio.sleep(0.5)


async def edited_homework(lesson: dict, account: dict, assigment: dict, old_value: str):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, учитель изменил домашнее задание!\n'
            f'🗓 Дата: <code>{lesson["day"].split("T")[0]}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'📚 Предмет: <i>{lesson["subjectName"]}</i>\n'
            f'🚫 <b>Старое задание</b>: <code>{old_value}</code>\n'
            f'📕 <b>Новое задание</b>: <code>{assigment["assignmentName"]}</code>'
        )
        await asyncio.sleep(0.5)


async def deleted_homework(lesson: dict, account: dict, old_value: str):
    for user in account['users']:
        await bot.send_message(
            user['user_id'],
            '🤖 Привет, домашку можно не учить!\n'
            f'👩‍🏫 Учитель по <i>{lesson["subjectName"]}</i> удалил домашнее задание :)\n'
            f'🗓 Дата: <code>{lesson["day"].split("T")[0]}</code> (<b>{lesson["startTime"]}</b>)\n'
            f'🚫 Оно было таким: <code>{old_value}</code>'
        )
        await asyncio.sleep(0.5)


async def lesson_handler(lesson: dict, account: dict):
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
                    await new_homework(lesson, account, assigment)  # notify
                elif assigment['assignmentName'] != homework_cache['value']:
                    await database.update_homework_value(
                        account['id'],
                        homework_cache['id'],
                        assigment['assignmentName']
                    )
                    await edited_homework(lesson, account, assigment, homework_cache['value'])  # notify

    if homework_cache and not have_homework:
        await database.delete_homeworks(id=homework_cache['id'])
        await deleted_homework(lesson, account, homework_cache['value'])  # notify


async def main():
    for account in await database.get_accounts():
        account['users'] = await database.get_users(account_id=account['id'])
        if not account['users']:
            continue

        try:
            obj = await Sgo(account)
            timetable = await obj.timetable(check=True)
            if timetable.get('weekDays') is not None:
                for day in timetable['weekDays']:
                    for lesson in day['lessons']:
                        await lesson_handler(lesson, account)
            await obj.close()
        except Exception as err:
            print(err)


# if __name__ == '__main__':
asyncio.run(main())
