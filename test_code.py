import os
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


# Write chatgpt code that suggests words to the user based on their profile.
def prompt_chatgpt_for_recommended_words(phone_number):
    """
    Prompts ChatGPT for the 3 recommended words in English that might be useful to learn in Spanish based on a given word or phrase.
    """
    # Get the user's profile
    user = get_user(phone_number)

    name = user.data["name"]
    location = user.data["location"]
    age = user.data["age"]
    proficiency = user.data["proficiency"]
    interests = user.data["interests"]
    

    recommendations = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {

                "role": "system",
                "content": f"{name} is trying to learn Spanish. They are located in {location}, but speak English fluently/natively. They are {age} years old and are a {proficiency} speaker. They are interested in {interests}. Using the prior information about {name}, generate a list of 3 English words that might be useful to learn in Spanish. Do not include the Spanish translation or any description. Separate each word by a comma. Try to make them different each time."
            },
        ]
    )

    return recommendations.choices[0].message.content

phone_number = "whatsapp:+18573347982"
print(prompt_chatgpt_for_recommended_words(phone_number))