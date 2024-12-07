import os
import streamlit as st
import asyncio
from newsapi import NewsApiClient
import aiohttp
from datetime import date, timedelta
from groq import Groq

# --- API Keys and Access Tokens ---
newsapi_key = "446dc1fa183e4e859a7fb0daf64a6f2c"
groq_api_key = "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"

# Initialize News API client
newsapi = NewsApiClient(api_key=newsapi_key)


# Function to fetch news using News API asynchronously
async def fetch_news(topic, sources=None, domains=None):
    # Calculate today's date
    today = date.today()
    yesterday = today - timedelta(days=1)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic or "",
        "sources": sources or "",
        "domains": domains or "",
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 100,
        "apiKey": newsapi_key,
        "from": yesterday.isoformat(),
        "to": today.isoformat(),
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=10) as response:
                data = await response.json()
                return data["articles"]
        except asyncio.TimeoutError:
            print("Timeout occurred while fetching news.")
            return None


# Function to summarize news using Groq API with LLaMA 3
def summarize_news(news_list):  # Takes a list of news articles
    client = Groq(api_key=groq_api_key)

    all_content = " ".join(news_list)  # Combine all articles into one string

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes news articles.",
            },
            {
                "role": "user",
                "content": f"Please provide a short summary of the following news articles:\n\n{all_content}",
            },
        ],
        model="llama3-70b-8192",
    )

    return chat_completion.choices[0].message.content


# --- Streamlit app ---
st.title("📰 News Summarizer")
st.write("Get a summary of the day's news on a specific topic!")

# --- Session state initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.news_data = None

# --- Display chat messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Get initial news topic ---
if st.session_state.news_data is None:
    if topic := st.chat_input("Enter your news topic:"):
        st.session_state.messages.append({"role": "user", "content": topic})
        with st.chat_message("user"):
            st.markdown(topic)

        with st.chat_message("assistant"):
            st.markdown("Fetching and summarizing news...")

        # Fetch news articles asynchronously and summarize
        async def fetch_and_summarize_news():
            try:
                st.session_state.news_data = await fetch_news(topic)

                if st.session_state.news_data:
                    news_content_list = [
                        article.get("content", "")
                        for article in st.session_state.news_data
                    ]
                    summary = summarize_news(news_content_list)
                    st.markdown(f"**Overall Summary:** {summary}")  # Display the summary
                else:
                    st.markdown("No news found for this topic.")
            except Exception as e:
                st.markdown(f"An error occurred: {type(e).__name__}: {e}")
                st.exception(e)

        asyncio.run(fetch_and_summarize_news())