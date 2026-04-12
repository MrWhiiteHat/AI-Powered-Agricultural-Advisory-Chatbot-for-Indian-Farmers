from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv('d:/AI CLG Project/.env')
try:
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    print("Incoming Numbers:")
    for num in client.incoming_phone_numbers.list():
        print(num.phone_number)
except Exception as e:
    print("Error:", e)
