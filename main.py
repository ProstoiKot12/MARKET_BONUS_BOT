import asyncio

from bot import *
from user_handlers import *
from admin_handlers import *
import config

if __name__ == '__main__':

    print("Work")

    async def main():

        await create_table()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())

    executor.start_polling(dp)
