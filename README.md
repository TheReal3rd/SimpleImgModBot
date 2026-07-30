# SimpleImgModBot (ModerationClanker)
Basic discord image banning bot with main goal to prevent and block scam image posting.

## TODO
* Add video hashing (Low priority just a feature not a needed component).
* Add image saving for further processing and checking by administrators. (Include a schedualed removal to prevent possible certain type of content being held.)

## Dev Info
This bot detects messages with images within their posts. Which are then Hashed into sha256 alongside fuzzy hashed. Which are then lookup into the fingerprint database.
If the database finds a match the image will be deleted and the posting user will be timedout for 28 days. Which results in a ban post confirmation being printed into the admin channel.
Where the user can confirm to ban the user.
The bot stricktly written to **not ban user without administrators confirmation**. To prevent false bans and removals.

sha256 - Used to image match saving compute before embedding.
Embedding - using OpenAI clip images are past through an AI model that creates an array of weight used to calculate the probabilty of image matching. By default the software will remove images with 87% confidance. With my testing this hasn't resulted into any false bans. after 100+ scans.

Database Managers.
1. PendingDataManager - Used to keep track of pending bans and checks. Which is automatically removed after 20 days. Used to ban new images or ban user for posting violating images.
2. FingerprintDataManager - Used to store and look up for banned image comparisons. First fetch sha256 if no results search embbed for any matches. If all fails moves on.

The bot will post when an image has been posted in the selected admin channel. Which will present a ban button and reaction trigger. When activated the image will be added to FingerprintDataManager and the offending image will be deleted.

> Note: Reactions are backup for buttons. Buttons won't work if the bot been restarted. Reactions are written so they will work after restart.

> Note: Debug being **True** in config will disable Ban, Kick, Timeout and more from working.

As of now the images for the db will be provided. They're scam sites do not follow them. Do not be fooled by them. I am not responsible for your own stupidity.

## Twitch Info

Their is a Tiwtch streamer notification system within the bot written by Tintrex.
The system isn't required to have the bot function but is provided for the specific use case of this bot.

To enable the functionality of the Twitch notify posting you must fill in the twitch section of the configuration i won't provide a full guide but there is plenty information around the internet to setup Twitch API. 

## Usage
1. Start the bot and let the program fail to create the config.json template.
2. Fill in the config.json will required entries. ChannelID, ServerID & Token.
3. Start the bot again and check if the bot starts.

> Note: Ensure you've installed all the requirements first.