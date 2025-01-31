import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import json
import googleapiclient.discovery
import googleapiclient.errors
import random
import time

CLIENT_SECRETS_FILE = "client_secrets.json"
API_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_authenticated_service():
    credentials = None

    if os.path.exists("token.json"):
        with open("token.json", "r") as token_file:
            token_info = json.load(token_file)
            credentials = Credentials.from_authorized_user_info(token_info, SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(credentials.to_json())
    
    return googleapiclient.discovery.build(API_NAME, API_VERSION, credentials=credentials)

def post_comment(youtube, video_id, comment):
    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment
                        }
                    }
                }
            }
        )
        request.execute()
        print(f"Comment posted: {comment.strip()} on video {video_id}")
    except Exception as e:
        print(f"Error posting comment: {e}")

def get_popular_videos(youtube, query, max_results=500, region="US"):
    video_ids = []
    next_page_token = None

    while len(video_ids) < max_results:
        request = youtube.search().list(
            part="snippet",
            q=query,
            regionCode=region,
            maxResults=50,
            type="video",
            order="viewCount",
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['id']['videoId'])

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids[:max_results]

def load_comments():
    try:
        with open("comments.txt", "r", encoding="utf-8") as file:
            comments = file.readlines()
        return comments
    except FileNotFoundError:
        print("File comments.txt not found. Make sure the file exists.")
        return []

def main():
    youtube = get_authenticated_service()

    query = input("Enter video topic (e.g., CS2): ")
    language = input("Enter region code (e.g., US, PL): ")
    num_comments = int(input("How many comments do you want to post? "))
    delay = float(input("Enter delay between comments (in seconds): "))

    comments = load_comments()
    if not comments:
        print("No comments to load. Exiting script.")
        return

    video_ids = get_popular_videos(youtube, query, region=language)

    for _ in range(num_comments):
        video_id = random.choice(video_ids)
        comment = random.choice(comments).strip()
        post_comment(youtube, video_id, comment)
        time.sleep(delay)

if __name__ == "__main__":
    main()
