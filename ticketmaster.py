"""Ticketmaster API integration for finding concerts."""

import os
import time
from datetime import datetime
from typing import Optional
import requests

TICKETMASTER_API_BASE = "https://app.ticketmaster.com/discovery/v2"


def find_attraction_id(artist_name: str) -> Optional[str]:
    """
    Find the Ticketmaster attraction ID for an artist.

    Returns:
        Attraction ID if found, None otherwise
    """
    api_key = os.environ["TICKETMASTER_API_KEY"]

    params = {
        "apikey": api_key,
        "keyword": artist_name,
        "classificationName": "Music",
        "size": 5,
    }

    response = requests.get(f"{TICKETMASTER_API_BASE}/attractions.json", params=params)
    response.raise_for_status()

    data = response.json()

    if "_embedded" not in data:
        return None

    # Look for exact or close match
    artist_lower = artist_name.lower()
    for attraction in data["_embedded"].get("attractions", []):
        attraction_name = attraction.get("name", "").lower()
        # Check for exact match or if artist name is contained
        if attraction_name == artist_lower or artist_lower in attraction_name:
            return attraction["id"]

    return None


def search_concerts_by_attraction(attraction_id: str, city: str = "San Francisco") -> list:
    """
    Search for concerts by attraction ID within 20 miles of a city.
    """
    api_key = os.environ["TICKETMASTER_API_KEY"]

    params = {
        "apikey": api_key,
        "attractionId": attraction_id,
        "city": city,
        "radius": 20,
        "unit": "miles",
        "classificationName": "Music",
        "size": 10,
        "sort": "date,asc",
    }

    response = requests.get(f"{TICKETMASTER_API_BASE}/events.json", params=params)
    response.raise_for_status()

    data = response.json()
    events = []

    if "_embedded" not in data:
        return events

    for event in data["_embedded"].get("events", []):
        # Extract venue info
        venue_name = "TBA"
        if "_embedded" in event and "venues" in event["_embedded"]:
            venues = event["_embedded"]["venues"]
            if venues:
                venue_name = venues[0].get("name", "TBA")

        # Extract date info
        dates = event.get("dates", {})
        start = dates.get("start", {})
        date_str = start.get("localDate", "")
        time_str = start.get("localTime", "")

        # Format date nicely
        formatted_date = ""
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = dt.strftime("%b %d, %Y")
                if time_str:
                    time_dt = datetime.strptime(time_str, "%H:%M:%S")
                    formatted_date += f" at {time_dt.strftime('%I:%M %p')}"
            except ValueError:
                formatted_date = date_str

        # Get image
        image_url = None
        for img in event.get("images", []):
            if img.get("width", 0) >= 300:
                image_url = img["url"]
                break

        concert = {
            "id": event["id"],
            "name": event["name"],
            "date": formatted_date,
            "raw_date": date_str,
            "venue": venue_name,
            "url": event.get("url", ""),
            "image_url": image_url,
        }
        events.append(concert)

    return events


def find_concerts_for_artists(artists: list, city: str = "San Francisco", max_artists: int = 25) -> list:
    """
    Search for concerts for a list of artists.

    Args:
        artists: List of artist dicts (must have 'name' key)
        city: City to search in
        max_artists: Maximum number of artists to search (to avoid rate limits)

    Returns:
        List of concert dicts with matched artist info
    """
    all_concerts = []
    seen_event_ids = set()

    # Limit artists to avoid rate limiting
    artists_to_search = artists[:max_artists]

    for i, artist in enumerate(artists_to_search):
        # Rate limit: wait between requests
        if i > 0:
            time.sleep(0.15)

        artist_name = artist["name"]

        try:
            # First find the attraction ID for exact matching
            attraction_id = find_attraction_id(artist_name)

            if not attraction_id:
                continue

            time.sleep(0.15)  # Rate limit between calls

            # Then search for events by attraction ID
            concerts = search_concerts_by_attraction(attraction_id, city)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited - wait and skip this artist
                time.sleep(2)
                continue
            raise

        for concert in concerts:
            # Deduplicate events
            if concert["id"] in seen_event_ids:
                continue
            seen_event_ids.add(concert["id"])

            # Add artist info to concert
            concert["artist"] = {
                "name": artist_name,
                "image_url": artist.get("image_url"),
            }
            all_concerts.append(concert)

    # Sort by date
    all_concerts.sort(key=lambda x: x.get("raw_date", "9999-99-99"))

    return all_concerts
