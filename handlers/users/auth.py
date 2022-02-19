from hashlib import md5

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from handlers.users.start import start_with_account
from loader import dp
from states import SetupAccount
from utils import sgo_api as city_data
from loader import bot
from utils.db_api import database
from utils.sgo_api import Sgo
from utils.sgo_api.exceptions import LoginError


@dp.message_handler(user_with_account=True, commands=['auth'])
async def alredy_authenticated(message: types.Message):
    await message.answer(
        "Вы уже авторизированы!\n"
        "Нечего вам тут делать."
    )


@dp.message_handler(user_with_account=False, commands=['auth'])
async def start_auth(message: types.Message):
    await message.answer("Окей, сейчас начнем авторизацию на sgo.rso23.ru!")
    await SetupAccount.city.set()
    await message.answer(
        "Введите город Краснодарского края:",
        reply_markup=types.ReplyKeyboardMarkup([[types.KeyboardButton('Отмена')]], resize_keyboard=True)
    )


@dp.message_handler(Text(equals='Отмена', ignore_case=True), state=SetupAccount)
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply(
        'Отменено!\n'
        'Для того чтобы начать с начала нажмите: /auth',
        reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message_handler(state=SetupAccount.city)
async def set_city_text(message: types.Message, state: FSMContext):
    cities = city_data.search_city(message.text)
    if not cities:
        await message.reply('Увы, мы не смогли найти таких городов по Краснодарскому краю!\nПроверьте опечатки!')
    elif len(cities) <= 10:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(*[
            types.InlineKeyboardButton(text=city['city']['name'], callback_data=city['city']['name']) for city in cities
        ])
        await message.reply(
            "Мы нашли несколько городов!\n"
            "Выберите свой город ниже.\n"
            "(Если вашего города нету, попробуйте поискать еще раз.)",
            reply_markup=markup
        )
    else:
        await message.reply('Мы нашли слишком много городов по Краснодарскому краю!\nВведите конкретнее!')


@dp.callback_query_handler(state=SetupAccount.city)
async def set_city_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    city = city_data.search_city(query.data)[0]
    async with state.proxy() as data:
        data['city'] = city
    await SetupAccount.next()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(*[
        types.InlineKeyboardButton(text=org['name'], callback_data=org['name']) for org in city['city']['oo_types']
    ])
    await bot.send_message(
        query.from_user.id,
        f'Город успешно установлен!\n'
        f'Теперь надо выбрать тип образовательной организации.\n',
        reply_markup=markup
    )


@dp.callback_query_handler(state=SetupAccount.org_type)
async def set_org_type_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    async with state.proxy() as data:
        data['org_type'] = city_data.search_orgs_by_city(data['city']['city'], query.data)
    await SetupAccount.next()
    await bot.send_message(
        query.from_user.id,
        'Так, сейчас будем искать твою образовательную организацию!\n'
        'Введи ключевое слово или номер своей школы, а мы что-нибудь подыщем!'
    )


@dp.message_handler(state=SetupAccount.org_id)
async def set_org_id_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        schools = city_data.search_schools(data['org_type']['orgs'], message.text)
    if not schools:
        await message.reply('Увы, бот не нашел учебных учереждений по вашему запросу, пропробуйте еще раз.')
    elif len(schools) <= 10:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(*[
            types.InlineKeyboardButton(text=school['name'], callback_data=school['id']) for school in schools
        ])
        await message.reply(
            "Отлично, выберите свое учебное учереждение из списка ниже!\n"
            "Если это не ваша школа, введите название школы еще раз.",
            reply_markup=markup
        )
    else:
        await message.reply("Мы нашли слишком много учебных учереждений, введите конкретнее!")


@dp.callback_query_handler(state=SetupAccount.org_id)
async def set_org_id_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    async with state.proxy() as data:
        data['org_id'] = city_data.search_schools(data['org_type']['orgs'], int(query.data))[0]
    await SetupAccount.next()
    await bot.send_message(
        query.from_user.id,
        "Введите логин:"
    )


@dp.message_handler(state=SetupAccount.username)
async def set_username_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
    await SetupAccount.next()
    await message.reply(
        f'Введите пароль:'
    )


@dp.message_handler(state=SetupAccount.password)
async def set_password_text(message: types.Message, state: FSMContext):
    await message.delete()
    await message.answer(
        'Я получил логин и пароль.\n'
        'Сейчас попробую зайти в ваш дневник.',
        reply_markup=types.ReplyKeyboardRemove()
    )

    async with state.proxy() as data:
        tmp_account = {
            'id': -1,
            'name': 'tmp',
            'state_id': data['city']['state_id'],
            'city_id': data['city']['city']['id'],
            'org_type': data['org_type']['id'],
            'org_id': data['org_id']['id'],
            'username': data['username'],
            'password': md5(message.text.encode()).hexdigest(),
            'session': None
        }
    await state.finish()
    try:
        account_id = await database.get_account(
            org_id=tmp_account['org_id'], username=tmp_account['username'], password=tmp_account['password']
        )
        if not account_id:
            obj = await Sgo(tmp_account)
            account_id = await database.create_account(
                obj.account['session']['accountInfo']['user']['name'],
                obj.account['state_id'],
                obj.account['city_id'],
                obj.account['org_type'],
                obj.account['org_id'],
                obj.account['username'],
                obj.account['password'],
                obj.account['session']
            )
        else:
            account_id = account_id['id']
        await database.update_user_account_id(message.chat.id, account_id)
        await start_with_account(message)
    except LoginError:
        await bot.send_message(
            message.chat.id,
            f'Не получилось зайти в аккаунт!\n'
            f'Повторите процедуру с начала!\n'
            f'/auth'
        )
    except Exception as err:
        print(err)
        await bot.send_message(
            message.chat.id,
            'Произошла непредвиденная ошибка!\n'
            'Повторите процедуру с начала!\n'
            '/auth'
        )
# try:
#     sgo_obj = await Sgo(username, password)
#     login_resp = await sgo_obj.login(user.state_id, user.city_id, user.org_type_id, user.org_id)
#     if login_resp[0]:
#         await user.set_auth_session(str(sgo_obj.auth_session))
#         await bot.send_message(
#             query.from_user.id,
#             f'Успешно вошел в аккаунт [{sgo_obj.user["name"]}].'
#         )
#         await user.set_login_data(username, password)
#         await state.finish()
#     else:
#         await bot.send_message(
#             query.from_user.id,
#             f'Не получилось зайти в аккаунт!\nНачнем ввод логина пароля сначала.\nВведите логин:'
#         )
#         await SetupLoginData.username.set()
#     await sgo_obj.close()
# except Exception as err:
#     print(err)
#     await bot.send_message(
#         query.from_user.id,
#         'Не удалось подключиться к серверу sgo.rso23.ru.'
#     )
#     await state.finish()
