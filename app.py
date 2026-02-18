"""Flask application for Spotify Concert Finder."""

import os
from flask import Flask, render_template, redirect, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

import spotify
import ticketmaster

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# Fix for running behind a proxy (Render, Heroku, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


def get_redirect_uri():
    """Get the OAuth redirect URI."""
    # Use environment variable if set, otherwise auto-detect
    base_url = os.environ.get("BASE_URL")
    if base_url:
        return f"{base_url}/callback"
    return url_for("callback", _external=True)


@app.route("/")
def index():
    """Landing page with Spotify login button."""
    logged_in = "access_token" in session
    return render_template("index.html", logged_in=logged_in)


@app.route("/login")
def login():
    """Redirect to Spotify authorization."""
    auth_url = spotify.get_auth_url(get_redirect_uri())
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handle Spotify OAuth callback."""
    error = request.args.get("error")
    if error:
        return render_template("index.html", error=f"Authorization failed: {error}")

    code = request.args.get("code")
    if not code:
        return render_template("index.html", error="No authorization code received")

    try:
        token_data = spotify.exchange_code_for_token(code, get_redirect_uri())
        session["access_token"] = token_data["access_token"]
        return redirect(url_for("concerts"))
    except Exception as e:
        return render_template("index.html", error=f"Token exchange failed: {str(e)}")


@app.route("/concerts")
def concerts():
    """Display concerts for user's top artists."""
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    # Get city from query param or session, default to San Francisco
    city = request.args.get("city")
    if city:
        session["city"] = city
    else:
        city = session.get("city", "San Francisco")

    try:
        # Fetch user's top artists
        artists = spotify.get_all_top_artists(access_token)

        # Find concerts for those artists in selected city
        concert_list = ticketmaster.find_concerts_for_artists(artists, city=city)

        return render_template(
            "concerts.html",
            concerts=concert_list,
            artist_count=len(artists),
            city=city,
        )
    except Exception as e:
        return render_template(
            "concerts.html",
            concerts=[],
            artist_count=0,
            city=city,
            error=str(e),
        )


@app.route("/logout")
def logout():
    """Clear session and redirect to home."""
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
