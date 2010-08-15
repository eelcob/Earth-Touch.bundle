import re, string, datetime

VIDEO_PREFIX      = "/video/earthtouch"

NAMESPACES_A   = {
    'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd',
    'media':'http://search.yahoo.com/mrss/', 
    'feedburner':'http://rssnamespace.org/feedburner/ext/1.0'
}
FEATURED_COMMENTARY = "http://feeds2.feedburner.com/earth-touch_featured_%s_commentary?format=xml"
FEATURED_NO_COMMENTARY = "http://feeds2.feedburner.com/earth-touch_featured_%s?format=xml"
WILDLIFE_HIGHLIGHTS = "http://feeds.feedburner.com/earth-touch_podcast_%s?format=xml"
MARINE_CHANNEL = "http://feeds.feedburner.com/WeeklyMarinePodcast-hd?format=xml"
MOREMI_LIONS_CHANNEL = 'http://feeds.feedburner.com/moremi_podcast_720?format=xml'
KIDS_CHANNEL = "http://feeds2.feedburner.com/kids-hd"
NAMESPACES_B ={
    'dc':'http://purl.org/dc/elements/1.1/',
    'sy':'http://purl.org/rss/1.0/modules/syndication/',
    'admin':'http://webns.net/mvcb/',
    'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'content':'http://purl.org/rss/1.0/modules/content/',
    'media':'http://www.itunes.com/dtds/podcast-1.0.dtd',
    'feedburner':'http://rssnamespace.org/feedburner/ext/1.0'
}
LATEST_STORIES = "http://feeds.feedburner.com/earth-touch_new?format=xml"

ARCHIVE_SEARCH = "http://earth-touch.com/search/search.php?page=%d&SearchString=%s&searchin=Archive&HabitatID=0&LocationID=0&orderby=%d"
DATE_ORDER = 0
HIGHEST_RATED = 1
MOST_VIEWED = 3
VIDEO_PAGE_URL = "http://earth-touch.com/result.php?i=%s"

SD_RES = "480p"
HD_RES = "720p"
USE_HD_PREF_KEY = "usehd"
CACHE_INTERVAL    = 1800
ICON = "icon-default.png"

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenuVideo, "Earth-Touch", ICON, "art-default.png")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.art = R('art-default.png')
  MediaContainer.title1 = 'Earth-Touch'
  HTTP.SetCacheTime(CACHE_INTERVAL)
  
####################################################################################################
def MainMenuVideo():
    dir = MediaContainer(mediaType='video')  
    dir.Append(Function(DirectoryItem(LastestStories, title="Latest Stories", thumb=R(ICON))))
    dir.Append(Function(DirectoryItem(Feed, title="Featured Videos (with commentary)", thumb=R(ICON)), urlFormat = FEATURED_COMMENTARY))
    dir.Append(Function(DirectoryItem(Feed, title="Featured Videos (no commentary)", thumb=R(ICON)), urlFormat = FEATURED_NO_COMMENTARY))
    dir.Append(Function(DirectoryItem(Feed, title="Wildlife Highlights", thumb=R(ICON)), urlFormat = WILDLIFE_HIGHLIGHTS))
    dir.Append(Function(DirectoryItem(Feed, title="Marine Channel HD", thumb=R(ICON)), urlFormat = MARINE_CHANNEL, variableResolution=False))
    dir.Append(Function(DirectoryItem(Feed, title="Moremi Lions Channel HD", thumb=R(ICON)), urlFormat = MOREMI_LIONS_CHANNEL, variableResolution=False))
    dir.Append(Function(DirectoryItem(Feed, title="Kids Channel HD", thumb=R(ICON)), urlFormat = KIDS_CHANNEL, variableResolution=False))
    dir.Append(Function(DirectoryItem(ArchiveBrowse, title="Most Recent in Archive", thumb=R(ICON)), order=DATE_ORDER))
    dir.Append(Function(DirectoryItem(ArchiveBrowse, title="Highest Rated in Archive", thumb=R(ICON)), order=HIGHEST_RATED))
    dir.Append(Function(DirectoryItem(ArchiveBrowse, title="Most Viewed in Archive", thumb=R(ICON)), order=MOST_VIEWED))
    dir.Append(Function(InputDirectoryItem(ArchiveSearch, title=L("Search Archive ..."), prompt=L("Search Archive"), thumb=R('search.png'))))
    dir.Append(PrefsItem(L("Preferences..."), thumb=R('icon-prefs.png')))
    return dir

####################################################################################################   
def CreatePrefs():
  Prefs.Add(id=USE_HD_PREF_KEY, type='bool', default=True, label='Display in 720p')
  
  
#######################################################################
def ArchiveSearch(sender, query, page=1):
    url = ARCHIVE_SEARCH % (page, String.Quote(query), DATE_ORDER)
    dir = ProcessSearchResults(url)
    pageCount = int(JSON.ObjectFromURL(url)['pagecount'])
    if page < pageCount:
        dir.Append(Function(DirectoryItem(ArchiveSearch, title="More ...", thumb=R(ICON)), query=query, page=page+1))
    return dir
    
####################################################################################################   
def ArchiveBrowse(sender, page=1, order=DATE_ORDER):
    url = ARCHIVE_SEARCH %(page, "", order)
    dir = ProcessSearchResults(url)
    pageCount = int(JSON.ObjectFromURL(url)['pagecount'])
    if page < pageCount:
        dir.Append(Function(DirectoryItem(ArchiveBrowse, title="More ...", thumb=R(ICON)), page=page+1, order=order))
    return dir
    
#################################################################################################### 
def ProcessSearchResults(url):
    dir = MediaContainer(viewGroup='Details', mediaType='video')  
    for item in JSON.ObjectFromURL(url)['searchresult']:
        title = item['headline'].strip()
        summary = item['summary'].strip()
        subtitle = Datetime.ParseDate(item['publishdate']).strftime('%a %b %d, %Y')
        videoPageUrl = VIDEO_PAGE_URL % title.replace(' ','-')
        thumb = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@id="imageGallery"]/p/a')[0].get('href')
        dir.Append(Function(VideoItem(PlayVideo, title, subtitle=subtitle, summary=summary, thumb=thumb), videoPageUrl=videoPageUrl))
    return dir

####################################################################################################
def Feed(sender, urlFormat, variableResolution=True):
    dir = MediaContainer(viewGroup='Details', mediaType='video')  
    url = urlFormat
    if variableResolution:
        res = SD_RES
        if Prefs.Get(USE_HD_PREF_KEY):
            res = HD_RES
        url = urlFormat % res
    for item in XML.ElementFromURL(url, errors='ignore').xpath('//item', namespaces=NAMESPACES_A):
        title = item.xpath('title', namespaces=NAMESPACES_A)[0].text
        summary = item.xpath('itunes:summary', namespaces=NAMESPACES_A)[0].text
        pubDate = item.xpath('pubDate', namespaces=NAMESPACES_A)[0].text
        subtitle = Datetime.ParseDate(pubDate).strftime('%a %b %d, %Y')
        durationStr = item.xpath('itunes:duration', namespaces=NAMESPACES_A)[0].text
        duration = ConvertDuration(durationStr)
        content = item.xpath('feedburner:origEnclosureLink', namespaces=NAMESPACES_A)[0].text
        description = item.xpath('description', namespaces=NAMESPACES_A)[0].text
        start = description.find('img src=')
        stop = description.find('jpg', start)
        thumb = description[start+9 : stop+3]
        dir.Append(VideoItem(content, title, subtitle, summary, thumb=thumb, duration=duration))
    return dir

####################################################################################################
def LastestStories(sender):
    dir = MediaContainer(viewGroup='Details', mediaType='video') 
    for item in XML.ElementFromURL(LATEST_STORIES, errors='ignore').xpath('//item', namespaces=NAMESPACES_B):
        title = item.xpath('title', namespaces=NAMESPACES_B)[0].text
        summary = item.xpath('description', namespaces=NAMESPACES_B)[0].text
        stop = summary.find('<')
        if stop > -1:
            summary = summary[0:stop]
        videoPageUrl = item.xpath('feedburner:origLink', namespaces=NAMESPACES_B)[0].text
        thumb = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@id="imageGallery"]/p/a')[0].get('href')
        dir.Append(Function(VideoItem(PlayVideo, title, subtitle=None, summary=summary, thumb=thumb), videoPageUrl=videoPageUrl))
    return dir

####################################################################################################
def PlayVideo(sender, videoPageUrl):
    res = SD_RES
    if Prefs.Get(USE_HD_PREF_KEY):
        res = HD_RES
    xpath = '//a[@title="HD %s commentary"]' % res
    videoUrl =  XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath(xpath)[0].get('href')
    return Redirect(videoUrl)

####################################################################################################
def ConvertDuration(durationStr):
    tokens = durationStr.split(":")
    seconds = int(tokens[-1])
    minutes  = 0
    if len(tokens) > 1:
        minutes = int(tokens[-2])
    hours = 0
    if len(tokens) > 2:
        hours = int(tokens[-3])
    return 1000*(60*60*hours + 60*minutes + seconds)