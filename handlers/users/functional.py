import re

import aiogram.utils.exceptions
import configcatclient
import pendulum
from aiogram import types
from aiogram.dispatcher.filters import Text
from wand.image import Image

import config
from loader import dp, bot
from utils.db_api import database
from utils.misc.throttling import rate_limit
from utils.sgo_api import Sgo

config = configcatclient.create_client(config.cat_keys.TELEGRAM)


def sort_lessons(elem):
    return elem['startTime']


@rate_limit(config.get_value('sgo_rate_limit', 0), 'timetable')
@dp.message_handler(Text('Получить расписание', ignore_case=True), user_with_account=True)
async def start_with_account(message: types.Message):
    user = await database.get_user(user_id=message.chat.id)
    await message.answer("Ожидайте, подготавливаю данные.")
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


notify_on_homework = types.InlineKeyboardButton('❌Выключить домашниe задания❌', callback_data='homework_notifications')
notify_off_homework = types.InlineKeyboardButton('✅Включить домашниe задания✅', callback_data='homework_notifications')
notify_on_marks = types.InlineKeyboardButton('❌Выключить оценки❌', callback_data='mark_notifications')
notify_off_marks = types.InlineKeyboardButton('✅Включить оценки✅', callback_data='mark_notifications')


async def gen_settings_message(chat_id):
    user = await database.get_user(user_id=chat_id)
    markup = types.InlineKeyboardMarkup()
    if user['homework_notifications']:
        markup.add(notify_on_homework)
    else:
        markup.add(notify_off_homework)

    if user['mark_notifications']:
        markup.add(notify_on_marks)
    else:
        markup.add(notify_off_marks)

    return {
        'text': 'Настройки',
        'reply_markup': markup
    }


@dp.message_handler(Text('Настройки', ignore_case=True), user_with_account=True)
async def settings_handler(message: types.Message):
    await message.answer(**(await gen_settings_message(message.chat.id)))


@dp.callback_query_handler(user_with_account=True)
async def queries_handler(query: types.CallbackQuery):
    user = await database.get_user(user_id=query.from_user.id)
    if query.data in ['homework_notifications', 'mark_notifications']:
        await database.query(
            f"UPDATE users SET {query.data} = ? WHERE id = ?",
            [not user[query.data], user['id']]
        )
        settings_message = await gen_settings_message(query.from_user.id)
        try:
            await bot.edit_message_text(
                **settings_message,
                chat_id=query.from_user.id,
                message_id=query.message.message_id
            )
        except aiogram.utils.exceptions.MessageCantBeEdited:
            await bot.send_message(
                **settings_message,
                chat_id=query.from_user.id
            )
    await query.answer()
