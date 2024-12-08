import streamlit as st
import requests
from datetime import datetime
from newspaper import Article
from groq import Groq
from diffusers import DiffusionPipeline
from IPython.display import display

# Your News API key and Groq API setup
API_KEY = '446dc1fa183e4e859a7fb0daf64a6f2c'
BASE_URL = 'https://newsapi.org/v2/everything'
client = Groq(api_key="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")

# Function to fetch news based on topic
def get_news_by_topic(topic):
    params = {
        'q': topic,
        'apiKey': API_KEY,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 5
    }

    response = requests.get(BASE_URL, params=params)
    news_list = []

    if response.status_code == 200:
        data = response.json()

        if 'articles' in data:
            for article in data['articles']:
                title = article['title']
                description = article['description']
                published_at = article['publishedAt']
                content = article.get('content', 'No full content available.')
                url = article['url']

                published_at = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                formatted_time = published_at.strftime('%Y-%m-%d %H:%M:%S')

                article_data = {
                    'title': title,
                    'description': description,
                    'publishedAt': formatted_time,
                    'content': content,
                    'url': url
                }

                news_list.append(article_data)

    return news_list

# Function to fetch full article using Newspaper
def fetch_full_article_with_newspaper(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Error occurred during parsing: {str(e)}"

# Function to summarize an article using Groq's Llama 3 model
def summarize_article(client, article_content, tone):
    prompt = f"""
    You are a professional News Summarizer.
    Your task is to summarize the provided news article while retaining all key details.
    Adjust the tone and style of the summary based on the user input (e.g., "formal," "conversational," or "humorous").
    
    # News Article:
    {article_content}
    
    # Tone/Style:
    {tone}
    
    Remove unwanted sentences in summary like "article not found" or anything unrelated to the user query.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )

        summary = chat_completion.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"An error occurred: {e}"

# Function to generate social media post content
def generate_social_media_post(summary, tone):
    prompt = f"""
    You are a professional social media content creator.
    Your task is to create an engaging text post based on the provided news article summary while retaining all key details.
    Ensure the tone matches the specified style provided.

    News Article:
    {summary}
    
    Provide the text post below:
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        
        social_media_post = chat_completion.choices[0].message.content.strip()
        return social_media_post
    except Exception as e:
        return f"Error occurred while generating the post: {e}"

# Generate an image from news summary description using Stable Diffusion
def generate_image_from_description(description):
    # Load the DiffusionPipeline for Stable Diffusion from the diffusers library
    generator = DiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
    generator.to("cuda")

    # Generate the image
    image = generator(description).images[0]
    return image

# Streamlit UI
def main():
    st.title("News Summarizer and Social Media Post Generator")
    st.subheader("Generate a social media post based on the latest news summary")

    # Input fields for topic and tone
    topic = st.text_input("Enter the topic you want news for:")
    tone = st.selectbox("Select the tone of the summary:", ["formal", "conversational", "humorous"])

    if st.button("Generate Social Media Post"):
        if topic:
            st.write(f"Fetching news about: {topic} in {tone} tone...")

            # Fetch the latest news based on the topic
            news_data = get_news_by_topic(topic)

            if news_data:
                combined_content = ""
                for article in news_data:
                    article_content = fetch_full_article_with_newspaper(article['url'])
                    summary = summarize_article(client, article_content, tone)
                    combined_content += summary
                
                # Generate the enhanced description for image generation
                enhanced_prompt = f"""
                You are a professional artist. Given the following news summary, create a detailed and vivid description that can be used to generate an image:
                {combined_content}

                The description should capture the mood, setting, actions, and emotions in a way that a model can visually interpret. Include details such as time of day, character appearance, atmosphere, and background elements.
                """

                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": enhanced_prompt}],
                    model="llama3-8b-8192"
                )

                enhanced_description = chat_completion.choices[0].message.content
                st.write("### Enhanced Description for Image Generation:")
                st.write(enhanced_description)

                # Generate an image based on the enhanced description
                image = generate_image_from_description(enhanced_description)
                
                # Display the generated image
                st.image(image, caption="Generated Image based on News Summary")

                # Generate a social media post based on the summary
                social_media_post = generate_social_media_post(combined_content, tone)

                st.write("### Generated Social Media Post:")
                st.write(social_media_post)

                # Allow user to download the post as a text file
                post_filename = f"news_summary_{topic.replace(' ', '_')}.txt"
                st.download_button("Download Post as Text File", data=social_media_post, file_name=post_filename)

            else:
                st.write("No news articles found for this topic.")
        else:
            st.write("Please enter a topic to search for news.")

if __name__ == "__main__":
    main()
