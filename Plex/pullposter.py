import argparse
import re
import requests
import sys

from bs4 import BeautifulSoup
from random import choice
from time import sleep

type = None

UAS = [
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)",
    "Mozilla/4.0 (Compatible; MSIE 8.0; Windows NT 5.2; Trident/6.0)","Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)"
]

def help():
    print("Example: python3 pullposter.py movie -i 26347")

def get_tmdb(title, category):
    if 'Season' in title:
        title = title.split(' - Season')[0]
    year = re.search(r'\d{4}', title.split(' ')[-1]).group()
    title = ' '.join(title.split(' ')[:-1])
    url = f'https://api.themoviedb.org/3/search/{category}?query={title}&include_adult=false&language=en-US&page=1&year={year}'
    ua = choice(UAS)
    auth_key = <auth_key>
    headers = {'User-Agent': ua, 'Authorization': f'Bearer {auth_key}', 'Accept': 'application/json'}

    try:
        with requests.Session() as session:
            response = session.get(url, headers=headers)
            response.raise_for_status()
            json_data = response.json()
        
        if category == 'tv':
            tvdb_id_url = f'https://api.themoviedb.org/3/tv/{json_data["results"][0]["id"]}/external_ids'
            with requests.Session() as session:
                response = session.get(tvdb_id_url, headers=headers)
                response.raise_for_status()
                json_data = response.json()
            return str(json_data['tvdb_id'])
        else:
            return str(json_data['results'][0]['id'])
    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"Error fetching TMDB data: {e}")
        return None

def fetch_poster(url):
    ua = choice(UAS)
    headers = {'User-Agent': ua}

    try:
        with requests.Session() as session:
            r = session.get(url, headers=headers)
            r.raise_for_status()
            filename = r.headers['content-disposition'].split('filename="')[1][:-1]
            ext = filename.rsplit('.', 1)[1]
            return r.content, filename, ext
    except requests.RequestException as e:
        print(f"Error fetching poster from {url}: {e}")
        return None, None, None

def save_poster(poster_content, output_path):
    try:
        with open(output_path, 'wb') as f:
            f.write(poster_content)
        return True
    except IOError as e:
        print(f"Error saving poster to {output_path}: {e}")
        return False

def handle_single(poster_id):
    global type
    
    try:
        int(poster_id)
    except ValueError:
        print(f"Invalid poster ID: {poster_id}")
        return
    
    url_poster = f"https://theposterdb.com/api/assets/{poster_id}/view"
    poster_content, filename, ext = fetch_poster(url_poster)
    
    if poster_content and filename and ext:
        if type == "movie":
            movie = filename.split(f".{ext}")[0]
            if movie.endswith("Collection"):
                handle_collection(poster_content, filename, ext)
            else:
                tmdb_id = get_tmdb(movie, 'movie')
                if tmdb_id:
                    save_path = f"assets/movies/{filename}"
                    saved = save_poster(poster_content, save_path)
                    if saved:
                        print(f"  #{movie}\n  {tmdb_id}:\n    file_poster: \"config/assets/movies/{filename}\"")
        
        if type == "season":
            show_title = filename.split(' - Season')[0]
            tvdb_id = get_tmdb(show_title, 'tv')
            num = re.findall(r'\d+', filename)[-1]
            if tvdb_id:
                num2 = "%02d" % (int(num),)
                save_path = f"assets/tv_shows/{show_title}_Season{num2}.{ext}"
                saved = save_poster(poster_content, save_path)
                if saved:
                    print(f"      {num}:\n        file_poster: \"config/assets/tv_shows/{show_title}_Season{num2}.{ext}\"")

def handle_set(poster_id):
    global type

    try:
        int(poster_id)
    except ValueError:
        print(f"Invalid poster ID: {poster_id}")
        return

    tpdb_set = {}
    url = f"https://theposterdb.com/set/{poster_id}"
    ua = choice(UAS)
    headers = {'User-Agent': ua}
    
    try:
        with requests.Session() as session:
            r = session.get(url, headers=headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features="html.parser")
            base_set = soup.find("div", class_="row d-flex flex-wrap m-0 w-100 mx-n1 mt-n1")
            for movie in base_set.find_all("div", class_="overlay rounded-poster"):
                movie_id = movie.attrs['data-poster-id']
                title = movie.p.text
                poster_url = f"https://theposterdb.com/api/assets/{movie_id}/view"
                tpdb_set[title] = poster_url

        if type == "collection":
            movie, url_poster = list(tpdb_set.items())[0]
            poster_content, filename, ext = fetch_poster(url_poster)
            handle_collection(poster_content, filename, ext)
        print(f"  #reference: https://theposterdb.com/set/{poster_id}")
        for movie, url_poster in list(tpdb_set.items())[1:]:
            poster_content, filename, ext = fetch_poster(url_poster)
            if poster_content and filename and ext:
                movie = filename.split(f".{ext}")[0]
                tmdb_id = get_tmdb(movie, 'movie')
                if tmdb_id:
                    save_path = f"assets/movies/{filename}"
                    saved = save_poster(poster_content, save_path)
                    if saved:
                        print(f"  #{movie}\n  {tmdb_id}:\n    file_poster: \"config/assets/movies/{filename}\"")

    except (requests.RequestException, AttributeError) as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()

        print(f"Error fetching set data (line {exc_tb.tb_lineno}): {e}")

def handle_collection(poster_content, filename, ext):
    collection = filename.split(f".{ext}")[0]
    collection = ' '.join(collection.split(' ')[:-1])
    save_path = f"assets/collections/{filename}"
    saved = save_poster(poster_content, save_path)
    if saved:
        print(f"  {collection}:\n    file_poster: \"config/assets/collections/{filename}\"")

def handle_show(poster_id):
    try:
        int(poster_id)
    except ValueError:
        print(f"Invalid poster ID: {poster_id}")
        return

    tpdb_set = {}
    url = f"https://theposterdb.com/set/{poster_id}"
    ua = choice(UAS)
    headers = {'User-Agent': ua}
    
    try:
        with requests.Session() as session:
            r = session.get(url, headers=headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features="html.parser")
            base_set = soup.find("div", class_="row d-flex flex-wrap m-0 w-100 mx-n1 mt-n1")
            for show in base_set.find_all("div", class_="overlay rounded-poster"):
                show_id = show.attrs['data-poster-id']
                title = show.p.text
                poster_url = f"https://theposterdb.com/api/assets/{show_id}/view"
                tpdb_set[title] = poster_url

        show_title = sorted(tpdb_set, key=len)[0]
        if 'Season' in show_title:
            show_title = show_title.split(' - Season')[0]
        tmdb_id = get_tmdb(show_title, 'tv')

        for show, url_poster in tpdb_set.items():
            poster_content, filename, ext = fetch_poster(url_poster)
            if poster_content and filename and ext:
                if "Specials" in show:
                    num = '0'
                elif "Season" in show:
                    num = re.findall(r'\d+', show)[-1]
                else:
                    num = '-1'
                if num == '-1':
                    save_path = f"assets/tv_shows/{filename}"
                    saved = save_poster(poster_content, save_path)
                    if saved:
                        print(f"  #{show_title}\n  {tmdb_id}:\n    #reference: https://theposterdb.com/set/{poster_id}\n    file_poster: \"config/assets/tv_shows/{filename}\"")
                elif int(num) == 1:
                    num2 = "%02d" % (int(num),)
                    save_path = f"assets/tv_shows/{show_title}_Season{num2}.{ext}"
                    saved = save_poster(poster_content, save_path)
                    if saved:
                        print(f"    seasons:\n      {num}:\n        file_poster: \"config/assets/tv_shows/{show_title}_Season{num2}.{ext}\"")
                else:
                    num2 = "%02d" % (int(num),)
                    save_path = f"assets/tv_shows/{show_title}_Season{num2}.{ext}"
                    saved = save_poster(poster_content, save_path)
                    if saved:
                        print(f"      {num}:\n        file_poster: \"config/assets/tv_shows/{show_title}_Season{num2}.{ext}\"")

    except (requests.RequestException, AttributeError) as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        
        print(f"Error fetching show data (line {exc_tb.tb_lineno}): {e}")

def get_pics(poster_id=None):
    global type

    handlers = {
        'movie': handle_single,
        'season': handle_single,
        'set': handle_set,
        'collection': handle_set,
        'show': handle_show,
        'collection poster': handle_single,
    }

    if poster_id is None:
        poster_id = input("What is the TPDB set ID: ")

    if type in handlers:
        handlers[type](poster_id)
    else:
        print(f"Unknown type '{type}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="PosterPull",
        description="Retrieves and saves posters from ThePosterDB based on ID"
    )
    parser.add_argument('type', choices=['movie', 'season', 'set', 'show', 'collection', 'collection poster'],
                        help='Type of poster to retrieve: movie, set, show, collection, collection poster')
    parser.add_argument('-i', '--id', type=str, help='ID of the poster set')

    args = parser.parse_args()

    #global type
    type = args.type

    if not type:
        print('Type must be "movie" or "episode" or "show" or "set" or "collection" exactly...')
        help()
    else:
        get_pics(args.id)
