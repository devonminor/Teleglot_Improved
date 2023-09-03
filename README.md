To run this application you need to start the Flask server. You can start the flask server by running `flask run` or `python3 -m flask run`.

To specify the port that the flask server is running on, add the `--port=[port]` where `[port]` will be replaced with the desired port number.

To run the server in debug mode, add the `--debug` option.

Then, you will need to run ngrok with the command `ngrok http [port]` where `[port]` will be replaced by the same port number as the server. Please note that you must authenticate ngrok in order to have it work with twilio.

Once the server and ngrok are running, take the HTTP address given to you by ngrok, add the correct route to the end of it (which in this case is `/ivr/welcome`), and update the twilio dashboard with the url.

For additional information about the Twilio dashboard, responding to incoming calls, and project setup, please see the [following documentation](https://www.twilio.com/docs/voice/tutorials/how-to-respond-to-incoming-phone-calls/python).
