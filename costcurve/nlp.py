from openai import OpenAI

def get_api_key(path: str = "openai_key.txt"):
    with open(path, "r") as f:
        key = f.read()
    return key

def isit(x: str, y: str, client=None) -> bool:
    """Query GPT3.5 to ask if x is a kind of y."""
    client = client or OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": f"In one word (True or False), is {x} a kind of {y}?",

        }
    ],
    model="gpt-3.5-turbo",
)
    r = response.choices[0].message.content
    if r.startswith("True"):
        return True
    elif r.startswith("False"):
        return False
    else:
        raise Exception(f"Expected True or False from GPT3.5, got {r}")
