# Spotify Concert Finder

A web app that shows upcoming San Francisco concerts from artists in your Spotify listening history.

## Setup

### 1. Create API Credentials

#### Spotify
1. Go to https://developer.spotify.com/dashboard
2. Create a new app
3. Add redirect URI: `http://localhost:5000/callback`
4. Copy your Client ID and Client Secret

#### Ticketmaster
1. Go to https://developer.ticketmaster.com
2. Create an account and get an API key

### 2. Configure Environment

```bash
cd spotify-concerts
cp .env.example .env
```

Edit `.env` with your credentials:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
TICKETMASTER_API_KEY=your_api_key
FLASK_SECRET_KEY=any_random_string
```

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the App

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Usage

1. Click "Connect with Spotify" on the landing page
2. Authorize the app to access your Spotify data
3. View upcoming concerts from your top artists in San Francisco
4. Click "Get Tickets" to purchase tickets on Ticketmaster

## Project Structure

```
spotify-concerts/
├── app.py              # Flask application
├── spotify.py          # Spotify API integration
├── ticketmaster.py     # Ticketmaster API integration
├── templates/
│   ├── base.html       # Base template
│   ├── index.html      # Landing page
│   └── concerts.html   # Results page
├── static/
│   └── style.css       # Styling
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## How It Works

1. **OAuth Authentication**: User authorizes the app to read their Spotify data
2. **Fetch Top Artists**: App retrieves top artists across short, medium, and long-term listening history
3. **Search Concerts**: For each artist, the app queries Ticketmaster for San Francisco events
4. **Display Results**: Matching concerts are displayed with dates, venues, and ticket links
