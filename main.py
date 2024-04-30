# %%
import json
from pathlib import Path
import uuid
from anthropic import Anthropic
import openai
import streamlit as st
from pprint import pprint
import random
import time
from dataclasses import asdict, dataclass, field

from streamlit_pills import pills as st_pills
import streamlit_cookies_controller as stcc

from prompts import *
import utils

anthropic_api_key = st.secrets["anthropic_api_key"]
openai.api_key = st.secrets["openai_api_key"]
client = Anthropic(api_key=anthropic_api_key)

model_name = (
    # "claude-3-haiku-20240307"
    # claude-3-sonnet-20240229
    # claude-3-opus-20240229
    "gpt-3.5-turbo"
)

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
BOT_NAME = "PolyPedia"


@dataclass
class User:
    uid: str
    chat_id: str
    fact: str
    positive: bool
    messages: list = field(default_factory=list)
    start_belief: int | None = None
    end_belief: int | None = None

    def generate_message(self):
        system = [SYSTEM_NEGATIF, SYSTEM_POSITIF][self.positive]
        # We store more than role+content in the messages list
        msg_dicts = [dict(role=msg["role"], content=msg["content"]) for msg in self.messages[2:]]

        if "claude" in model_name:
            with client.messages.stream(
                system=system,
                model=model_name,
                max_tokens=2048,
                messages=msg_dicts,
            ) as stream:
                response = st.write_stream(stream.text_stream)
        else:
            stream = openai.chat.completions.create(
                model=model_name,
                messages=[dict(role="system", content=system)] + msg_dicts,
                max_tokens=2048,
                stream=True,
            )
            response = st.write_stream(
                self.filter_name(
                    chunk.choices[0].delta.content
                    for chunk in stream
                    if chunk.choices[0].delta.content is not None
                )
            )

        if self.messages[-1]["role"] == "assistant" and "claude" in model_name:
            self.messages[-1]["content"] += response
        else:
            self.messages.append(dict(role="assistant", content=response))

        self.messages[-1]["timestamp"] = time.time()
        try:
            self.messages[-1]["suggestions"] = self.make_suggestions()
        except Exception as e:
            # Rate limit
            print(e)

        self.save()

    def answer(self, answer: str):
        self.messages.append(dict(role="user", content=answer, timestamp=time.time()))
        self.save()

    def ask_belief(self, start: bool):
        value = self.start_belief if start else self.end_belief
        sentiment = st.select_slider(
            f"Quel est le bilan des actions de {self.fact} ?",
            options=range(1, 100),
            format_func=utils.fmt,
            disabled=value is not None,
            value=value or 50,
            key=f"belief_{start}",
        )

        if value is not None:
            return

        if st.button("Commencer !" if start else "Terminer"):
            if start:
                self.start_belief = sentiment
            else:
                self.end_belief = sentiment
            self.save()
            return True

    def make_suggestions(self):
        suggestions = client.messages.create(
            max_tokens=200,
            model="claude-3-haiku-20240307",
            system=SYSTEM_SUGGESTIONS,
            messages=[
                dict(
                    role="user",
                    content="\n---\n".join(m["role"] + ": " + m["content"] for m in self.messages),
                ),
                dict(role="assistant", content='["'),
            ],
        )

        as_list = json.loads('["' + suggestions.content[0].text)
        return as_list

    def filter_name(self, stream):
        """Remove all instances of the name from the stream"""
        to_filter = ["FavorFact", "DefavorFact"]
        # Note: the name is spread over multiple tokens
        past = ""
        for token in stream:
            past += token
            if any(f in past for f in to_filter):
                past = past.replace("FavorFact", BOT_NAME).replace("DefavorFact", BOT_NAME)

            yield past[: -len("DefavorFact")]
            past = past[-len("DefavorFact") :]
        yield past

    def save(self):
        path = DATA / f"{self.uid}-chat-{self.chat_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2))


st.title("😈 Parole de Robot 😇")
st.caption("Mets la parole de l'IA à l'épreuve en jugeant la véracité des faits 🕵️")


if "user" not in st.session_state:
    cookie_manager = stcc.CookieController()
    uid = cookie_manager.get("parole-user")
    if uid is None:
        # Apparently, get does a reload once a communication with the page returned the cookie.
        # If we set a new cookie before the page is reloaded, we overwrite the previous cookie...
        time.sleep(0.5)
        uid = str(uuid.uuid4())
        cookie_manager.set("parole-user", uid)

    user = User(
        fact=random.choice(PERSONNAGES),
        positive=random.choice([True, False]),
        uid=uid,
        chat_id=str(uuid.uuid4()),
        messages=[dict(role="user", content="Bonjour!")],
    )
    st.session_state["user"] = user

    first_message = RESPONSE_LLM.format(FACT=user.fact)
    with st.chat_message("assistant"):
        st.write_stream(
            time.sleep(abs(random.gauss(sigma=0.04))) or l + " " for l in first_message.split()
        )
    user.messages.append(dict(role="assistant", content=first_message))
else:
    user = st.session_state["user"]
    st.chat_message("assistant").write(user.messages[1]["content"])


turn = len(user.messages) // 2 - 1

# Ask for their sentiment
if user.ask_belief(start=True):
    user.answer(MESSAGE_INTRO.format(FACT=user.fact))
    st.rerun()

for i, msg in enumerate(user.messages[2:]):
    st.chat_message(msg["role"]).write(msg["content"])


max_turn = 2
if turn < max_turn and user.start_belief:
    # Show suggestions
    user_answer = st.empty()
    if "suggestions" in user.messages[-1]:
        with user_answer:
            suggested = st_pills("Suggestions", user.messages[-1]["suggestions"], index=None)
    else:
        suggested = None
    prompt = st.chat_input() or suggested

    if prompt:
        user.answer(prompt)
        user_answer.chat_message("user").write(prompt)

    if user.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            user.generate_message()
            st.rerun()

elif turn == max_turn:

    if (end := user.ask_belief(start=False)) is not None:
        user.end_belief = end
        st.rerun()
    elif user.end_belief is not None:
        st.write("Merci pour ta participation ! 🎉 \n 🔄 Recharge la page pour rejouer ! 🔄")
        st.balloons()
