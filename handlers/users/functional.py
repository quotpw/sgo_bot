import configcatclient
from aiogram import types
from aiogram.dispatcher.filters import Text

from utils.db_api import database
from loader import dp
from utils.sgo_api import Sgo
import pendulum
from utils.misc.throttling import rate_limit
from wand.image import Image

config = configcatclient.create_client('XvnZCMXRUk2AYlhFwpHeCg/0oW9esHgO0iliYuGz8jTcQ')


def sort_lessons(elem):
    return elem['startTime']


@rate_limit(config.get_value('sgo_rate_limit', 0), 'timetable')
@dp.message_handler(Text('Получить рассписание', ignore_case=True), user_with_account=True)
async def start_with_account(message: types.Message):
    user = await database.get_user(user_id=message.chat.id)
    await message.answer("Ожидайте, подготоваливаю данные.")
    obj = await Sgo(await database.get_account(id=user['account_id']))
    date = pendulum.now()
    timetable = await obj.timetable(date, check=True)

    lessons = None
    day_time = None
    for week in timetable['weekDays']:
        day_time = pendulum.parse(week['date'])
        day_time.add(days=1)
        if date < day_time:
            lessons = week['lessons']
            break
    lessons.sort(key=sort_lessons)
    day_time.subtract(days=1)
    #   /mnt/c/Users/edman/Desktop/sgo_timetable.svg
    svg_photo = open('handlers/users/timetable.svg', encoding='utf-8').read() \
        .replace('week_day_date', day_time.format('dddd, D MMMM YYYY г.', 'ru'))

    for i in range(7):
        ln = i + 1
        try:
            lesson = lessons[i]
            lesson_name = lesson['subjectName']
            if len(lesson_name) > 16:
                lesson_name = lesson_name[:16] + '...'
            svg_photo = svg_photo \
                .replace(f'subjectName{ln}', lesson_name) \
                .replace(f'startTime{ln}', lesson['startTime']) \
                .replace(f'endTime{ln}', lesson['endTime'])
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
                svg_photo = svg_photo.replace(f'assignment{ln}', assignments)
            else:
                svg_photo = svg_photo.replace(f'assignment{ln}', '')
        except:
            svg_photo = svg_photo \
                .replace(f'subjectName{ln}', '') \
                .replace(f'startTime{ln} - endTime{ln}', '') \
                .replace(f'assignment{ln}', '') \
                .replace(f'>{ln}<', '><')

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
