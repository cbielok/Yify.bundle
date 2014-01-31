NAME = 'Yify'
BASE_URL = 'http://yify.tv'
RELEASES_URL = '%s/files/releases/page/%%d/' % BASE_URL
POPULAR_URL = '%s/popular/page/%%d/' % BASE_URL
TOP250_URL = '%s/files/movies/page/%%d/?meta_key=imdbRating&orderby=meta_value&order=desc' % BASE_URL

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

	return oc

####################################################################################################
@route('/video/yify/listmovies', page=int)
def ListMovies(title, url, page=1):

	oc = ObjectContainer(title2=title)
	html = HTML.ElementFromURL(url % page)

	for movie in html.xpath('//article[@class="posts3"]'):

		movie_url = movie.xpath('.//img/parent::a/@href')[0]
		movie_title = movie.xpath('.//h2/text()')[0]
		movie_summary = movie.xpath('.//h1/text()')[0].split('\n')[0].strip()
		movie_thumb = movie.xpath('.//img/@src')[0]

		try: year = int(movie.xpath('.//h2//a/text()')[0])
		except: year = None

		oc.add(MovieObject(
			url = movie_url,
			title = movie_title,
			summary = movie_summary,
			thumb = Resource.ContentsOfURLWithFallback(url=movie_thumb, fallback='icon-default.jpg')
		))

	if len(html.xpath('//a[@class="nextpostslink"]')) > 0:

		oc.add(NextPageObject(
			key = Callback(ListMovies, title=title, url=url, page=page+1),
			title = L('More...')
		))

	return oc
