import requests
import time
import os
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
PLACE_ID = 131772435103692 # this is a place holder, change the id to the id of the game your trying to track (this placeholder legend cuz its pet orby)
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK") 
ERROR_WEBHOOK_URL = os.environ.get("ERROR_WEBHOOK") 
TRACKER_ENABLED = os.environ.get("TRACKER_ENABLED", "true").lower() == "true"
CHECK_INTERVAL = 60   

# --- RENDER CUSTOMIZATION VARIABLES ---
BOT_NAME = os.environ.get("BOT_NAME", "Pet Orby Tracker")

JOIN_TITLE = os.environ.get("JOIN_TITLE", "📈 Player Joined")
DEFAULT_JOIN = "Someone joined the game. There are now **{count}** players online."
JOIN_TEXT = os.environ.get("JOIN_TEXT", DEFAULT_JOIN)

LEAVE_TITLE = os.environ.get("LEAVE_TITLE", "📉 Player Left")
DEFAULT_LEAVE = "Someone left the game. There are now **{count}** players online."
LEAVE_TEXT = os.environ.get("LEAVE_TEXT", DEFAULT_LEAVE)

DEFAULT_FOOTER = "👁️ Visits: {visits} | 👍 Rating: {ratio} ({likes} Likes)"
FOOTER_TEXT = os.environ.get("FOOTER_TEXT", DEFAULT_FOOTER)

def parse_hex_color(hex_str, default_int):
    if not hex_str: 
        return default_int
    try:
        return int(hex_str.replace("#", ""), 16)
    except ValueError:
        return default_int

JOIN_COLOR = parse_hex_color(os.environ.get("JOIN_COLOR"), 0x00FF00) 
LEAVE_COLOR = parse_hex_color(os.environ.get("LEAVE_COLOR"), 0xFF0000) 


# What's the matter, Mags... You wanna live forever?
app = Flask(__name__)

@app.route('/')
def home():
    status = "AWAKE" if TRACKER_ENABLED else "PAUSED"
    return f"Tracker web server is online. Tracking status: {status}"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- TRACKER LOGIC ---
def get_universe_id(place_id):
    url = f"https://apis.roproxy.com/universes/v1/places/{place_id}/universe"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("universeId")
    return None

def get_game_icon(place_id):
    url = f"https://thumbnails.roproxy.com/v1/places/gameicons?placeIds={place_id}&returnPolicy=PlaceHolder&size=512x512&format=Png&isCircular=false"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data and data[0].get("state") == "Completed":
                return data[0].get("imageUrl")
    except Exception:
        pass
    return None

def get_game_votes(universe_id):
    timestamp = int(time.time())
    url = f"https://games.roproxy.com/v1/games/{universe_id}/votes?_={timestamp}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            up = data.get("upVotes", 0)
            down = data.get("downVotes", 0)
            total = up + down
            
            # Calculates the percentage
            ratio = int((up / total) * 100) if total > 0 else 0
            return up, f"{ratio}%"
        else:
            print(f"⚠️ somethin wrong with api {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ grabbing votes failed: {e}")
        
    return 0, "N/A"

def get_game_data(universe_id):
    timestamp = int(time.time())
    url = f"https://games.roproxy.com/v1/games?universeIds={universe_id}&_={timestamp}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        if data:
            playing = data[0].get("playing", 0)
            visits = data[0].get("visits", 0)
            return playing, visits, 200
    else:
        print(f"⚠️ somethin wrong with api {response.status_code}")
        
    return None, None, response.status_code

def format_message(template, count, visits, likes, ratio):
    text = template.replace("{count}", str(count))
    text = text.replace("{visits}", f"{visits:,}") 
    text = text.replace("{likes}", f"{likes:,}")
    text = text.replace("{ratio}", str(ratio))
    return text

def send_webhook(target_url, title, description, color, thumbnail_url=None, footer_text=None):
    if not target_url:
        return 
        
    clean_url = target_url.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"
    }
    
    embed = {
        "title": title,
        "description": description,
        "color": color
    }
    
    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}
        
    if footer_text:
        embed["footer"] = {"text": footer_text}
        
    payload = {
        "username": BOT_NAME, 
        "embeds": [embed]
    }
    
    try:
        response = requests.post(clean_url, json=payload, headers=headers)
        if response.status_code in [200, 204]:
            print(f"[{time.strftime('%X')}] ✅ webhook sent")
        else:
            print(f"[{time.strftime('%X')}] ❌ webhook not sent (the webhook could have gotten sent and this is some other error) {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ somethin up with ur proxy: {e}")

def main():
    print(f"Fetching universe ID for Place {PLACE_ID}...")
    universe_id = get_universe_id(PLACE_ID)
    
    if not universe_id:
        print("Failed to get Universe ID. Double-check your Place ID.")
        return

    print("grabbing game thumbnail")
    game_icon_url = get_game_icon(PLACE_ID)
    if game_icon_url:
        print("✅ game thumbnail succesfully grabbed")

    keep_alive()
    print("game tracker enabled.....noob")
    
    previous_count, _, _ = get_game_data(universe_id)
    if previous_count is None:
        previous_count = 0
        
    was_rate_limited = False 

    while True:
        time.sleep(CHECK_INTERVAL) 
        
        if not TRACKER_ENABLED:
            continue 
            
        current_count, visits, status_code = get_game_data(universe_id)
        
        if status_code == 429: 
            if not was_rate_limited:
                send_webhook(ERROR_WEBHOOK_URL, "⚠️ ur getting ratelimited noob, "roblox is ratelimiting the bot.", 0xFFA500)
                was_rate_limited = True
            continue 
            
        if status_code == 200 and was_rate_limited:
            send_webhook(ERROR_WEBHOOK_URL, "✅ ur not ratelimited anymore pro", 0x00FF00)
            was_rate_limited = False
            
        if current_count is None:
            continue 
            
        if current_count > previous_count:
            likes, ratio = get_game_votes(universe_id)
            
            # Formats both the body and the footer
            formatted_text = format_message(JOIN_TEXT, current_count, visits, likes, ratio)
            formatted_footer = format_message(FOOTER_TEXT, current_count, visits, likes, ratio)
            
            send_webhook(WEBHOOK_URL, JOIN_TITLE, formatted_text, JOIN_COLOR, game_icon_url, formatted_footer)
            time.sleep(5) 
            
        elif current_count < previous_count:
            likes, ratio = get_game_votes(universe_id)
            
            formatted_text = format_message(LEAVE_TEXT, current_count, visits, likes, ratio)
            formatted_footer = format_message(FOOTER_TEXT, current_count, visits, likes, ratio)
            
            send_webhook(WEBHOOK_URL, LEAVE_TITLE, formatted_text, LEAVE_COLOR, game_icon_url, formatted_footer)
            time.sleep(5) 
            
        previous_count = current_count

if __name__ == "__main__":
    main()