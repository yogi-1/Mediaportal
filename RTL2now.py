from imports import *
from Components.config import config
from PlayRtmpMovie import PlayRtmpMovie

def rtl2AuswahlListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 900, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
		]

def rtl2SerieListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 900, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
		]

class RTL2nowGenreScreen(Screen):
	
	def __init__(self, session):
		self.session = session
		path = "/usr/lib/enigma2/python/Plugins/Extensions/mediaportal/skins/%s/RTLnowGenreScreen.xml" % config.mediaportal.skin.value
		if not fileExists(path):
			path = "/usr/lib/enigma2/python/Plugins/Extensions/mediaportal/skins/original/RTLnowGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
			
		Screen.__init__(self, session)
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)
		
		self['title'] = Label("RTL2NOW.de")
		self['name'] = Label("Genre Auswahl")
		self['handlung'] = Label("")
		self['Pic'] = Pixmap()

		self.genreliste = []
		self.keyLocked = True
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', 23))
		self.chooseMenuList.l.setItemHeight(25)
		self['List'] = self.chooseMenuList
		
		self.onLayoutFinish.append(self.loadPage)
		
	def loadPage(self):
		self.keyLocked = True
		url = "http://rtl2now.rtl2.de"
		getPage(url, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)
		
	def loadPageData(self, data):
		rtl2FreeVideos = re.findall('<div class="seriennavi_free" style=""><a href="(.*?)".*?>FREE.*?</div>.*?<div style="" class="seriennavi_link">.*?">(.*?)</a>.*?</div>', data, re.S)
		if rtl2FreeVideos:
			self.genreliste = []
			for url, title in rtl2FreeVideos:
				url = "http://rtl2now.rtl2.de" + url
				self.genreliste.append((title, url))
			self.chooseMenuList.setList(map(rtl2AuswahlListEntry, self.genreliste))
			self.keyLocked = False
		
	def dataError(self, error):
		print error
		
	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreLink = self['List'].getCurrent()[0][1]
		self.session.open(RTL2nowFilmeListeScreen, streamGenreLink)
		
	def keyLeft(self):
		if self.keyLocked:
			return
		self['List'].pageUp()
		
	def keyRight(self):
		if self.keyLocked:
			return
		self['List'].pageDown()
		
	def keyUp(self):
		if self.keyLocked:
			return
		self['List'].up()

	def keyDown(self):
		if self.keyLocked:
			return
		self['List'].down()

	def keyCancel(self):
		self.close()

class RTL2nowFilmeListeScreen(Screen):
	
	def __init__(self, session, streamGenreLink):
		self.session = session
		self.streamGenreLink = streamGenreLink
		path = "/usr/lib/enigma2/python/Plugins/Extensions/mediaportal/skins/%s/RTLnowFilmeScreen.xml" % config.mediaportal.skin.value
		if not fileExists(path):
			path = "/usr/lib/enigma2/python/Plugins/Extensions/mediaportal/skins/original/RTLnowFilmeScreen.xml"
		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
			
		Screen.__init__(self, session)
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("RTL2NOW.de")
		self['name'] = Label("Film Auswahl")

		self.keyLocked = True
		self.filmliste = []
		self.keckse = {}
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', 23))
		self.chooseMenuList.l.setItemHeight(25)
		self['List'] = self.chooseMenuList

		self.onLayoutFinish.append(self.loadPage)
		
	def loadPage(self):
		print self.streamGenreLink
		getPage(self.streamGenreLink, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)
		
	def dataError(self, error):
		print error
		
	def loadPageData(self, data):
		free = re.findall('teaser_content_row.*?FREE(.*?)pagesel', data, re.S)
		if free:
			folgen = re.findall('id="title_basic_.*?[0-9]"><a\shref="(.*?)"\stitle="(.*?)">.*?kostenlos</a>', free[0])
			if folgen:
				self.filmliste = []
				for (url,title) in folgen:
					print title
					url = "http://rtl2now.rtl2.de" + url.replace('amp;','')
					self.filmliste.append((decodeHtml(title), url))
				self.chooseMenuList.setList(map(rtl2SerieListEntry, self.filmliste))
				self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		self.streamName = self['List'].getCurrent()[0][0]
		self.pageurl = self['List'].getCurrent()[0][1]
		print self.pageurl
		getPage(self.pageurl, agent=std_headers, cookies=self.keckse, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.get_xml).addErrback(self.dataError)

	def get_xml(self, data):
		print "xml data"
		self.stream = re.findall("'playerdata': '(.*?)'", data, re.S)
		if self.stream:
			print self.stream[0].replace('amp;',''), self.keckse
			getPage(self.stream[0].replace('amp;',''), agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.get_stream).addErrback(self.dataError)
		else:
			print "nix"
			
	def get_stream(self, data):
		print "stream data"
		rtmpe_data = re.findall('<filename.*?><!\[CDATA\[(rtmpe://.*?rtl2now/)(.*?)\]\]></filename>', data, re.S|re.I)
		if rtmpe_data:
			print rtmpe_data, self.pageurl
			(host, playpath) = rtmpe_data[0]
			print host, playpath
			if config.mediaportal.useRtmpDump.value:
				final = "%s' --swfVfy=1 --playpath=mp4:%s --app=rtl2now/_definst_ --pageUrl=http://rtl2now.rtl2.de/ --tcUrl=rtmpe://fms-fra30.rtl.de/rtl2now/ --swfUrl=http://rtl2now.rtl2.de/includes/vodplayer.swf'" % (host, playpath)
				print final
				movieinfo = [final,self.streamName+'.f4v']
				self.session.open(PlayRtmpMovie, movieinfo, self.streamName)
			else:
				final = "%s swfUrl=http://rtl2now.rtl2.de/includes/vodplayer.swf pageurl=%s playpath=mp4:%s swfVfy=1" % (host, self.pageurl, playpath)
				print final
				sref = eServiceReference(0x1001, 0, final)
				sref.setName(self.streamName)
				self.session.open(MoviePlayer, sref)
	
	def keyTMDbInfo(self):
		if TMDbPresent:
			title = self['List'].getCurrent()[0][0]
			self.session.open(TMDbMain, title)
			
	def keyCancel(self):
		self.close()