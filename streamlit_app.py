import streamlit as st
import asyncio
from newsapi import NewsApiClient
import aiohttp
from datetime import date, timedelta
import requests

# --- API Keys and Access Tokens ---
newsapi_key = "446dc1fa183e4e859a7fb0daf64a6f2c"  # Replace with your actual News API key
gorq_api_key = "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"  # Replace with your actual Gorq API key


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
        "to": today.isoformat()
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=10) as response:  # Add timeout
                data = await response.json()
                return data["articles"]
        except asyncio.TimeoutError:
            print("Timeout occurred while fetching news.")
            return None  # Or handle the timeout in another way

# Function to summarize news using Gorq API with LLaMA 3
def summarize_news(text):
    headers = {
        "Authorization": f"Bearer {gorq_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "length": "short",
        "model": "llama2-70b-chat"  # Use LLaMA 2 70B chat model
    }
    try:
        response = requests.post("https://api.gorq.io/summarize", headers=headers, json=data, timeout=10)  # Add timeout
        if response.status_code == 200:
            return response.json()["summary"]
        else:
            print(f"Error summarizing: {response.status_code} - {response.text}")
            return "Error summarizing the text."
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during summarization: {e}")
        return "Error summarizing the text."

# --- Streamlit app ---
st.title("📰 News Retriever & Summarizer")
st.write("Retrieve, summarize, and display news articles!")

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
            st.markdown("Fetching news...")

        # Fetch news articles asynchronously
        async def fetch_and_display_news():
            try:
                st.session_state.news_data = await fetch_news(topic)

                if st.session_state.news_data:
                    st.markdown("News retrieved!")
                else:
                    st.markdown("No news found for this topic.")
            except Exception as e:
                st.markdown(f"An error occurred: {type(e).__name__}: {e}")
                st.exception(e)

        asyncio.run(fetch_and_display_news())

# --- Display news data with summaries if available ---
if st.session_state.news_data:
    if st.button("Show News with Summaries"):
        with st.chat_message("assistant"):
            # Display all news articles with summaries
            for article in st.session_state.news_data:
                st.markdown(f"**{article['title']}**")
                summary = summarize_news(article.get('content', ''))
                st.markdown(f"**Summary:** {summary}")
                st.markdown(article['url'])
                st.markdown("---")

        # Clear news data after displaying
        st.session_state.news_data = None