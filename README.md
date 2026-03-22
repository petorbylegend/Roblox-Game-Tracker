### Welcome to my legend guide on how to setup my legend game tracker bot by me @jxper (legend guy)
---
## Step 1: Setup your webhooks
Before you host the bot you need to get your webhook links ready

1. create a webhook in your discord server settings and copy the URL.
2. standard discord webhook links often get blocked by hosting providers for me atleast (giving you a 403 error where the webhooks just randomly stop sending) you should route your webhook through a custom cloudflare Worker to fix this.
3. If you use a cloudflare proxy, it will sometimes send the webhook twice for some reason to prevent cloudflare from double sending simply add `?wait=true` to the very end of your webhook URL.
   * *Example:* `https://your-proxy.workers.dev/api/webhooks/123/abc?wait=true`
---
## Step 2: create a github repository
you need to create a github rerepository for your hosting site
1. download "maintracker.py" and "requirements"
2. create a github account if you dont have one
3. click on your profile picture then click repositories
4. click on the green "new" button
5. give it a name and click on the green "create repository"
6. go onto your repository and click add files
7. add the "maintracker.py" and "requirements" files
---
## Step 2: Host on render
i recommend hosting this bot on a platform like render. (https://render.com) legend website

1. create a new web service on render and link your gitHub repo.
2. when setting up the service make sure your start command is set to:
   `python -u maintracker.py`
   *(The `-u` is really important it makes sure all the print statements get sent directly to the render dashboard logs so you can see what the bot is doing)*
---
## Step 3: Configure core variables
In your render dashboard go to the environment tab You need to add these three required variables to make your bot actually work:

| Variable | What you need to put |
| :--- | :--- |
| `DISCORD_WEBHOOK` | your proxied Discord Webhook URL (ending in `?wait=true`) |
| `ERROR_WEBHOOK`   | a separate Webhook URL where the bot will silently log API rate limits so it doesnt spam your main channel. |
| `TRACKER_ENABLED` | set to `true` to run the bot (You can change this to `false` later if you ever need a off switch). |

---

## Step 4: customize your messages (optional)
you can add any of these optional environment variables to render to change how the bot looks and talks if you leave these blank the bot will just use the default messages

### Viusal variables
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `BOT_NAME` | Game Tracker | The username the bot uses when posting. (not required but nice to have)   |
| `JOIN_COLOR` | `#00FF00` (Green) | the hex color code for the embed's side stripe when a player joins |
| `LEAVE_COLOR` | `#FF0000` (Red)  | the hex color code for the embed's side stripe when a player leaves|

### Tags
you can customize the exact text using `JOIN_TITLE` `JOIN_TEXT` `LEAVE_TITLE` `LEAVE_TEXT` and `FOOTER_TEXT`.

when writing your custom sentences you can use tags, type these exact tags anywhere in your text and the bot will replace them with the live roblox data before sending the message:

* `{count}` - The current number of players online (e.g., `5`)
* `{visits}` - The total number of game visits, formatted with commas (e.g., `6,529`)
* `{likes}` - The total number of thumbs up (e.g., `51`)
* `{ratio}` - The Like-to-Dislike percentage (e.g., `67%`)

**Example `JOIN_TEXT` setup:**
> "a new player arrived! we are now at **{count}** players"