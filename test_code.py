import os
from datetime import date
from enum import Enum

import openai
import supabase
from dotenv import load_dotenv
from flask import Flask, request
from supabase import Client as SupabaseClient
from supabase import create_client
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

# load Supabase credentials
url: str = os.environ.get("SUPABASE_PROJECT_URL")
supabase_key: str = os.environ.get("SUPABASE_PUBLIC_ANON_KEY")
supabase: SupabaseClient = create_client(url, supabase_key)

# initialize supabase
try:
    client = SupabaseClient(url, supabase_key)
except Exception as e:
    print("Supabase initialization error:", e)
    
# load ChatGPT credentials
chatgpt_key = os.getenv("CHATGPT")

# initialize openai
openai.api_key = chatgpt_key

def get_user(phone_number):
    # Check if the phone number exists in the user database
    try:
        return supabase.table("users").select("*").eq("phone_number", phone_number).maybe_single().execute()
    except Exception as e:
        try:
            supabase.table("users").insert([ {"phone_number": phone_number}]).execute()
        except Exception as e:
            print("Supabase insertions error (phone_number):", e)
        return get_user(phone_number)


def prompt_chatgpt_for_mc_words(wop):
    recommendations = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"Generate a comma separated list of 3 English words that could be confused with the word or phrase '{wop}' because they sound alike, have similar spellings, or have similar but different meanings. Only include the English word. Do not include the Spanish translation or any description, or punctuation. Separate each word by a comma with no numbers."
            }
        ]
    )
    return recommendations.choices[0].message.content.lower()

phone_number = "whatsapp:+18573347982"
# user = get_user(phone_number)
print(prompt_chatgpt_for_mc_words("choice"))
