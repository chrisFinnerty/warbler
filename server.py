# import os
# from dotenv import load_dotenv
from app import create_app
from models import connect_db

# load_dotenv()

app = create_app('warbler')
connect_db(app)