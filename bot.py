import asyncio
from asyncio import sleep
from random import uniform
import json
import os

import aiogram
from aiogram import types, Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

import aiosqlite

import config

class UserState(StatesGroup):

    wait_24_hours = State()
    wait_screenshot_with_review = State()
    confirm_send_screenshot_with_review = State()
    screenshot_with_review_sent = State()
    corresp_with_admin_started = State()

class AdminState(StatesGroup):

    wait_reviews = State()
    wait_message_for_mailing = State()
    confirm_message_for_mailing = State()
    corresp_with_user_started = State()
    confirm_final_corresp_with_user = State()

with open("offer_to_start_a_conversation_sent_admin.txt", "w", encoding = "utf-8") as file:

    file.write("False")
    offer_to_start_a_conversation_sent_admin = "False"

bot = Bot(token=config.bot_token)
dp = Dispatcher(bot, storage=JSONStorage("data.json"))

db = aiosqlite.connect("users.db")

async def create_table():

    global db

    await db

    await db.execute("""CREATE TABLE IF NOT EXISTS users(
           user_id INT);
    """)

    await db.commit()
