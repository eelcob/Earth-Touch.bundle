VIDEO_PREFIX      = "/video/earthtouch"
ART 			= 'art-default.jpg'
ICON 			= 'icon-default.png'
NAME 			= "Earth Touch"
ICON_SEARCH 	= "search.png"

BASE			= "http://www.earth-touch.com"
SHOWS			= BASE + "/shows"
LOGIN			= BASE + "/user/login/"
AGE				= BASE + "/age-gate/"

NAMESPACES_A   = {
    'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd',
    'media':'http://search.yahoo.com/mrss/',
    'feedburner':'http://rssnamespace.org/feedburner/ext/1.0'
}

## Age gate support is in here but till validation that we can show graphic footage is disabled.
####################################################################################################
def Start():

	Plugin.AddPrefixHandler("/video/earthtouch", MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('Details', viewMode='InfoList', mediaType='items')

	ObjectContainer.title1 = NAME
	ObjectContainer.view_group = 'List'
	ObjectContainer.art = R(ART)
	
	VideoClipObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:13.0) Gecko/20100101 Firefox/13.0.1'

####################################################################################################
def MainMenu():
	oc = ObjectContainer()

	for shows in HTML.ElementFromURL(SHOWS).xpath('//div[@class="show-block"]'):
		show_title 	= shows.xpath('./div[@class="show-overlay"]/h3')[0].text
		show_thumb	= BASE + shows.xpath('./div[@class="show-img"]/img')[0].get('src')
		show_descr	= shows.xpath('./div[@class="show-overlay"]/p')[0].text
		show_link	= BASE + shows.xpath('./div[@class="show-overlay"]/a')[0].get('href')

		oc.add(DirectoryObject(key = Callback(getVideos, url=show_link), title=show_title, summary=show_descr, thumb=Resource.ContentsOfURLWithFallback(url=show_thumb, fallback=ICON)))

	oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.earthtouch", title = L('Search'), prompt = L('Search'), thumb = R(ICON_SEARCH)))
	
		
	return oc

####################################################################################################
def getVideos(url):

	oc = ObjectContainer()
	
	mrssurl = url + "mrss"
	rssurl	= url + "?rss"

# Below code is part of the age-gate pass... enable to pass age-gate	
#	content = HTTP.Request(AGE, values=dict(
#		year = "1980",
#		month = "1",
#		day = "1"
#		))
#	cookies = HTTP.CookiesForURL(AGE)
#	session_cookie = {"Cookie": cookies}
	
	try:
	    for video in XML.ElementFromURL(mrssurl).xpath('//item', namespaces=NAMESPACES_A):
			# Get MRSS feed for clip info
			title 	= video.xpath('title')[0].text.strip()
			link 	= video.xpath('link')[0].text.strip()
			try:
				thumb 	= video.xpath('media:thumbnail', namespaces=NAMESPACES_A)[0].get('url')
			except:
				thumb = ""			
			try:
				descr	= video.xpath('description')[0].text.strip()
			except:
				descr = ""
			try:
				reldate	= Datetime.ParseDate(video.xpath('pubDate')[0].text)
			except:
				reldate = Datetime.Now()
			try:
				duration = TimeToMilliseconds(video.xpath('media:content', namespaces=NAMESPACES_A)[0].get('duration'))
			except:
				duration = 0
			try:
				explicit	= video.xpath('media:rating', namespaces=NAMESPACES_A)[0].text
			except:
				explicit	= "no"
			
			if explicit == "adult":
				oc	= ObjectContainer(header = "Error", message = "Graphical content found, not able to play")
				continue
			else:			
				oc.add(VideoClipObject(
					url = link,
					title = title,
					summary = descr,
					duration = duration,
					originally_available_at = reldate,
					thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
				))
	except:
		try:
			### Get the rss feed here, less info but mrss seems to break now and then.
		
			# Below code will pass the Age-Gate for 18+ content
			#resp = HTTP.Request(rssurl, headers = session_cookie, cacheTime=0).content
			#for rssvideo in XML.ElementFromString(resp).xpath('//item')
			
			for rssvideo in XML.ElementFromURL(rssurl).xpath('//item'):
				
				title 	= rssvideo.xpath('title')[0].text.strip()
				link 	= rssvideo.xpath('link')[0].text.strip()
		
				cdata	= rssvideo.xpath('description/text()')[0]
				cdata	= cdata.strip()
				data	= HTML.ElementFromString(cdata)
				try:
					descr	= data.xpath('p')[0].text
				except:
					descr	= ""
				try:
					thumb	= BASE + data.xpath('img')[0].get('src')
				except:
					thumb 	= ""
				reldate = Datetime.Now()
				duration = 0	
			
				oc.add(VideoClipObject(
					url = link,
					title = title,
					summary = descr,
					duration = duration,
					originally_available_at = reldate,
					thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
				))	
		except:
			oc = ObjectContainer(header = L("Error"), message = L("NeedLogin"))

	return oc
	
###################################################################################################	
def TimeToMilliseconds(time):

	milliseconds  = 0
	duration = time.split(':')
	duration.reverse()

	for i in range(0, len(duration)):
		milliseconds += int(duration[i]) * (60**i) * 1000

	return milliseconds	