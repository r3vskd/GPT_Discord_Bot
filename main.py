from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
import openai
from discord.ext import commands
import webserver

load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY: Final[str] = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

webserver.keep_alive()

async def get_chatgpt_response(prompt: str, model_list: list[str]) -> str:
    for model in model_list:
        try:
            response = await openai.Completion.acreate(
                model=model,
                prompt=prompt,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,)
            return response.choices[0].text.strip()
        except openai.error.RateLimitError:
            print("Rate limit exceeded.")
            return "Rate limit exceeded. Please try again later."
        except openai.error.InvalidRequestError as e:
            if "upgrade your plan" in str(e):
                print("Plan upgrade required.")
                return "You have reached the limits of the free plan. Please consider upgrading to a Plus or Team plan for more access."
            print(f"Invalid request: {e}")
            return "There was an error with the request. Please try again."
        except openai.error.AuthenticationError:
            print("Authentication failed. Check your API key.")
            return "Authentication failed. Please check the API key."
        except openai.error.OpenAIError as e:
            print(f"General OpenAI error: {e}")
            return "An error occurred with OpenAI's API. Please try again later."
        except openai.error.RateLimitError as e:
            print(f"Quota exceeded for model {model}: {e}")
            return "The service is currently experiencing high demand. Please try again later."
        except Exception as e:
            print(f"Error fetching response from OpenAI using {model}: {e}")
        return "Sorry, I couldn't process your request."

async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('(Message was empty because intents were not enabled probably)')
        return

    is_private = user_message[0] == '?'

    if is_private:
        user_message = user_message[1:]

    try:
        response: str = await get_chatgpt_response(user_message, ["gpt-3.5-turbo"])
        if is_private:
            await message.author.send(response)
        else:
            await message.channel.send(response)
    except Exception as e:
        print(f"Error sending message: {e}")
        
@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)

def main() -> None:
    if not DISCORD_TOKEN:
        print("Discord token is not set. Please check your .env file.")
        return

    client.run(DISCORD_TOKEN)

if __name__ == '__main__':
    main()