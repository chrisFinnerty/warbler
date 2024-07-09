"""Seed database with sample data from CSV Files."""
import os 

from dotenv import load_dotenv
from csv import DictReader
from app import db, create_app
from models import User, Message, Follows

load_dotenv()

app = create_app(os.environ.get('DATABASE_URL'))

with app.app_context():
    # db.drop_all()
    # db.create_all()

    with open('generator/users.csv') as users:
        db.session.bulk_insert_mappings(User, DictReader(users))

    with open('generator/messages.csv') as messages:
        db.session.bulk_insert_mappings(Message, DictReader(messages))

    with open('generator/follows.csv') as follows:
        db.session.bulk_insert_mappings(Follows, DictReader(follows))

    db.session.commit()
