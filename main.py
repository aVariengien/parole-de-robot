# %%
from anthropic import Anthropic
import streamlit as st
import os
from pprint import pprint
from prompts import (
    SYSTEM_PROMPT,
    MESSAGE_INTRO,
    RESPONSE_LLM,
    FALSE_FACTS,
    TRUE_FACTS,
    INTRO_QUESTION_PRIOR,
    ASK_CHANGE_MIND,
    FINAL_PROMPT,
    AVANT_DERNIERE
)
import random as rd
import time

# %%
anthropic_api_key = st.secrets["anthropic_api_key"]
model_name = (
    "claude-3-haiku-20240307"  # claude-3-sonnet-20240229 	claude-3-opus-20240229
)
max_turn = 2

if "messages" not in st.session_state:
    
    print("hello")
    st.session_state["turn_question"] = 0
    
    ALL_FACTS = TRUE_FACTS + FALSE_FACTS
    
    fact = rd.choice(ALL_FACTS)
    st.session_state["fact"] = fact

    print(fact)

    dialogue = [
        {"role": "user", "content": MESSAGE_INTRO.format(FACT=fact)},
        {"role": "assistant", "content": RESPONSE_LLM.format(FACT=fact)},
    ]

    client = Anthropic(api_key=anthropic_api_key)
    response = client.messages.create(
        system=SYSTEM_PROMPT, model=model_name, max_tokens=2048, messages=dialogue
    )
    msg_intro = response.content[0].text

    dialogue[1]["content"] += msg_intro + INTRO_QUESTION_PRIOR
    st.session_state["messages"] = dialogue

# %%

st.title("😈 Parole de Robot 😇")
st.caption("Mets la parole de l'IA à l'épreuve en jugeant la véracité des faits 🕵️")


def print_hello():
    print("hello")


if 'first_guess' not in st.session_state:
    st.session_state["first_guess"] = "unset"

for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

def stream_data_factory(string):
    def stream_data():
        for c in string:
            yield c
            time.sleep(0.01)
    return stream_data


# if st.session_state["first_guess"] == "unset":
#     prompt = st.chat_input(disabled=True)
# else:
if prompt := st.chat_input():
    client = Anthropic(api_key=anthropic_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "assistant", "content": "[PolyPedia]"})

    # with client.messages.stream(
    #     system=SYSTEM_PROMPT,
    #     model=model_name,
    #     max_tokens=2048,
    #     messages=st.session_state.messages,
    # ) as stream:
    #     for text in stream.text_stream:
    #         print(text, end="", flush=True)
    if st.session_state["turn_question"] <= max_turn:
        with st.chat_message("assistant"):
            with client.messages.stream(
                system=SYSTEM_PROMPT,
                model=model_name,
                max_tokens=2048,
                messages=st.session_state.messages,
            ) as stream:
                response = st.write_stream(stream.text_stream)
    elif st.session_state["turn_question"] == max_turn + 1:
        verite = "✅ VRAI ! ✅" if st.session_state["fact"] in TRUE_FACTS else "❌ FAUX ! ❌"
        final_answer = FINAL_PROMPT.format(ANSWER = verite)
        with st.chat_message("assistant"):
            st.write_stream(stream_data_factory(final_answer))

    if st.session_state["turn_question"] <= max_turn:
        # response = client.messages.create(
        #     system=SYSTEM_PROMPT, model=model_name, max_tokens=2048, messages=st.session_state.messages
        # )
        # msg = response.content[0].text
        #print("'{rep}'".format(rep=response))
        st.session_state.messages[-1]["content"] += response
        #pprint(st.session_state.messages)
        
        #print(st.session_state["turn_question"])

        if st.session_state["turn_question"] == max_turn -1:
            with st.chat_message("assistant"):
                st.write_stream(stream_data_factory(AVANT_DERNIERE))
            st.session_state.messages[-1]["content"] += AVANT_DERNIERE

        if st.session_state["turn_question"] == max_turn:
            st.session_state.messages[-1]["content"] += ASK_CHANGE_MIND
            with st.chat_message("assistant"):
                st.write_stream(stream_data_factory(ASK_CHANGE_MIND))
        st.session_state["turn_question"] += 1
        # st.chat_message("assistant").write(response)


# if st.session_state["first_guess"] == "unset":
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         btn_true = st.button("✅ C'est vrai !", help = "Je connais ce fait, et c'est vrai !")

#     with col2:
#         btn_idk = st.button('🤷 Je suis pas sûr.', help = "Je ne suis pas fixé, je vais poser des questions pour y voir plus clair !")

#     with col3:
#         btn_false = st.button("❌ C'est faux !", help = "Je connais ce fait, et c'est faux !")

#     if btn_false:
#         st.chat_message("assistant").write("Commencons ! Vous pouvez poser votre première question.")
#         st.session_state["first_guess"] = "idk"
#         st.rerun()

#     if btn_true:
#         st.chat_message("assistant").write("Commencons ! Vous pouvez poser votre première question.")
#         st.session_state["first_guess"] = "idk"
#         st.rerun()

#     if btn_idk:
#         st.chat_message("assistant").write("Commencons ! Vous pouvez poser votre première question.")
#         st.session_state["first_guess"] = "idk"
#         st.rerun()