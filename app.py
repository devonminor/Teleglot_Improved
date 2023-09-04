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
from datetime import date
from enum import Enum
from random import choice, shuffle

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
                 "* To be quizzed on the words that you have already learned, text 'Quiz'.\n\n" \
                 "* To read a brief article in Spanish, text 'Article'\n\n" \
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
    # delete the user's learned vocab from the database
    try:
        supabase.table("learned_vocab").delete().eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase deletion error (learned_vocab):", e)
        return respond("Error: Unable to delete account. Please try again later.")

    # delete the user's suggested vocab from the database
    try:
        supabase.table("suggested_vocab").delete().eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase deletion error (suggestion_vocab):", e)
        return respond("Error: Unable to delete account. Please try again later.")

    # delete the user from the database
    try:
        supabase.table("users").delete().eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase insertions error (phone_number):", e)
        return respond("Error: Unable to delete account. Please try again later.")

    return respond("Your account has been deleted. Text anything to start over.")

def phone_number_vocab_pair_exists(phone_number, vocab):
    try:
        data = supabase.table("learned_vocab").select(
            "*").eq("phone_number", phone_number).eq("wp", vocab).execute()
    except Exception as e:
        print("Supabase insertions error (phone_number):", e)
        return False 
    return not len(data.data) == 0

def insert_vocab(phone_number, vocab):
    # Check if the phone number and vocab pair already exists
    if (phone_number_vocab_pair_exists(phone_number, vocab)):
        return False

    # Insert the vocab into the database under that phone number
    try:
        supabase.table("learned_vocab").insert([
            {"phone_number": phone_number, "wop": vocab}
        ]).execute()
    except Exception as e:
        print("Supabase insertions error (phone_number):", e)
        return False

    return True

def insert_suggested_vocab(phone_number, vocab):
    try:
        supabase.table("suggested_vocab").insert([
            {"phone_number": phone_number, "suggestion": vocab}
        ]).execute()
    except Exception as e:
        print("Supabase insertions error (phone_number):", e)

def get_all_learned_vocab_for_user(phone_number):
    try:
        data = supabase.table("learned_vocab").select(
            "*").eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase fetch error (phone_number):", e)
        return []
    
    vocab = []
    for row in data.data:
        vocab.append(row["wop"])
    
    return vocab

def get_all_suggested_vocab_for_user(phone_number):
    try:
        data = supabase.table("suggested_vocab").select(
            "*").eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase fetch error (phone_number):", e)
        return []
    
    vocab = []
    for row in data.data:
        vocab.append(row["suggestion"])
    
    return vocab

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

        try:
            supabase.table("users").update({ "info_stage": Basic_Info_Stage.COMPLETED.name }).eq("phone_number", phone_number).execute()
        except Exception as e:
            print("Supabase insertions error (info stage update):", e)

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
LEARN FUNCTION
"""
def handle_learn_request(phone_number, wop):
    """This function generates the translation and sample sentence using OpenAi"""

    # Get the translation, pronounciation, and sample sentence from ChatGPT
    try:
        generated_text = prompt_chatgpt_for_translation_pronunciation_and_sample_sentence(wop)
    except Exception as e:
        print("ChatGPT error:", e)
        return respond("Error: Unable to get translation. Please try again later.")
    
    print("Generated Text: ", generated_text)

    # Check if the generated text is empty
    if not generated_text:
        return respond("Error: Unable to get translation. Please try again later.")

    # Concatenate thhe first part of the response with the generated text and respond to user
    combined_wop_and_response = f"Learned word or phrase: {wop}\n\n{generated_text}"
    print(combined_wop_and_response)

    # Insert learned phrase/word into database
    insert_vocab(phone_number, wop)

    return respond(combined_wop_and_response)

"""
SUGGEST FUNCTION
"""
def handle_suggest_request(phone_number):
    # Get the user
    user = get_user(phone_number)

    # Get the words that the user has already learned
    vocab = get_all_learned_vocab_for_user(phone_number)
    print('previously learned vocab', vocab)

    # Get the words the ChatGPT has previously suggested
    suggested_vocab = get_all_suggested_vocab_for_user(phone_number)
    print('suggested vocab', suggested_vocab)

    # Get the recommendations from ChatGPT
    try:
        response = prompt_chatgpt_for_recommended_words(user, [*vocab, *suggested_vocab])
    except Exception as e:
        print("ChatGPT error:", e)
        return respond("Error: Unable to get recommendations. Please try again later.")
    insert_suggested_vocab(phone_number, response)

    return respond(f"Hey, {user.data['name']}! Check out the following vocab suggestions from ChatGPT:\n\n {response}")


"""
ARTICLE FUNCTION
"""
def handle_article_request(phone_number):
    user = get_user(phone_number)
    try:
        print("Getting article from ChatGPT")
        article = prompt_chatgpt_for_article(user)
        print(article)
    except Exception as e:
        print("ChatGPT error:", e)
        return respond("Error: Unable to get article. Please try again later.")
    return respond(article)

"""
QUIZ FUNCTION
"""
def handle_quiz_request(phone_number):
    """
    Two Steps for Quiz Mode:

    1) Show the user the quiz
      - Get the words that the user has learned
      - If the user has learned <4 words, tell them that they need to learn more words
      - Create a quiz with 4 randomly selected words from ChatGPT
      - Store the answer in the database
      - Set the quiz mode to active
      - Send the quiz to the user
    """
    # Get the words that the user has already learned
    vocab = get_all_learned_vocab_for_user(phone_number)

    # Check if the user has learned enough words to take the quiz
    if (len(vocab) < 4):
        return respond("You need to learn more words before you can take the quiz. Text 'Learn ___' to learn a new word.")
    
    # Select 1 random words from the user's learned vocab
    random_vocab = choice(vocab)

    # Get the spanish translation of the randomly selected word
    try:
        spanish_translation = prompt_chatgpt_for_translation(random_vocab)
    except Exception as e:
        print("ChatGPT error:", e)
        return respond("Error: Unable to send quiz. Please try again later.")
    
    # Get the other words for the quiz from ChatGPT
    try:
        incorrect_quiz_answers = prompt_chatgpt_for_mc_words(random_vocab)
    except Exception as e:
        print("ChatGPT error:", e)
        return respond("Error: Unable to send quiz. Please try again later.")

    # randomly sort the incorrect quiz answers
    incorrect_quiz_answers_list = incorrect_quiz_answers.replace(" ", "").split(",")
    incorrect_quiz_answers_list.append(random_vocab)
    shuffle(incorrect_quiz_answers_list)
    correct_answer_index = incorrect_quiz_answers_list.index(random_vocab) + 1
    
    # Store the answer in the database
    try:
        supabase.table("users").update({ "quiz_answer": correct_answer_index }).eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase insertions error (quiz answer):", e)
        return respond("Error: Unable to send quiz. Please try again later.")

    # Set the quiz mode to active
    try:
        supabase.table("users").update({ "is_in_quiz_mode": True }).eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase insertions error (quiz mode):", e)
        return respond("Error: Unable to send quiz. Please try again later.")

    # Send the quiz to the user
    return respond(f"What is the translation of {spanish_translation} in English? (Type the number corresponding the correct answer)\n\n"\
            f"1) {incorrect_quiz_answers_list[0]}\n\n" \
            f"2) {incorrect_quiz_answers_list[1]}\n\n" \
            f"3) {incorrect_quiz_answers_list[2]}\n\n" \
            f"4) {incorrect_quiz_answers_list[3]}\n\n")


def handle_quiz_response(phone_number, incoming_message):
    """
    2) Check the user's answers
      Done:
      - When checking the user's input, if quiz mode is set to active, reroute to the quiz mode

      Not Done:
      - Check if the user's answer is correct
      - set quiz mode to inactive
      - if the user's answer is correct, send them a message saying that they are correct
      - if the user's answer is incorrect, send them a message saying that they are incorrect and the correct answer
    """

    # Get the user
    user = get_user(phone_number)

    # if the user did not send a valid response, return
    if (not incoming_message.isdigit()):
        return respond("Please enter a valid response (1, 2, 3, or 4).")
    if (int(incoming_message) not in [1, 2, 3, 4]):
        return respond("Please enter a valid response (1, 2, 3, or 4).")

    # Check if the user's answer is correct
    answer_is_correct = int(incoming_message) == int(user.data["quiz_answer"])

    # Set quiz mode to inactive
    try:
        supabase.table("users").update({ "is_in_quiz_mode": False }).eq("phone_number", phone_number).execute()
    except Exception as e:
        print("Supabase update error (quiz mode):", e)
        return respond("Error: Unable to complete quiz. Please try again later.")
    
    # If the user's answer is correct, send them a message saying that they are correct
    if (answer_is_correct):
        return respond("Correct! Great job!")
    else:
        return respond(f"Incorrect. The correct answer was #{user.data['quiz_answer']}.")


"""
CHATGPT HELPER FUNCTIONS
"""
def prompt_chatgpt_for_translation_pronunciation_and_sample_sentence(wop):
    try:
        print("CHATGPT is going to be prompted")
        openai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"What is the translation, pronunciation, and sample sentence for the word/phrase {wop} in the language Spanish? Include the English translation for the sample sentence. Only include the translation once.",
                }
            ]
        )
    except Exception as e:
        print("ChatGPT error:", e)
        return None
    return openai_response.choices[0].message.content

def prompt_chatgpt_for_recommended_words(user, previously_learned_vocab):
    # Get the user's profile data
    name = user.data["name"]
    interests = user.data["interests"]

    recommendations = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {

                "role": "system",
                "content": f"{name} is trying to learn Spanish. They are interested in {interests}. Using their interests, generate a list of 3 English words that might be useful to learn in Spanish. The generated words do not have to come from their interests, however. The suggestions can be random. Please only include real English words. Do not include the Spanish translation or any description. Separate each word by a comma with no numbers. Do not include any of the following words: {', '.join(previously_learned_vocab)}."
            },
        ]
    )

    return recommendations.choices[0].message.content

def prompt_chatgpt_for_article(user):
    # Get the user's profile data
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
                "content": f"{name} is trying to learn Spanish. They are located in {location}. They are {age} years old. Their Spanish proficiency level is {proficiency}. They are interested in {interests}. Today's date is {date.today()}. Using the information about {name}, generate a two paragraph news article for {date.today()}. Match it to their proficiency level. Include a label before the Spanish reading that says 'Spanish Article:' and is followed by two empty lines. Include a label fefore the English translation that says 'English Translation:' and is followed by two empty lines."
            },
        ]
    )

    return recommendations.choices[0].message.content

def prompt_chatgpt_for_translation(wop):
    translation = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"Answer this with just the one word or phrase that is a translation of '{wop}' into Spanish. ",
            }
        ]
    )
    return translation.choices[0].message.content

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


"""
ROUTES
"""
@app.route("/whatsapp", methods=["POST"])
def handle_sms():
    incoming_message = request.values.get('Body', '').strip()
    user_phone_number = request.values.get('From')

    print(f"Received message from {user_phone_number}: {incoming_message}")

    # If this is a new user, ask them some basic questions
    info_quiz_stage = phone_number_has_completed_basic_info(user_phone_number)
    if (info_quiz_stage != Basic_Info_Stage.COMPLETED.name):
        return take_info_quiz(info_quiz_stage, user_phone_number, incoming_message)

    # If the user is in quiz mode, check their answer
    user = get_user(user_phone_number)
    if (user.data["is_in_quiz_mode"]):
        return handle_quiz_response(user_phone_number, incoming_message)
    
    if (incoming_message.lower() == "main menu"):
        print("Should see Main Menu")
        return main_menu()
    elif (incoming_message.lower().startswith("learn ")):
        print("Should see Learn")
        return handle_learn_request(user_phone_number, incoming_message[6:])
    elif (incoming_message.lower() == ("suggest")):
        print("Should see Suggest")
        return handle_suggest_request(user_phone_number)
    elif (incoming_message.lower() == "quiz"):
        print("Should see Quiz")
        return handle_quiz_request(user_phone_number)
    elif (incoming_message.lower() == "article"):
        return handle_article_request(user_phone_number)
    elif incoming_message.lower() == "delete account":
        print("Should see Delete Account")
        return delete_account(user_phone_number)
    else:
        print("Should see Unrecognized command")
        return respond("Unrecognized command. Please try again or text 'Main Menu' to see the menu options.")

# Start flask app
if __name__ == "__main__":
    app.run(debug=True)
