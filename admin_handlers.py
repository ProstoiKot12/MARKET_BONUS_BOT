from asyncio import sleep

from bot import *
from user_handlers import get_review

import config

final_corresp_with_user_keyboard = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True)
final_corresp_with_user_keyboard.add("Завершить переписку")

cancel_start_mailing_keyboard = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True)
cancel_start_mailing_keyboard.add("Отменить рассылку")

@dp.message_handler(lambda message: message.from_user.id == config.admin_id,
commands = "start", state = AdminState.corresp_with_user_started)
@dp.message_handler(lambda message: message.from_user.id == config.admin_id,
commands = "start", state = AdminState.confirm_final_corresp_with_user)
async def start_for_admin_with_error(message: types.Message,  state: FSMContext):

    await message.answer("Пожалуйста, завершите переписку с пользователем")

@dp.message_handler(lambda message: message.from_user.id == config.admin_id, commands = "start")
async def start_for_admin(message: types.Message,  state: FSMContext):

    await AdminState.wait_reviews.set()

    await message.answer("Вы админ")

@dp.callback_query_handler(lambda x: x.data.startswith("s_c_w_"), state = AdminState.wait_reviews)
async def start_corresp_with_user(callback, state: FSMContext):

    global offer_to_start_a_conversation_sent_admin

    await callback.answer()

    temp_cb_data = callback.data.replace("s_c_w_", "").split("_")

    current_user_id = int(temp_cb_data[0])

    if len(temp_cb_data) > 3:

        current_user_username = "".join(temp_cb_data[1:-1])
        current_chat_id = int(temp_cb_data[-1])

    else:

        current_user_username = temp_cb_data[1]
        current_chat_id = int(temp_cb_data[2])

    await AdminState.corresp_with_user_started.set()

    with open("offer_to_start_a_conversation_sent_admin.txt", "w", encoding = "utf-8") as file:

        file.write("True")
        offer_to_start_a_conversation_sent_admin = "True"

    user_state = dp.current_state(chat=current_chat_id, user=current_user_id)
    await user_state.set_state(UserState.corresp_with_admin_started)

    await callback.message.answer(
    f"Бот: Переписка с пользователем @{current_user_username} началась", reply_markup = final_corresp_with_user_keyboard)

    await bot.send_message(current_user_id, text = "Бот: Переписка с менеджером началась")

    await state.update_data(current_user_id = current_user_id,
                            current_user_username = current_user_username,
                            current_chat_id = current_chat_id)

@dp.callback_query_handler(lambda x: x.data.startswith("s_c_w_"), state = AdminState.corresp_with_user_started)
async def second_start_corresp_with_user(callback):

        await callback.message.answer("Бот: для начала завершите переписку с нынешним пользователем")

@dp.message_handler(text = "Завершить переписку", state = AdminState.corresp_with_user_started)
async def confirm_final_corresp_with_user(message: types.Message, state: FSMContext):

    confirm_final_corresp_with_user_keyboard = types.ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True)
    confirm_final_corresp_with_user_keyboard.add("Да")
    confirm_final_corresp_with_user_keyboard.add("Нет")

    data = await state.get_data()

    current_user_username = data["current_user_username"]

    await message.answer(f"Бот: Вы уверены, что хотите завершить переписку с пользователем @{current_user_username}?",
    reply_markup = confirm_final_corresp_with_user_keyboard)

    await AdminState.confirm_final_corresp_with_user.set()

@dp.message_handler(text = "Да", state = AdminState.confirm_final_corresp_with_user)
async def accept_final_corresp_with_user(message: types.Message, state: FSMContext):

    global offer_to_start_a_conversation_sent_admin

    data = await state.get_data()

    user_state = dp.current_state(chat=data["current_chat_id"], user=data["current_user_id"])

    await user_state.reset_data()
    await user_state.set_state(None)

    await AdminState.wait_reviews.set()

    with open("offer_to_start_a_conversation_sent_admin.txt", "w", encoding = "utf-8") as file:

        file.write("False")
        offer_to_start_a_conversation_sent_admin = "False"

    current_user_username = data["current_user_username"]

    await message.answer(f"Бот: Переписка с пользователем @{current_user_username} завершена",
    reply_markup = types.ReplyKeyboardRemove())

    await bot.send_message(data["current_user_id"], text = "Бот: Переписка с менеджером завершена")

@dp.message_handler(text = "Нет", state = AdminState.confirm_final_corresp_with_user)
async def cancel_final_corresp_with_user(message: types.Message, state: FSMContext):

    data = await state.get_data()

    await AdminState.corresp_with_user_started.set()

    current_user_username = data["current_user_username"]

    await message.answer(f"Бот: переписка с пользователем @{current_user_username} продолжается",
    reply_markup = final_corresp_with_user_keyboard)

@dp.message_handler(commands = "start_mailing", state = AdminState.wait_reviews)
async def start_mailing(message: types.Message):

    await AdminState.wait_message_for_mailing.set()

    await message.answer(f"Отправьте необходимое сообщение для рассылки", reply_markup = cancel_start_mailing_keyboard)

@dp.message_handler(text = "Отменить рассылку", state = AdminState.wait_message_for_mailing)
async def cancel_start_mailing(message: types.Message):

    await AdminState.wait_reviews.set()

    await message.answer(f"Рассылка отменена", reply_markup = types.ReplyKeyboardRemove())

@dp.message_handler(content_types = types.ContentTypes.ANY, state = AdminState.wait_message_for_mailing)
async def confirm_message_for_mailing(message: types.Message, state: FSMContext):

    await AdminState.confirm_message_for_mailing.set()

    if message.photo != []:

        await message.photo[-1].download(f"{message.photo[-1].file_id}.jpg")

        await state.update_data(required_message_for_mailing = f"📢<b>Рассылка</b>📢\n\n{message.caption}")
        await state.update_data(required_photo_for_mailing = f"{message.photo[-1].file_id}.jpg")

    else:

        await state.update_data(required_message_for_mailing = f"📢<b>Рассылка</b>📢\n\n{message.text}")
        await state.update_data(required_photo_for_mailing = None)

    confirm_message_for_mailing_keyboard = types.ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True)
    confirm_message_for_mailing_keyboard.add("Да")
    confirm_message_for_mailing_keyboard.add("Нет")

    await message.answer("Вы уверены, что в вашем сообщении нет ошибок?", reply_markup = confirm_message_for_mailing_keyboard)

@dp.message_handler(text = "Нет", state = AdminState.confirm_message_for_mailing)
async def change_message_for_mailing(message: types.Message, state: FSMContext):

    await AdminState.wait_message_for_mailing.set()

    await message.answer("Отправьте необходимое сообщение для рассылки", reply_markup = cancel_start_mailing_keyboard)

async def send_ad_with_photo(req_photo, text, cursor, message):

    sent_messages_сount = 0
    all_messages_count = 0

    async for row in cursor:

        photo = open(req_photo, "rb")

        try:

            await bot.send_photo(chat_id = row[0], photo=photo, caption = text, parse_mode = "HTML")

            sent_messages_сount += 1
            all_messages_count += 1

            await sleep(0.07)

        except aiogram.utils.exceptions.BadRequest:

            try:

                await sleep(uniform(1, 2))

                await bot.send_photo(chat_id = row[0], photo=photo, caption = text, parse_mode = "HTML")

                sent_messages_сount += 1
                all_messages_count += 1

            except:

                all_messages_count += 1

        except Exception as exc:

            print(exc)

            all_messages_count += 1

    await message.answer("""Рассылка завершена!\n"""
                        f"""Успешно отправленных сообщений: {sent_messages_сount}\n"""
                        f"""Всего отправлено сообщений: {all_messages_count}\n""")

    os.remove(req_photo)

async def send_ad_without_photo(text, cursor, message):

    sent_messages_сount = 0
    all_messages_count = 0

    async for row in cursor:

        try:

            await bot.send_message(row[0], text = text, parse_mode = "HTML")

            sent_messages_сount += 1
            all_messages_count += 1

            await sleep(0.07)

        except aiogram.utils.exceptions.BadRequest:

            try:

                await sleep(uniform(1, 2))

                await bot.send_message(row[0], text = text, parse_mode = "HTML")

                sent_messages_сount += 1
                all_messages_count += 1

            except:

                all_messages_count += 1

        except:

            all_messages_count += 1

    await message.answer("""Рассылка завершена!\n"""
                        f"""Успешно отправленных сообщений: {sent_messages_сount}\n"""
                        f"""Всего отправлено сообщений: {all_messages_count}\n""")

@dp.message_handler(text = "Да", state = AdminState.confirm_message_for_mailing)
async def mass_send_messages(message: types.Message, state: FSMContext):

    await AdminState.wait_reviews.set()

    state_data = await state.get_data()

    required_message = state_data["required_message_for_mailing"]
    required_photo = state_data["required_photo_for_mailing"]

    if "None" in required_message:

        required_message = "📢<b>Рассылка</b>📢"

    await message.answer("Рассылка началась", reply_markup = types.ReplyKeyboardRemove())

    cursor = await db.execute('SELECT * FROM users')

    if required_photo != None:

        await send_ad_with_photo(required_photo, required_message, cursor, message)

    else:

        await send_ad_without_photo(required_message, cursor, message)

@dp.message_handler(commands = "start_mailing", state = AdminState.confirm_final_corresp_with_user)
@dp.message_handler(commands = "start_mailing", state = AdminState.corresp_with_user_started)
async def print_error_after_start_mailing(message: types.Message):

    await message.answer("Для начала завершите переписку с пользователем")

@dp.message_handler(content_types = types.ContentTypes.ANY, state = AdminState.confirm_final_corresp_with_user)
@dp.message_handler(content_types = types.ContentTypes.ANY, state = AdminState.corresp_with_user_started)
async def send_message_to_user(message: types.Message, state: FSMContext):

    global offer_to_start_a_conversation_sent_admin

    data = await state.get_data()

    current_user_username = data["current_user_username"]

    try:

        await bot.send_message(data["current_user_id"], text = message.text)

    except aiogram.utils.exceptions.BotBlocked:

        user_state = dp.current_state(chat=data["current_chat_id"], user=data["current_user_id"])

        await user_state.reset_data()
        await user_state.set_state(None)

        await AdminState.wait_reviews.set()

        with open("offer_to_start_a_conversation_sent_admin.txt", "w", encoding = "utf-8") as file:

            file.write("False")
            offer_to_start_a_conversation_sent_admin = "False"

        await message.answer(f"Бот: Пользователь @{current_user_username} заблокировал бота, переписка с ним завершена",
        reply_markup = types.ReplyKeyboardRemove())

    except:

        await message.answer(
        f"Бот: Во время отправки сообщения пользователю @{current_user_username} "
        "произошла непредвиденная ошибка, попробуйте ещё раз, отправляйте только текст!")

@dp.message_handler(content_types = types.ContentTypes.ANY, state = AdminState.wait_reviews)
async def send_message_to_empty(message: types.Message, state: FSMContext):

    await message.answer("Бот: в данный момент у вас нет открытых переписок")
