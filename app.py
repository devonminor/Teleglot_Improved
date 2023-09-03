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

import openai
from dotenv import load_dotenv
from flask import Flask
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

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

# initialize twilio
try:
    twilio_client = TwilioClient(account_sid, auth_token)
except Exception as e:
    print("An error occurred while initializing the Twilio client:", e)

# initialize openai
openai.api_key = chatgpt_key


def respond(message):
    """Respond to incoming calls with a simple text message."""
    response = MessagingResponse()
    response.message(message)
    return str(response)


@app.route("/whatsapp", methods=["POST"])
def handle_sms():
    return respond("Hello World!")


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
