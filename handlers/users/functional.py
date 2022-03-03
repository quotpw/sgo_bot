import re

import configcatclient
import pendulum
from aiogram import types
from aiogram.dispatcher.filters import Text
from wand.image import Image

import config
from loader import dp
from utils.db_api import database
from utils.misc.throttling import rate_limit
from utils.sgo_api import Sgo

config = configcatclient.create_client(config.cat_keys.TELEGRAM)


def sort_lessons(elem):
    return elem['startTime']


@rate_limit(config.get_value('sgo_rate_limit', 0), 'timetable')
@dp.message_handler(Text('Получить рассписание', ignore_case=True), user_with_account=True)
async def start_with_account(message: types.Message):
    user = await database.get_user(user_id=message.chat.id)
    await message.answer("Ожидайте, подготоваливаю данные.")
    obj = await Sgo(await database.get_account(id=user['account_id']))
    date = pendulum.now('Europe/Moscow')
    timetable = await obj.timetable(date, check=True)

    lessons = None
    day_time = None
    for day in timetable['weekDays']:
        if not day.get('lessons'):
            continue

        last_lesson = day['lessons']
        last_lesson.sort(key=sort_lessons)
        last_lesson = last_lesson[-1]

        day_time = pendulum.parse(day['date'].replace('00:00:00', '') + last_lesson['endTime'])
        if date < day_time:
            lessons = day['lessons']
            break

    print(lessons)
    svg_photo = open('handlers/users/timetable.svg', encoding='utf-8').read() \
        .replace('week_day_date', day_time.format('dddd, D MMMM YYYY г.', 'ru'))

    for lesson in lessons:
        lesson_number = lesson['number']
        lesson_name = lesson['subjectName']
        if len(lesson_name) > 16:
            lesson_name = lesson_name[:16] + '...'
        svg_photo = svg_photo \
            .replace(f'subjectName{lesson_number}', lesson_name) \
            .replace(f'startTime{lesson_number}', lesson['startTime']) \
            .replace(f'endTime{lesson_number}', lesson['endTime'])
        if lesson.get('assignments'):
            assignments = lesson['assignments'][0]['assignmentName']
            max_len = 55
            if len(assignments) > max_len:
                first_text = ""
                for word in assignments.split(' '):
                    if len(first_text + word) > max_len:
                        break
                    else:
                        first_text += word + " "
                assignments = f'<tspan x="0">{first_text}</tspan>' \
                              f'<tspan x="0" dy="1em">{assignments[len(first_text):]}</tspan>'
            else:
                assignments = f'<tspan x="0">{assignments}</tspan>'
            svg_photo = svg_photo.replace(f'assignment{lesson_number}', assignments)
        else:
            svg_photo = svg_photo.replace(f'assignment{lesson_number}', '')

    svg_photo = re.sub('assignment\d|subjectName\d|startTime\d - endTime\d', '', svg_photo)  # delete unused vars

    with Image(blob=svg_photo.encode('utf-8'), format="svg") as image:
        await message.reply_photo(image.make_blob("jpg"))


@rate_limit(config.get_value('sgo_rate_limit', 0), 'average_grades')
@dp.message_handler(Text('Средние оценки', ignore_case=True), user_with_account=True)
async def start_with_account(message: types.Message):
    user = await database.get_user(user_id=message.chat.id)
    await message.answer("Ожидайте, подготоваливаю данные.")
    obj = await Sgo(await database.get_account(id=user['account_id']))
    text = "<b>Средние оценки по предметам:</b>\n"
    for predmet in await obj.information_letter_for_parents():
        text += f"\n<i>{predmet[0]}</i>: <code>{predmet[1].replace('&nbsp;', '⁉️')}</code>"
    await message.reply(text)
    await obj.close()
