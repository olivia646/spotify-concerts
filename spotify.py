"""Spotify API integration for OAuth and fetching top artists."""

import os
import base64
import requests
from urllib.parse import urlencode

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

SCOPES = "user-top-read"


def get_auth_url(redirect_uri: str) -> str:
    """Generate Spotify OAuth authorization URL."""
    params = {
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for access token."""
    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]

    # Create base64 encoded credentials
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def get_top_artists(access_token: str, time_range: str = "medium_term", limit: int = 50) -> list:
    """
    Fetch user's top artists from Spotify.

    Args:
        access_token: Spotify access token
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (years)
        limit: Number of artists to fetch (max 50)

    Returns:
        List of artist dicts with name, id, and images
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"time_range": time_range, "limit": limit}

    response = requests.get(
        f"{SPOTIFY_API_BASE}/me/top/artists",
        headers=headers,
        params=params,
    )
    response.raise_for_status()

    data = response.json()
    artists = []

    for item in data.get("items", []):
        artist = {
            "id": item["id"],
            "name": item["name"],
            "image_url": item["images"][0]["url"] if item.get("images") else None,
            "genres": item.get("genres", []),
        }
        artists.append(artist)

    return artists


def get_all_top_artists(access_token: str) -> list:
    """
    Fetch top artists across all time ranges and deduplicate.

    Returns:
        Deduplicated list of artists sorted by appearance count
    """
    artist_counts = {}
    artist_data = {}

    for time_range in ["short_term", "medium_term", "long_term"]:
        artists = get_top_artists(access_token, time_range)
        for artist in artists:
            artist_id = artist["id"]
            artist_counts[artist_id] = artist_counts.get(artist_id, 0) + 1
            artist_data[artist_id] = artist

    # Sort by appearance count (most frequent first)
    sorted_ids = sorted(artist_counts.keys(), key=lambda x: artist_counts[x], reverse=True)

    return [artist_data[aid] for aid in sorted_ids]
