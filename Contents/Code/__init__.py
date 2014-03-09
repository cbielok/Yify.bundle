NAME = 'Yify'
BASE_URL = 'http://yify.tv'
RELEASES_URL = '%s/files/releases/page/%%d/' % BASE_URL
POPULAR_URL = '%s/popular/page/%%d/' % BASE_URL
TOP250_URL = '%s/files/movies/page/%%d/?meta_key=imdbRating&orderby=meta_value&order=desc' % BASE_URL
GENRE_URL = '%s/genre/%%s/page/%%%%d/' % BASE_URL

RE_POSTS = Regex('var posts = ({.+});')

ART = 'art-default.jpg'
ICON = 'icon-default.jpg'

####################################################################################################
def Start():

	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = NAME
	DirectoryObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'
	HTTP.Headers['Referer'] = 'http://yify.tv/'

####################################################################################################
@handler('/video/yify', NAME, thumb=ICON, art=ART)
def MainMenu():

	oc = ObjectContainer()
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Releases', url=RELEASES_URL), title='Releases'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Popular', url=POPULAR_URL), title='Popular'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Top +250', url=TOP250_URL), title='Top +250'))
	oc.add(DirectoryObject(key = Callback(ListGenres), title='Genres'))
	oc.add(DirectoryObject(key = Callback(Watchlist), title='Watchlist'))
	oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.yify', title='Search', summary='Search Movies on Yify', prompt='Search for...'))

	if Client.Product != 'PlexConnect':
		oc.add(PrefsObject(title='Preferences'))

	return oc

####################################################################################################
@route('/video/yify/listmovies', page=int)
def ListMovies(title, url, page=1):

	oc = ObjectContainer(title2=title)
	data = HTTP.Request(url % page).content
	json = RE_POSTS.search(data)

	html = HTML.ElementFromString(data)

	if json:
		json_obj = JSON.ObjectFromString(json.group(1))

		for movie in json_obj['posts']:

			movie_url = movie['link']
			movie_title = movie['title']
			movie_thumb = movie['image']

			try: movie_summary = movie['post_content']
			except: movie_summary = None

			try: year = int(movie['year'])
			except: year = None

			oc.add(MovieObject(
				url = movie_url,
				title = movie_title,
				summary = movie_summary,
				thumb = Resource.ContentsOfURLWithFallback(url=movie_thumb, fallback='icon-default.jpg')
			))

	else:
		for movie in html.xpath('//article[@class="posts3"]'):

			movie_url = movie.xpath('.//img/parent::a/@href')[0]
			movie_title = movie.xpath('.//h2/text()')[0]
			movie_thumb = movie.xpath('.//img/@src')[0]

			try: movie_summary = movie.xpath('.//h1/text()')[0].split('\n')[0].strip()
			except: movie_summary = None

			try: year = int(movie.xpath('.//h2//a/text()')[0])
			except: year = None

			oc.add(MovieObject(
				url = movie_url,
				title = movie_title,
				summary = movie_summary,
				thumb = Resource.ContentsOfURLWithFallback(url=movie_thumb, fallback='icon-default.jpg')
			))

	if len(html.xpath('//a[@class="nextpostslink"]')) > 0:

		if page % 5 != 0:
			oc.extend(ListMovies(title=title, url=url, page=page+1))

		else:
			oc.add(NextPageObject(
				key = Callback(ListMovies, title=title, url=url, page=page+1),
				title = L('More...')
			))

	return oc

####################################################################################################
@route('/video/yify/listgenres')
def ListGenres():

	oc = ObjectContainer(title2='Genres')

	oc.add(DirectoryObject(key = Callback(ListMovies, title='Action', url=GENRE_URL % 'action'), title='Action'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Animation', url=GENRE_URL % 'animation'), title='Animation'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Comedy', url=GENRE_URL % 'comedy'), title='Comedy'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Documentary', url=GENRE_URL % 'documentary'), title='Documentary'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Drama', url=GENRE_URL % 'drama'), title='Drama'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Family', url=GENRE_URL % 'family'), title='Family'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Horror', url=GENRE_URL % 'horror'), title='Horror'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Mystery', url=GENRE_URL % 'mystery'), title='Mystery'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Romance', url=GENRE_URL % 'romance'), title='Romance'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Science fiction', url=GENRE_URL % 'sci-fi'), title='Science fiction'))
	oc.add(DirectoryObject(key = Callback(ListMovies, title='Thriller', url=GENRE_URL % 'thriller'), title='Thriller'))

	return oc

####################################################################################################
@route('/video/yify/watchlist')
def Watchlist():

	if not Login():
		return ObjectContainer(header="Login failed", message="Check your username and password")

	oc = ObjectContainer(title2='Watchlist', no_cache=True)

	post_values = {
		'a': 'get_lists',
		'ajax': '1'
	}

	cookies = HTTP.CookiesForURL(BASE_URL)
	json_obj = JSON.ObjectFromURL(BASE_URL, values=post_values, headers={'Cookie': cookies})

	for list in json_obj:
		id = list['ID']
		title = list['titulo']

		oc.add(DirectoryObject(key = Callback(WatchlistMovies, id=id, title=title), title=title))

	return oc

####################################################################################################
@route('/video/yify/watchlistmovies')
def WatchlistMovies(id, title):

	if not Login():
		return ObjectContainer(header="Login failed", message="Check your username and password")

	oc = ObjectContainer(title2=title, no_cache=True)

	post_values = {
		'listid': id,
		'a': 'get_posts_from_list',
		'ajax': '1'
	}

	cookies = HTTP.CookiesForURL(BASE_URL)
	json_obj = JSON.ObjectFromURL(BASE_URL, values=post_values, headers={'Cookie': cookies})

	for movie in json_obj['posts']:

		if not 'ID' in movie or not 'link' in movie or not 'title' in movie or not 'image' in movie:
			continue

		movie_url = movie['link']
		movie_title = movie['title']
		movie_thumb = movie['image']

		try: movie_summary = movie['post_content']
		except: movie_summary = None

		try: year = int(movie['year'])
		except: year = None

		oc.add(MovieObject(
			url = movie_url,
			title = movie_title,
			summary = movie_summary,
			thumb = Resource.ContentsOfURLWithFallback(url=movie_thumb, fallback='icon-default.jpg')
		))

	return oc

####################################################################################################
@route('/video/yify/login')
def Login():

	if Prefs['username'] and Prefs['password']:

		HTTP.ClearCookies()

		post_values = {
			'log': Prefs['username'],
			'pwd': Prefs['password'],
			'a': 'login',
			'ajax': '1'
		}

		json = HTTP.Request(BASE_URL, values=post_values).content
		json = json.replace("'", '"')
		json_obj = JSON.ObjectFromString(json)

		if 'status' in json_obj and json_obj['status'] == 'OK':
			return True

	return False
