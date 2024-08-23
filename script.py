import uuid
import asyncio
import aiohttp
import time

DEBUG = False
MAX_RETRIES = 20
OUTPUT_FILE = "promo_codes.txt"
LOOP_DELAY = 2 * 60  # Delay between complete cycles in seconds (2 minutes)

games = {
    "My Clone Army": {
        "appToken": "74ee0b5b-775e-4bee-974f-63e7f4d5bacb",
        "promoId": "fe693b26-b342-4159-8808-15e3ff7f8767",
        "delay": 120,
        "retry": 20,
        "keys": 4,
    },
    "Riding Extreme 3D": {
        "appToken": "d28721be-fd2d-4b45-869e-9f253b554e50",
        "promoId": "43e35910-c168-4634-ad4f-52fd764a843f",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
    "Chain Cube 2048": {
        "appToken": "d1690a07-3780-4068-810f-9b5bbf2931b2",
        "promoId": "b4170868-cef0-424f-8eb9-be0622e8e8e3",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
    "Train Miner": {
        "appToken": "82647f43-3f87-402d-88dd-09a90025313f",
        "promoId": "c4480ac7-e178-4973-8061-9ed5b2e17954",
        "delay": 120,
        "retry": 20,
        "keys": 4,
    },
    "Merge Away": {
        "appToken": "8d1cc2ad-e097-4b86-90ef-7a27e19fb833",
        "promoId": "dc128d28-c45b-411c-98ff-ac7726fbaea4",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
    "Twerk Race 3D": {
        "appToken": "61308365-9d16-4040-8bb0-2f4a4c69074c",
        "promoId": "61308365-9d16-4040-8bb0-2f4a4c69074c",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
    "POLY": {
        "appToken": "2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71",
        "promoId": "2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
    "MOW": {
        "appToken": "ef319a80-949a-492e-8ee0-424fb5fc20a6",
        "promoId": "ef319a80-949a-492e-8ee0-424fb5fc20a6",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
    "MUD": {
        "appToken": "8814a785-97fb-4177-9193-ca4180ff9da8",
        "promoId": "8814a785-97fb-4177-9193-ca4180ff9da8",
        "delay": 20,
        "retry": 20,
        "keys": 4,
    },
}


def debug(*args):
    if DEBUG:
        print(*args)


def info(*args):
    print(*args)


async def fetch_api(session, path, auth_token=None, body=None):
    url = f"https://api.gamepromo.io{path}"
    headers = {}

    if auth_token:
        headers["authorization"] = f"Bearer {auth_token}"

    if body is not None:
        headers["content-type"] = "application/json"

    async with session.post(url, headers=headers, json=body) as response:
        debug(f"URL: {url}, Headers: {headers}, Body: {body}")
        if response.status != 200:
            error_message = await response.text()
            debug(f"Error {response.status}: {error_message}")
            raise Exception(f"{response.status} {response.reason}: {error_message}")

        return await response.json()


async def get_promo_code(session, game_key):
    game_config = games[game_key]
    client_id = str(uuid.uuid4())

    try:
        login_client_data = await fetch_api(
            session,
            "/promo/login-client",
            body={
                "appToken": game_config["appToken"],
                "clientId": client_id,
                "clientOrigin": "ios",
            },
        )
    except Exception as e:
        info(f"Failed to login client for {game_key}: {e}")
        return None

    auth_token = login_client_data.get("clientToken")
    if not auth_token:
        info(f"Failed to obtain auth token for {game_key}")
        return None

    promo_code = None

    for _ in range(MAX_RETRIES):
        try:
            await asyncio.sleep(game_config["delay"])
            register_event_data = await fetch_api(
                session,
                "/promo/register-event",
                auth_token,
                body={
                    "promoId": game_config["promoId"],
                    "eventId": str(uuid.uuid4()),
                    "eventOrigin": "undefined",
                },
            )
        except Exception as e:
            info(f"Failed to register event for {game_key}: {e}")
            await asyncio.sleep(game_config["retry"])
            continue

        if not register_event_data.get("hasCode"):
            await asyncio.sleep(game_config["retry"])
            continue

        try:
            create_code_data = await fetch_api(
                session,
                "/promo/create-code",
                auth_token,
                body={
                    "promoId": game_config["promoId"],
                },
            )
            promo_code = create_code_data.get("promoCode")
            break
        except Exception as e:
            info(f"Failed to create code for {game_key}: {e}")
            await asyncio.sleep(game_config["retry"])

    if promo_code is None:
        info(f"Unable to get {game_key} promo after {MAX_RETRIES} retries")

    return promo_code


async def main():
    async with aiohttp.ClientSession() as session:
        with open(OUTPUT_FILE, "a") as f:  # ('a' - append mode)
            while True:
                for game_key in games:
                    promo_codes = []
                    for _ in range(games[game_key]["keys"]):
                        code = await get_promo_code(session, game_key)
                        if code:
                            info(f"{code}")
                            promo_codes.append(f"{code}\n")
                    f.writelines(promo_codes)
                info(f"End of cycle. Wait {LOOP_DELAY} second before next cycle.")
                await asyncio.sleep(LOOP_DELAY)


if __name__ == "__main__":
    asyncio.run(main())
