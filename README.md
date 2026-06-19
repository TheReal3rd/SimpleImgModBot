# SimpleImgModBot
Basic discord image banning bot with main goal to prevent and block scam image posting.


## TODO
* Add video hashing too.
* Finish adding basic supporting functions. 
* Add ability to scroll backwards in message history to find banned imgs.
* Improve logging delete really old logs.
* Finish the move from json to db with rework of detection code.
* Break the hash comparing into sequences. SHA256 -> phash(possibly removed) -> CLIP. Aim to improve performance.