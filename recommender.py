import streamlit as st
import pickle
import numpy as np
import pandas as pd
import requests
import time
import random
import html

st.set_page_config(page_title="CineMatch", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600&display=swap');

    .stApp { background-color: #141414; color: white; }
    #MainMenu, footer, header {visibility: hidden;}

    .netflix-title {
        font-family: 'Bebas Neue', cursive;
        font-size: 3.5rem; color: #E50914;
        letter-spacing: 4px; text-align: center;
        text-shadow: 0 0 30px rgba(229,9,20,0.4);
    }
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem; color: #888;
        text-align: center; letter-spacing: 3px;
        text-transform: uppercase; margin-bottom: 2rem;
    }
    .stSelectbox > div > div {
        background-color: #2a2a2a !important;
        border: 1px solid #E50914 !important;
        border-radius: 6px !important; color: white !important;
    }
    .stButton > button {
        background: #E50914 !important; color: white !important;
        font-family: 'Bebas Neue', cursive !important;
        font-size: 1.2rem !important; letter-spacing: 2px !important;
        border: none !important; border-radius: 6px !important;
        padding: 0.6rem 3rem !important; width: 100% !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: #ff1a1a !important; transform: scale(1.02) !important;
        box-shadow: 0 0 20px rgba(229,9,20,0.5) !important;
    }
    .movie-card {
        background: #1f1f1f; border-radius: 10px;
        overflow: hidden; transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #2a2a2a; height: 100%;
    }
    .movie-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 30px rgba(229,9,20,0.3);
        border-color: #E50914;
    }
    .movie-card img { width: 100%; }
    .movie-info {
        padding: 10px 8px; background: #1f1f1f;
    }
    .movie-name {
        font-family: 'Inter', sans-serif; font-size: 0.85rem;
        font-weight: 600; color: white; text-align: center;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .movie-rating {
        font-family: 'Inter', sans-serif; font-size: 0.78rem;
        color: #f5c518; text-align: center; margin-top: 4px;
    }
    .section-header {
        font-family: 'Bebas Neue', cursive; font-size: 1.8rem;
        color: white; letter-spacing: 2px; margin: 1.5rem 0 1rem 0;
        border-left: 4px solid #E50914; padding-left: 12px;
    }
    .watchlist-badge {
        background: #E50914; color: white; border-radius: 20px;
        padding: 2px 10px; font-size: 0.75rem; font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    .overview-box {
        background: #2a2a2a; border-radius: 8px;
        padding: 12px; font-family: 'Inter', sans-serif;
        font-size: 0.85rem; color: #ccc; line-height: 1.5;
        margin-top: 6px; border-left: 3px solid #E50914;
    }
    .trending-badge {
        background: linear-gradient(90deg, #E50914, #ff6b35);
        color: white; border-radius: 4px; padding: 2px 8px;
        font-size: 0.7rem; font-weight: 700;
        font-family: 'Inter', sans-serif; letter-spacing: 1px;
    }
    hr { border-color: #2a2a2a !important; }
    .stSpinner > div { border-top-color: #E50914 !important; }
    .stExpander {
        background: #1f1f1f !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


# ==================== API FUNCTIONS ====================

session = requests.Session()
NO_POSTER = "https://placehold.co/500x750/1f1f1f/888?text=No+Poster"

# TMDB API key: read from .streamlit/secrets.toml (TMDB_API_KEY = "...") if present,
# otherwise fall back to the default key below.
try:
    API_KEY = st.secrets["TMDB_API_KEY"]
except Exception:
    API_KEY = "7db5441aa6a9110866d8afa35e432cf6"

@st.cache_data(show_spinner=False, ttl=24 * 3600)
def fetch_poster(movie_id):
    for attempt in range(3):
        try:
            response = session.get(
                f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US',
                timeout=10
            )
            data = response.json()
            if 'poster_path' in data and data['poster_path']:
                return "https://image.tmdb.org/t/p/w500" + data['poster_path']
            return NO_POSTER
        except Exception:
            time.sleep(1)
    return "https://placehold.co/500x750/1f1f1f/888?text=Error"


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def fetch_movie_details(movie_id):
    """✅ NEW: Fetch rating + overview for popup"""
    try:
        response = session.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US',
            timeout=10
        )
        data = response.json()
        return {
            'rating': round(data.get('vote_average', 0), 1),
            'overview': data.get('overview', 'No overview available.'),
            'poster': "https://image.tmdb.org/t/p/w500" + data['poster_path'] if data.get('poster_path') else None,
            'genres': ", ".join([g['name'] for g in data.get('genres', [])]),
            'year': (data.get('release_date') or '')[:4] or 'N/A'
        }
    except Exception:
        return {'rating': 0, 'overview': 'N/A', 'poster': None, 'genres': 'N/A', 'year': 'N/A'}


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_trending():
    """✅ NEW: Fetch trending movies from TMDB"""
    try:
        response = session.get(
            f'https://api.themoviedb.org/3/trending/movie/week?api_key={API_KEY}',
            timeout=10
        )
        data = response.json()
        results = data.get('results', [])[:5]
        trending = []
        for m in results:
            trending.append({
                'title': m['title'],
                'poster': "https://image.tmdb.org/t/p/w500" + m['poster_path'] if m.get('poster_path') else NO_POSTER,
                'rating': round(m.get('vote_average', 0), 1),
                'id': m['id']
            })
        return trending
    except Exception:
        return []


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    # Top 5 most similar movies (cosine similarity, precomputed in top_matches.npy)
    movies_list = top_matches[movie_index]

    recommended_movies = []
    recommended_posters = []
    recommended_ids = []
    # The dataset contains a few duplicate rows (same movie twice), so skip the selected
    # movie itself and any movie already recommended, and stop at 5.
    seen_ids = {int(movies.iloc[movie_index].id)}

    for i in movies_list:
        movie_id = int(movies.iloc[i].id)
        if movie_id in seen_ids:
            continue
        seen_ids.add(movie_id)
        movie_title = movies.iloc[i].title
        recommended_movies.append(movie_title)
        recommended_posters.append(fetch_poster(movie_id))
        recommended_ids.append(movie_id)
        if len(recommended_ids) == 5:
            break

    return recommended_movies, recommended_posters, recommended_ids


# ==================== LOAD DATA ====================

@st.cache_resource(show_spinner=False)
def load_data():
    with open('Movies_d.pkl', 'rb') as f:
        # reset_index: the saved DataFrame has gaps in its row labels (rows were dropped in
        # the notebook), but top_matches is indexed by row POSITION. Without this, 45% of
        # movies got another movie's recommendations and 3 movies crashed the app.
        movies_df = pd.DataFrame(pickle.load(f)).reset_index(drop=True)
    # For each movie, the indices of its 10 most similar movies. Built from the
    # full cosine-similarity matrix (185 MB) so the app stays small enough for GitHub.
    matches = np.load('top_matches.npy')
    return movies_df, matches

movies, top_matches = load_data()


# ==================== WATCHLIST ====================
# Each saved movie is a dict {'id', 'title', 'poster'} identified by its TMDB id
# (titles are not unique, e.g. two different films called "Batman").
# The list lives in st.session_state and is mirrored to the page URL
# (?watchlist=19995,285) so it survives a page refresh.

def save_watchlist_to_url():
    ids = ",".join(str(m['id']) for m in st.session_state.watchlist)
    if ids:
        st.query_params["watchlist"] = ids
    elif "watchlist" in st.query_params:
        del st.query_params["watchlist"]


def load_watchlist_from_url():
    """Rebuild the watchlist from the URL. Returns (items, number_of_invalid_entries)."""
    items, skipped = [], 0
    for part in st.query_params.get("watchlist", "").split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            skipped += 1
            continue
        movie_id = int(part)
        match = movies[movies['id'] == movie_id]
        if match.empty:
            skipped += 1
            continue
        if any(m['id'] == movie_id for m in items):
            continue
        items.append({'id': movie_id, 'title': match.iloc[0].title, 'poster': fetch_poster(movie_id)})
    return items, skipped


def add_to_watchlist(movie_id, title, poster):
    """Returns 'added', 'duplicate' or 'error'."""
    try:
        movie_id = int(movie_id)
    except (TypeError, ValueError):
        return 'error'
    if not title:
        return 'error'
    if any(m['id'] == movie_id for m in st.session_state.watchlist):
        return 'duplicate'
    st.session_state.watchlist.append({'id': movie_id, 'title': str(title), 'poster': poster or NO_POSTER})
    save_watchlist_to_url()
    return 'added'


def remove_from_watchlist(movie_id):
    """Returns True if the movie was found and removed."""
    before = len(st.session_state.watchlist)
    st.session_state.watchlist = [m for m in st.session_state.watchlist if m['id'] != movie_id]
    save_watchlist_to_url()
    return len(st.session_state.watchlist) < before


# ✅ Watchlist + current recommendations stored in session state
if 'watchlist' not in st.session_state:
    st.session_state.watchlist, skipped = load_watchlist_from_url()
    if skipped:
        st.session_state.watchlist_msg = ('warning', f"{skipped} saved item(s) could not be restored and were skipped.")
    save_watchlist_to_url()
if 'recs' not in st.session_state:
    st.session_state.recs = None


# ==================== HEADER ====================

st.markdown('<p class="netflix-title">🎬 CineMatch</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your Personal Movie Recommender</p>', unsafe_allow_html=True)
st.markdown("---")


# ==================== TABS ====================

tab1, tab2, tab3 = st.tabs(["🔍 Recommend", "🔥 Trending", "❤️ Watchlist"])


# ==================== TAB 1: RECOMMEND ====================

with tab1:
    col_a, col_b, col_c = st.columns([1, 3, 1])
    with col_b:
        selected_movie_name = st.selectbox("🎬 Search a Movie", movies['title'].unique())

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            clicked = st.button("GET RECOMMENDATIONS")
        with col_btn2:
            random_clicked = st.button("🎲 SURPRISE ME")   # ✅ NEW: Random movie

    # ✅ Random movie button
    if random_clicked:
        selected_movie_name = random.choice(movies['title'].unique())
        st.info(f"🎲 Randomly picked: **{selected_movie_name}**")
        clicked = True

    if clicked:
        with st.spinner('🎬 Finding your movies...'):
            names, posters, ids = recommend(selected_movie_name)
        # Keep results so they survive the rerun when a Watchlist button is clicked
        st.session_state.recs = {'movie': selected_movie_name, 'names': names,
                                 'posters': posters, 'ids': ids}

    if st.session_state.recs:
        recs = st.session_state.recs
        selected_movie_name = recs['movie']
        names, posters, ids = recs['names'], recs['posters'], recs['ids']

        st.markdown(f'<p class="section-header">Because you watched: {html.escape(selected_movie_name)}</p>',
                    unsafe_allow_html=True)

        cols = st.columns(5)
        for idx, (col, name, poster, mid) in enumerate(zip(cols, names, posters, ids)):
            with col:
                # Movie card
                st.markdown(f"""
                    <div class="movie-card">
                        <img src="{poster or NO_POSTER}" />
                        <div class="movie-info">
                            <div class="movie-name">{html.escape(str(name or 'Unknown title'))}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # ✅ NEW: Movie details expander
                with st.expander("ℹ️ Details"):
                    details = fetch_movie_details(mid)
                    st.markdown(f"⭐ **Rating:** {details['rating']}/10")
                    st.markdown(f"📅 **Year:** {details['year']}")
                    st.markdown(f"🎭 **Genre:** {details['genres']}")
                    st.markdown(f'<div class="overview-box">{details["overview"]}</div>',
                                unsafe_allow_html=True)

                # ✅ NEW: Add to Watchlist button
                if st.button("➕ Add to Watchlist", key=f"watch_{idx}"):
                    result = add_to_watchlist(mid, name, poster)
                    if result == 'added':
                        st.success("Added! Open the ❤️ Watchlist tab to see it.")
                    elif result == 'duplicate':
                        st.warning("Already in watchlist!")
                    else:
                        st.error("Could not add this movie. Please try again.")


# ==================== TAB 2: TRENDING ====================

with tab2:
    st.markdown('<p class="section-header">🔥 Trending This Week</p>', unsafe_allow_html=True)

    with st.spinner("Loading trending movies..."):
        trending = fetch_trending()

    if trending:
        cols = st.columns(5)
        for col, movie in zip(cols, trending):
            with col:
                st.markdown(f"""
                    <div class="movie-card">
                        <img src="{movie['poster']}" />
                        <div class="movie-info">
                            <div class="movie-name">{movie['title']}</div>
                            <div class="movie-rating">⭐ {movie['rating']}/10</div>
                        </div>
                    </div>
                    <br/>
                """, unsafe_allow_html=True)
    else:
        st.warning("Could not load trending movies. Check your API key.")


# ==================== TAB 3: WATCHLIST ====================

with tab3:
    st.markdown('<p class="section-header">❤️ My Watchlist</p>', unsafe_allow_html=True)

    # Message from the previous action (remove / clear / restore), shown once
    msg = st.session_state.pop('watchlist_msg', None)
    if msg:
        getattr(st, msg[0])(msg[1])

    if not st.session_state.watchlist:
        st.info("💡 Your watchlist is empty! Add movies from the Recommend tab.")
    else:
        st.markdown(f'<span class="watchlist-badge">{len(st.session_state.watchlist)} Movies Saved</span>',
                    unsafe_allow_html=True)
        st.write("")

        cols = st.columns(5)
        to_remove = None

        for idx, item in enumerate(st.session_state.watchlist):
            with cols[idx % 5]:
                st.markdown(f"""
                    <div class="movie-card">
                        <img src="{item['poster']}" />
                        <div class="movie-info">
                            <div class="movie-name">{html.escape(item['title'])}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander("ℹ️ Details"):
                    details = fetch_movie_details(item['id'])
                    st.markdown(f"⭐ **Rating:** {details['rating']}/10")
                    st.markdown(f"📅 **Year:** {details['year']}")
                    st.markdown(f"🎭 **Genre:** {details['genres']}")
                    st.markdown(f'<div class="overview-box">{details["overview"]}</div>',
                                unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"remove_{item['id']}"):
                    to_remove = item
                st.write("")

        if to_remove is not None:
            if remove_from_watchlist(to_remove['id']):
                st.session_state.watchlist_msg = ('success', f"Removed \"{to_remove['title']}\" from your watchlist.")
            else:
                st.session_state.watchlist_msg = ('error', "Could not remove this movie. Please refresh and try again.")
            st.rerun()

        if st.button("🗑️ Clear Entire Watchlist"):
            st.session_state.watchlist = []
            save_watchlist_to_url()
            st.session_state.watchlist_msg = ('success', "Watchlist cleared.")
            st.rerun()
