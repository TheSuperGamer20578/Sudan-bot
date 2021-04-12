# Sudan-bot
## Installation
1. Clone this repo.
2. In `bot/` rename `.env.sample` to `.env`.
3. Again in `bot/` edit `.env`.
4. Install requirements from `requirements.txt`. This can be done by passing the `-r` flag to pip followed by the requirements file.
5. Run `setup.py`
6. Run the commands in `Setup_DB.sql` to create the tables in the database.
7. `cd bot` and run `core.py`. If you are on linux and want to use the auto updating cog you will have to run it with `start.sh`.
8. `cd slash` and run `gunicorn app:app`  
<br/>
Or push this button  
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)  

For more info look at the (currently non-existent) [Wiki](https://github.com/TheSuperGamer20578/Sudan-bot/wiki)
