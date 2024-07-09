from app import create_app
from models import connect_db

app = create_app('warbler')
connect_db(app)