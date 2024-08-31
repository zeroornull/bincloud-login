import json
import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
from datetime import datetime, timedelta
import aiofiles
import random
import requests
import os

# 从环境变量中获取 Telegram Bot Token 和 Chat ID
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def format_to_iso(date):
    """格式化日期为 ISO 格式"""
    return date.strftime('%Y-%m-%d %H:%M:%S')


async def delay_time(ms):
    """延迟函数"""
    await asyncio.sleep(ms / 1000)


async def login(page, username, password):
    """执行登录操作"""
    serviceName = 'bincloud'
    try:
        url = 'https://www.bincloud.top/index.php?rp=/login'
        await page.goto(url)

        # 等待输入框和按钮加载完成
        await page.waitForSelector('#inputEmail', timeout=10000)
        await page.waitForSelector('#inputPassword', timeout=10000)
        await page.waitForSelector('#login', timeout=10000)

        await page.type('#inputEmail', username)
        await page.type('#inputPassword', password)

        login_button = await page.querySelector('#login')
        if login_button:
            await login_button.click()
        else:
            raise Exception('无法找到登录按钮')

        # 等待导航或检查登录成功
        await page.waitForNavigation(timeout=15000)

        # 检查登录状态并查找注销按钮
        is_logged_in = await page.evaluate('''() => {
            const logoutButton = document.getElementById('Secondary_Navbar-Account-Logout');
            return logoutButton !== null;
        }''')

        # 如果找到注销按钮，则点击它
        if is_logged_in:
            await page.click('#Secondary_Navbar-Account-Logout')

        return is_logged_in

    except TimeoutError as e:
        print(f'{serviceName}账号 {username} 登录时超时: {e}')
        return False
    except Exception as e:
        print(f'{serviceName}账号 {username} 登录时出现错误: {e}')
        return False


async def main():
    global message
    message = 'bincloud 自动化脚本运行\n'

    # 创建浏览器实例
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])

    try:
        # 读取账号信息
        async with aiofiles.open('accounts.json', mode='r', encoding='utf-8') as f:
            accounts_json = await f.read()
        accounts = json.loads(accounts_json)
    except Exception as e:
        print(f'读取 accounts.json 文件时出错: {e}')
        return

    # 登录所有账号
    for account in accounts:
        page = await browser.newPage()
        username = account['username']
        password = account['password']

        is_logged_in = await login(page, username, password)

        if is_logged_in:
            now_utc = format_to_iso(datetime.utcnow())
            now_beijing = format_to_iso(datetime.utcnow() + timedelta(hours=8))
            success_message = f'bincloud账号 {username} 于北京时间 {now_beijing}（UTC时间 {now_utc}）登录成功！'
            message += success_message + '\n'
            print(success_message)
        else:
            message += f'bincloud账号 {username} 登录失败，请检查账号和密码是否正确。\n'
            print(f'bincloud账号 {username} 登录失败，请检查账号和密码是否正确。')

        delay = random.randint(1000, 8000)
        await delay_time(delay)
        await page.close()

    message += '所有bincloud账号登录完成！'
    await send_telegram_message(message)
    print('所有bincloud账号登录完成！')

    # 关闭浏览器实例
    await browser.close()


async def send_telegram_message(message):
    """发送消息到 Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"发送消息到Telegram失败: {response.text}")
    except Exception as e:
        print(f"发送消息到Telegram时出错: {e}")


if __name__ == '__main__':
    asyncio.run(main())
