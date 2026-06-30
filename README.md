# SimpleImgModBot
Basic discord image banning bot with main goal to prevent and block scam image posting.

## TODO
* Add video hashing (Low priority just a feature not a needed component).
* Add Automated Scans for missing roles that are required for the server alongside age of the acount, Present a ban or kick options for the users.
* Move the update loop for scans to a thread with waiting to limit number of requests.
* Create a multithreading manager to throw tasks to.
* self cleanup if an pending task message has expired delete it. so it cleans up and declutters the channel.

## Think about:
* Possibly multithread queue the messages processing.
