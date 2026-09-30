# 🎬 CineMatch – Content-Based Movie Recommender

A Netflix-style movie recommendation web app built with **Python** and **Streamlit**. Pick a movie you like and CineMatch suggests 5 similar movies, with posters, ratings, genres and plot summaries fetched live from the **TMDB API**.

## Features
- **🔍 Recommend:** get 5 similar movies from a catalogue of ~4,800 films (TMDB 5000 dataset)
- **🎲 Surprise Me:** recommendations for a randomly picked movie
- **ℹ️ Movie details:** rating, release year, genres and overview for each recommendation
- **🔥 Trending:** this week's trending movies from TMDB
- **❤️ Watchlist:** save movies, view their details and remove them; duplicates are blocked and the list survives a page refresh (saved in the URL)
- Custom dark, Netflix-inspired UI with hover effects

## How It Works
1. **Data:** the TMDB 5000 Movies and Credits datasets are merged on title.
2. **Feature engineering:** each movie's overview, genres, keywords, cast and crew are combined into a single `tags` text, then lower-cased and stemmed.
3. **Vectorization:** tags are converted into bag-of-words vectors.
4. **Similarity:** cosine similarity between every pair of movies gives a 4806 × 4806 similarity matrix.
5. **Recommendation:** for the selected movie, the 5 movies with the highest similarity score are shown.

> The full similarity matrix is 185 MB, which is too large for GitHub. The app instead ships `top_matches.npy` (96 KB), which stores the indices of each movie's 10 most similar movies taken from that matrix. The recommendations are identical, and the app loads instantly.

## Tech Stack
- Python, Pandas, NumPy
- Scikit-learn (text vectorization, cosine similarity)
- Streamlit (UI, session state, caching)
- TMDB REST API (posters, details, trending)

## Run Locally
```bash
git clone https://github.com/aakashcse/content-based-movie-recommender.git
cd content-based-movie-recommender
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
streamlit run recommender.py
```
The app opens at http://localhost:8501.

### TMDB API Key (optional)
The app includes a default key. To use your own, get a free key at [themoviedb.org](https://www.themoviedb.org/settings/api) and create `.streamlit/secrets.toml`:
```toml
TMDB_API_KEY = "your_key_here"
```
> If posters don't load on an Indian network (e.g. Jio), switch DNS to `8.8.8.8` / `1.1.1.1`, because some ISPs block TMDB.

## Project Structure
```
├── recommender.py      # Streamlit app
├── Movies_d.pkl        # Movie ids, titles and processed tags
├── top_matches.npy     # Top-10 similar movies for each movie
└── requirements.txt
```

## Author
**Aakash Kumar Singh** · [GitHub](https://github.com/aakashcse)
