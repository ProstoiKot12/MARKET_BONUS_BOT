

from bot import *

start_keyboard = types.InlineKeyboardMarkup(row_width=1)
start_keyboard.add(types.InlineKeyboardButton(text="Отзыв опубликован", callback_data="send_review"))

confirm_send_screenshot_keyboard = types.InlineKeyboardMarkup(row_width=1)
confirm_send_screenshot_keyboard.add(types.InlineKeyboardButton(text="Да", callback_data="yes"))
confirm_send_screenshot_keyboard.add(types.InlineKeyboardButton(text="Нет", callback_data="no"))

@dp.message_handler(lambda message: message.from_user.id != config.admin_id,
commands = "start", state = UserState.corresp_with_admin_started)
async def start_for_users_with_error(message: types.Message):

    await message.answer("Пожалуйста, дождитесь окончания переписки с менеджером")

@dp.message_handler(lambda message: message.from_user.id != config.admin_id, commands = "start")
async def start_for_users(message: types.Message,  state: FSMContext):

    cursor = await db.execute(f"SELECT * FROM users WHERE user_id = {message.from_user.id}")
    row = await cursor.fetchall()

    if row is None:

        await db.execute("INSERT INTO users VALUES(?);", [message.from_user.id])
        await db.commit()

    await message.answer("Привет, получи БОНУС на телефон или на карту, выполнив 3 действия:\n"
                   "1. Оставьте отзыв на товар\n"
                   "2. Пришлите скриншот ОПУБЛИКОВАННОГО отзыва через 24 часа\n"
                   "3. Оставьте номер телефона который привязан к карте и какой банк."
                   "Если вам нужно пополнить баланс мобильного телефона, то напишите имя мобильного оператора и сам номер телефона.")

    await sleep(0.02)

    await message.answer("Для начала нужно оставить отзыв на МАРКЕТПЛЕЙСЕ.")

    await sleep(0.02)

    await message.answer("Сообщи нам с помощью кнопки ниже, когда отзыв будет опубликован и мы сообщим Вам о дальнейшем действии",
    reply_markup = start_keyboard)

@dp.callback_query_handler(text = "send_review")
async def callback_for_send_review_button(callback, state: FSMContext):

    await callback.answer()

    await callback.message.answer(
    "Теперь нужно подождать 24 часа, чтобы убедиться, что модераторы маркетплейса не удалят и не исключат отзыв из рейтинга.\n"
    "Я напомню через 24 часа, что нужно прислать скриншот отзыва.")

    await UserState.wait_24_hours.set()
    await sleep(86400)

    await callback.message.answer(
    "Пришло время прислать скриншот вашего отзыва.\n"
    "Нужно зайти на страницу товара, найти свой отзыв и сделать скриншот.\n"
    "P.S. Если по какой-то причине модераторы маркетплейса удалили и исключили Ваш отзыв из рейтинга, "
    "то мы БОНУС не переводим, мы переводим только за опубликованные отзывы.")

    await UserState.wait_screenshot_with_review.set()

@dp.callback_query_handler(text = "send_review", state = UserState.screenshot_with_review_sent)
async def third_callback_for_send_review_button(callback):

    await callback.answer()

    await callback.message.answer("Бот: пожалуйста, подождите, пока менеджер проверит уже отправленный скриншот")

@dp.callback_query_handler(text = "send_review", state = UserState.corresp_with_admin_started)
async def second_callback_for_send_review_button(callback):

    await callback.answer()

    await callback.message.answer("Бот: скриншот с отзывом можно будет отправить после того, как менеджер завершит с вами переписку")

@dp.message_handler(content_types = ["photo"], state = UserState.wait_screenshot_with_review)
async def confirm_send_review(message: types.Message, state: FSMContext):

    await state.update_data(current_photo_id = message.photo[-1].file_id,
                            current_user_id = message.from_user.id,
                            current_user_username = message.from_user.username,
                            current_chat_id = message.chat.id)

    await message.answer("Вы уверены, что отправили верный скриншот?", reply_markup = confirm_send_screenshot_keyboard)

@dp.callback_query_handler(text = "no", state = UserState.wait_screenshot_with_review)
async def accept_send_review(callback):

    await callback.answer()
    await callback.message.delete()

    await callback.message.answer("Пожалуйста, пришлите верный скриншот")

@dp.callback_query_handler(text = "yes", state = UserState.wait_screenshot_with_review)
async def get_review(callback, state: FSMContext):

    await UserState.screenshot_with_review_sent.set()

    global offer_to_start_a_conversation_sent_admin

    await callback.answer()
    await callback.message.delete()

    state_data = await state.get_data()

    current_user_id = state_data["current_user_id"]
    current_user_username = state_data["current_user_username"]
    current_chat_id = state_data["current_chat_id"]

    start_corresp_with_user_keyboard = types.InlineKeyboardMarkup(row_width=1)
    start_corresp_with_user_keyboard.add(types.InlineKeyboardButton(text="Начать переписку",
    callback_data =
    f"s_c_w_{current_user_id}_{current_user_username}_{current_chat_id}"))

    await callback.message.answer(
    "Если у вас есть ещё один аккаунт на маркетплейсе, "
    'то Вы можете опубликовать ещё один ОТЗЫВ и после нажать на кнопку "Отзыв опубликован"',
    reply_markup = start_keyboard)

    await callback.message.answer("Менеджер свяжется с вами в течение нескольких часов.")

    with open("offer_to_start_a_conversation_sent_admin.txt", "r", encoding = "utf-8") as file:

        offer_to_start_a_conversation_sent_admin = file.read()

    while True:

        if "False" in offer_to_start_a_conversation_sent_admin:

            await bot.send_photo(config.admin_id, photo = state_data["current_photo_id"],
            caption = f"Пользователь @{current_user_username} прислал отзыв",
            reply_markup = start_corresp_with_user_keyboard)

            break

        else:

            await sleep(uniform(5, 15))

            with open("offer_to_start_a_conversation_sent_admin.txt", "r", encoding = "utf-8") as file:

                offer_to_start_a_conversation_sent_admin = file.read()

@dp.message_handler(content_types = types.ContentTypes.ANY, state = UserState.wait_screenshot_with_review)
async def get_review(message: types.Message):

    await message.answer("Пожалуйста, отправьте один скриншот, нажав на кнопку 'Сжать изображение'")

@dp.message_handler(content_types = types.ContentTypes.ANY, state = UserState.corresp_with_admin_started)
async def send_message_to_admin(message: types.Message):

    try:

        await bot.send_message(config.admin_id, text = message.text)

    except:

        await message.answer(
        f"Бот: Во время отправки сообщения "
        "произошла непредвиденная ошибка, попробуйте ещё раз, отправляйте только текст!")
