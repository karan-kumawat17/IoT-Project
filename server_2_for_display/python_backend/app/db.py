import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv("postgresql://neondb_owner:npg_7nIju6qeckMx@ep-ancient-grass-a1sf9huw-pooler.ap-southeast-1.aws.neon.tech/IoT?sslmode=require"), sslmode='require')
