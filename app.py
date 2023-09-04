"""
Feedback from meeting:
    - Don't make the app entirely user driven. Potentially prompt the
      user with sample words to learn as well
    - Potentially add fill in the blank functionality to quiz mode
    - We have achieved the MVP, but we should try and hit more stretch goals
    - Our project should work smoothly 99% of the time
    - We should have some stretch goals ready to test in the user study as well

Feedback from email:
    Overall good job on getting an end-to-end system running. The system handles
    the core functionality of allowing users to learn words in Spanish and the
    quiz feature enables users to be tested on their knowledge.
  
    The project, however, could have been elevated given that it was a four
    member team. In addition to some basic error handling which was missing,
    we felt that the project could've been more sophisticated. The quiz
    feature was rather basic and a richer use of ChatGPT to enable a more
    interactive way for users to test out their knowledge could've been useful.
    Similarly, leveraging background information about the user to suggest
    words that were more relevant to their day-to-day use could've been another
    feature. ** Such features, if implemented , would've allowed you guys to have
    a more rigorous user-study and an opportunity to dig deeper into
    quantitative/qualitative aspects of the system. **

Feedback from email (simplified):
    Good Stuff:
        - End-to-end system
        - Had core functionality of allowing users to learn words in spanish
        - Quiz feature is good for users to test knowledge

    Could be better:
        - Basic error handling
        - More sophisticated
            - Quiz feature was basic
            - More ChatGPT integrations to make testing their knowledge more interactive
        - Leverage background information about the user to suggest more relevant words
        - ** other non-technical stuff **
    
The improvements I am going to make:
    1. Basic error handling
    2. Leveraging background information
        - Instagram/Facebook data?
        - Short quiz to determine level of Spanish and more about them?
    3. Generative image data?
        - This may not be possible
    4. More ChatGPT integrations
        - TV shows/books or something narrative
        - Speaking with someone? (conversationally) -- probably not going to do this
        - Practicing pronounciation
        - Summarizing news articles using the level of their language ability (I like this idea)
"""
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

"""
ENVIRONMENT VARIABLES/CREDENTIALS
"""
# Load environment variables
load_dotenv()

# Setup flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# load twilio credentials
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTHTOKEN")

# load ChatGPT credentials
chatgpt_key = os.getenv("CHATGPT")

# load Supabase credentials
url: str = os.environ.get("SUPABASE_PROJECT_URL")
supabase_key: str = os.environ.get("SUPABASE_PUBLIC_ANON_KEY")
supabase: SupabaseClient = create_client(url, supabase_key)

"""
INITIALIZATIONS
"""
# initialize twilio
try:
    twilio_client = TwilioClient(account_sid, auth_token)
except Exception as e:
    print("An error occurred while initializing the Twilio client:", e)

# initialize supabase
try:
    client = SupabaseClient(url, supabase_key)
except Exception as e:
    print("Supabase initialization error:", e)

# initialize openai
openai.api_key = chatgpt_key

"""
CLASS DEFINITIONS
"""
class Basic_Info_Stage(Enum):
    NOT_STARTED = 0
    NO_NAME = 1
    NO_LOCATION = 2
    NO_AGE = 3
    NO_PROFICIENCY = 5
    NO_INTERESTS = 6
    COMPLETED = 7

"""
HELPER FUNCTIONS
"""
def respond(message):
    """Respond to incoming calls with a simple text message."""
    response = MessagingResponse()
    response.message(message)
    return str(response)


main_menu_text = "MAIN MENU:\n\n" \
                 "* To learn a word or phrase, text: 'Learn ___.'\n\n" \
                 "* To see recommendations on some new words, text 'Suggest'\n\n" \
                 "* To hear the word or phrase in Spanish, text 'Speak ___ '.\n\n" \
                 "* To be quizzed on the words that you have already learned, text 'Quiz'.\n\n" \
                 "* To see the menu options again, text 'Main Menu'\n\n" \
                 "* To delete your account or start fresh, text 'Delete Account'"

def main_menu():
    return respond(main_menu_text)

"""
DATABASE FUNCTIONS
"""
def get_user(phone_number):
    # Check if the phone number exists in the user database
    try:
        return supabase.table("users").select("*").eq("phone_number", phone_number).maybe_single().execute()
    except:
        try:
            supabase.table("users").insert([ {"phone_number": phone_number}]).execute()
        except Exception as ie:
            print("Supabase insertions error (phone_number):", ie)
        return get_user(phone_number)


def delete_account(phone_number):
    try:
        supabase.table("users").delete().eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase insertions error (phone_number):", e)
    return respond("Your account has been deleted. Text anything to start over.")


"""
BASIC INFO FUNCTIONS
"""

def phone_number_has_completed_basic_info(phone_number):
    # Check if the user exists and create it if they don't
    user = get_user(phone_number)

    # Go through the user's data and check if they have completed the basic info
    if (user.data["name"] == None):
        return Basic_Info_Stage.NO_NAME.name
    if (user.data["location"] == None):
        return Basic_Info_Stage.NO_LOCATION.name
    if (user.data["age"] == None):
        return Basic_Info_Stage.NO_AGE.name
    if (user.data["proficiency"] == None):
        return Basic_Info_Stage.NO_PROFICIENCY.name
    if (user.data["interests"] == None):
        return Basic_Info_Stage.NO_INTERESTS.name

    return Basic_Info_Stage.COMPLETED.name

def take_info_quiz(stage, phone_number, incoming_message):
    """Ask the user some basic questions to learn more about them"""
    user = get_user(phone_number)
    print("user: ", user)
    print("stored info stage on user profile: ", user.data["info_stage"])
    print("claimed stage: ", stage) 

    # Name
    if (stage == Basic_Info_Stage.NO_NAME.name and stage == user.data["info_stage"]):
        try:
            res = supabase.table("users").update({ "name": incoming_message }).eq("phone_number", phone_number).execute()
            user.data = res.data[0]
        except Exception as e:
            print("Supabase insertions error (user name insertion):", e)
        stage = Basic_Info_Stage.NO_LOCATION.name
    elif (stage == Basic_Info_Stage.NO_NAME.name):
        try:
            supabase.table("users").update({ "info_stage": stage }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (info stage update):", e)
        return respond("Welcome to Teleglot! Teleglot is a ChatGPT-powered language learning service. We're going to walk your a quick quiz to learn some more information about you.\n\nWhat is your first and last name?")

    # Location
    if (stage == Basic_Info_Stage.NO_LOCATION.name and stage == user.data["info_stage"]):
        try:
            supabase.table("users").update({ "location": incoming_message }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (user location):", e)
        stage = Basic_Info_Stage.NO_AGE.name
    elif (stage == Basic_Info_Stage.NO_LOCATION.name):
        try:
            supabase.table("users").update({ "info_stage": stage }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (info stage update):", e)
        return respond(f"Hi {user.data['name']}! Where are you from?")

    # Age
    if (stage == Basic_Info_Stage.NO_AGE.name and stage == user.data["info_stage"]):
        # Check if the age is a valid number
        try:
            incoming_message = int(incoming_message)
        except:
            return respond("Please enter a valid age (in years).")

        try:
            supabase.table("users").update({ "age": incoming_message }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (user location):", e)
        stage = Basic_Info_Stage.NO_PROFICIENCY.name
    elif (stage == Basic_Info_Stage.NO_AGE.name):
        try:
            supabase.table("users").update({ "info_stage": stage }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (info stage update):", e)
        return respond(f"How old are you (in years)?")

    # Proficiency/Level of Spanish
    if (stage == Basic_Info_Stage.NO_PROFICIENCY.name and stage == user.data["info_stage"]):
        # Check if the profiency is valid (beginner/intermediate/advanced)
        if (incoming_message.lower() not in ["beginner", "intermediate", "advanced"]):
            return respond("Please enter a valid proficiency (beginner/intermediate/advanced).")

        try:
            supabase.table("users").update({ "proficiency": incoming_message }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (user location):", e)
        stage = Basic_Info_Stage.NO_INTERESTS.name
    elif (stage == Basic_Info_Stage.NO_PROFICIENCY.name):
        try:
            supabase.table("users").update({ "info_stage": stage }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (info stage update):", e)
        return respond(f"What is your level of experience? (Beginner, Intermediate, or Advanced)")

    # Interests
    if (stage == Basic_Info_Stage.NO_INTERESTS.name and stage == user.data["info_stage"]):
        try:
            supabase.table("users").update({ "interests": incoming_message }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (user location):", e)
        stage = Basic_Info_Stage.COMPLETED.name
        return respond(f"Thanks for taking our intro quiz {user.data['name']}! You are now ready to start learning Spanish with Teleglot! See our main menu now below:\n\n{main_menu_text}")
    elif (stage == Basic_Info_Stage.NO_INTERESTS.name):
        try:
            supabase.table("users").update({ "info_stage": stage }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (info stage update):", e)
        return respond(f"What are your interests? (separated by commas) Ex: Sports, Music, Art")

    return respond("Something went wrong. Please try again later.")


"""
ROUTES
"""
@app.route("/whatsapp", methods=["POST"])
def handle_sms():
    incoming_message = request.values.get('Body', '').strip()
    user_phone_number = request.values.get('From')

    # If this is a new user, ask them some basic questions
    info_quiz_stage = phone_number_has_completed_basic_info(user_phone_number)
    if (info_quiz_stage != Basic_Info_Stage.COMPLETED.name):
        return take_info_quiz(info_quiz_stage, user_phone_number, incoming_message)
    
    if (incoming_message.lower() == "main menu"):
        return main_menu()
    if incoming_message.lower() == "delete account":
        return delete_account(user_phone_number)
    else:
        return main_menu()


"""
STEPS:
    1) Respond to the user with a menu with all of the available options
    2) If this is there first time (meaning we haven't previously collected data about this user). Learn more about the user
    3) Cipher options and redirect them to the appropriate function
    4) Use ChatGPT to generate a response
"""


# Start flask app
if __name__ == "__main__":
    app.run(debug=True)
