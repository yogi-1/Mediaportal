﻿#	-*-	coding:	utf-8	-*-

from Plugins.Extensions.mediaportal.resources.imports import *
from Plugins.Extensions.mediaportal.resources.decrypt import *
from Plugins.Extensions.mediaportal.resources.yt_url import *
import Queue
import threading
from Components.ScrollLabel import ScrollLabel

HSH_Version = "HörspielHouse.de v0.90"

HSH_siteEncoding = 'utf-8'

"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel	: Menu Up / Exit
	KeyOK		: Menu Down / Select
	
Doku Auswahl:
	Bouquet +/-			: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'		: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau			: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau			: Die Beschreibung Seitenweise scrollen
	Gelb				: Videopriorität 'L','M','H'

"""
def HSH_menuListentry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, 25, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0])
		] 
		
class show_HSH_Genre(Screen):

	def __init__(self, session):
		self.session = session
		
		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + "/skins"
		
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + "/original/defaultGenreScreen.xml"

		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
			
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up"	: self.keyUp,
			"down"	: self.keyDown,
			"left"	: self.keyLeft,
			"right"	: self.keyRight,
			"red"	: self.keyRed
		}, -1)

		self['title'] = Label(HSH_Version)
		self['ContentTitle'] = Label("Hörspiel Auswahl")
		self['name'] = Label("")
		self['F1'] = Label("")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")
		
		self.menuLevel = 0
		self.menuMaxLevel = 1
		self.menuIdx = [0,0,0]
		self.keyLocked = True
		self.genreSelected = False
		self.menuListe = []
		self.baseUrl = "http://www.xn--hrspielhouse-4ib.de"
		self.genreBase = "/category"
		self.genreName = ["","","",""]
		self.genreUrl = ["","","",""]
		self.genreTitle = ""
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', 23))
		self.chooseMenuList.l.setItemHeight(25)
		self['genreList'] = self.chooseMenuList
		
		self.genreMenu = [
			[
			("Abenteuer", "/abenteuer"),
			("Comedy", "/comedy"),
			("Drama", "/drama"),
			("Erotik", "/erotik"),
			("Fantasy", "/fantasy"),
			("Horror", "/horror"),
			("Kinder", "/kinder"),
			("Krimi", "/krimi"),
			("Philosophie", "/philosophie"),
			("Roman", "/roman"),
			("SciFi", "/scifi"),
			("Special", "/special"),
			("Thriller", "/thriller")
			],
			[None,None,None,None,None,None,None,None,None,None,None,
			[
			("A-Team", "/special/a-team"),
			("Dexter", "/special/dexter"),
			("Die Chroniken von Narnia", "/special/die-chroniken-von-nania"),
			("Die Dr3i", "/special/die-dr3i"),
			("Die Drei ???", "/special/die-drei"),
			("Die Funk-Füchse", "/special/die-funk-fuechse"),
			("Die PSI Akten", "/special/die-psi-akten"),
			("Geisterjäger - John Sinclair", "/special/geisterjaeger-john-sinclair"),
			("How i met your mother", "/special/how-i-met-your-mother"),
			("James Bond", "/special/james-bond"),
			("Jan Tenner", "/special/jan-tenner"),
			("Masters of the Universe", "/special/master-of-the-universe"),
			("Perry Rhodan", "/special/perry-rhodan"),
			("Sherlock Holmes", "/special/sherlock-holmes"),
			("Tatort", "/special/tatort"),
			("Teen Agents", "/special/teen-agents"),
			("WDR Krimi", "/special/wdr-krimi")
			],
			None
			],
			[
			None
			]
			]
			
		self.onLayoutFinish.append(self.loadMenu)
		
	def setGenreStrTitle(self):
		genreName = self['genreList'].getCurrent()[0][0]
		genreLink = self['genreList'].getCurrent()[0][1]
		if self.menuLevel in range(self.menuMaxLevel+1):
			if self.menuLevel == 0:
				self.genreName[self.menuLevel] = genreName
			else:
				self.genreName[self.menuLevel] = ':'+genreName
				
			self.genreUrl[self.menuLevel] = genreLink
		self.genreTitle = "%s%s%s" % (self.genreName[0],self.genreName[1],self.genreName[2])
		self['name'].setText("Auswahl: "+self.genreTitle)

	def loadMenu(self):
		print "HörspielHouse.de:"
		self.setMenu(0, True)
		self.keyLocked = False

	def keyRed(self):
		pass

	def keyUp(self):
		self['genreList'].up()
		self.menuIdx[self.menuLevel] = self['genreList'].getSelectedIndex()
		self.setGenreStrTitle()
		
	def keyDown(self):
		self['genreList'].down()
		self.menuIdx[self.menuLevel] = self['genreList'].getSelectedIndex()
		self.setGenreStrTitle()
		
	def keyRight(self):
		self['genreList'].pageDown()
		self.menuIdx[self.menuLevel] = self['genreList'].getSelectedIndex()
		self.setGenreStrTitle()
		
	def keyLeft(self):
		self['genreList'].pageUp()
		self.menuIdx[self.menuLevel] = self['genreList'].getSelectedIndex()
		self.setGenreStrTitle()
		
	def keyMenuUp(self):
		print "keyMenuUp:"
		if self.keyLocked:
			return
		self.menuIdx[self.menuLevel] = self['genreList'].getSelectedIndex()
		self.setMenu(-1)

	def keyOK(self):
		print "keyOK:"
		if self.keyLocked:
			return
			
		self.menuIdx[self.menuLevel] = self['genreList'].getSelectedIndex()
		self.setMenu(1)
		
		if self.genreSelected:
			print "Genre selected"
			genreurl = self.baseUrl+self.genreBase+self.genreUrl[0]+self.genreUrl[1]
			print genreurl
			self.session.open(HSH_FilmListeScreen, genreurl, self.genreTitle)

	def setMenu(self, levelIncr, menuInit=False):
		print "setMenu: ",levelIncr
		self.genreSelected = False
		if (self.menuLevel+levelIncr) in range(self.menuMaxLevel+1):
			if levelIncr < 0:
				self.genreName[self.menuLevel] = ""
			
			self.menuLevel += levelIncr
			
			if levelIncr > 0 or menuInit:
				self.menuIdx[self.menuLevel] = 0
			
			if self.menuLevel == 0:
				print "level-0"
				if self.genreMenu[0] != None:
					self.menuListe = []
					for (Name,Url) in self.genreMenu[0]:
						self.menuListe.append((Name,Url))
					self.chooseMenuList.setList(map(HSH_menuListentry, self.menuListe))
					self['genreList'].moveToIndex(self.menuIdx[0])
				else:
					self.genreName[self.menuLevel] = ""
					self.genreUrl[self.menuLevel] = ""
					print "No menu entrys!"
			elif self.menuLevel == 1:
				print "level-1"
				if self.genreMenu[1][self.menuIdx[0]] != None:
					self.menuListe = []
					for (Name,Url) in self.genreMenu[1][self.menuIdx[0]]:
						self.menuListe.append((Name,Url))
					self.chooseMenuList.setList(map(HSH_menuListentry, self.menuListe))
					self['genreList'].moveToIndex(self.menuIdx[1])
				else:
					self.genreName[self.menuLevel] = ""
					self.genreUrl[self.menuLevel] = ""
					self.menuLevel -= levelIncr
					self.genreSelected = True
					print "No menu entrys!"
			elif self.menuLevel == 2:
				print "level-2"
				if self.genreMenu[2][self.menuIdx[0]][self.menuIdx[1]] != None:
					self.menuListe = []
					for (Name,Url) in self.genreMenu[2][self.menuIdx[0]][self.menuIdx[1]]:
						self.menuListe.append((Name,Url))
					self.chooseMenuList.setList(map(HSH_menuListentry, self.menuListe))
					self['genreList'].moveToIndex(self.menuIdx[2])
				else:
					self.genreName[self.menuLevel] = ""
					self.genreUrl[self.menuLevel] = ""
					self.menuLevel -= levelIncr
					self.genreSelected = True
					print "No menu entrys!"
		else:
			print "Entry selected"
			self.genreSelected = True
				
		print "menuLevel: ",self.menuLevel
		print "mainIdx: ",self.menuIdx[0]
		print "subIdx_1: ",self.menuIdx[1]
		print "subIdx_2: ",self.menuIdx[2]
		print "genreSelected: ",self.genreSelected
		print "menuListe: ",self.menuListe
		print "genreUrl: ",self.genreUrl
		
		self.setGenreStrTitle()		
		
	def keyCancel(self):
		if self.menuLevel == 0:
			self.close()
		else:
			self.keyMenuUp()
	

def HSH_FilmListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
		] 
class HSH_FilmListeScreen(Screen):
	
	def __init__(self, session, genreLink, genreName):
		self.session = session
		self.genreLink = genreLink
		self.genreName = genreName
		
		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + "/skins"
		
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + "/original/dokuListScreen.xml"

		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
			
		Screen.__init__(self, session)
		
		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions","DirectionActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"red" :  self.keyTxtPageUp,
			"blue" :  self.keyTxtPageDown
		}, -1)

		self.sortOrder = 0
		self.baseUrl = "http://www.allmusichouse.de"
		self.genreTitle = "Hörspiele in Auswahl "
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(HSH_Version)
		self['ContentTitle'] = Label("")
		self['name'] = Label("")
		self['handlung'] = ScrollLabel("")
		self['page'] = Label("")
		self['F1'] = Label("Text-")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("Text+")
		self['VideoPrio'] = Label("")
		self['vPrio'] = Label("")
		self['Page'] = Label("Page")
		self['coverArt'] = Pixmap()
		
		self.timerStart = False
		self.seekTimerRun = False
		self.filmQ = Queue.Queue(0)
		self.eventL = threading.Event()
		self.keyLocked = True
		self.musicListe = []
		self.keckse = {}
		self.page = 0
		self.pages = 0;
		self.genreSpecials = re.match('.*?\*Special',self.genreName)

		self.setGenreStrTitle()
		
		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('mediaportal', 23))
		self.chooseMenuList.l.setItemHeight(25)
		self['liste'] = self.chooseMenuList
		
		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		#print genreName
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		print "loadPage:"
		#if not self.genreSpecials:
		url = "%s/page/%d/" % (self.genreLink, self.page)
		#else:
		#	url = "%s/page/%d/" % (self.genreLink, self.page)
			
		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))
			
		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()
		print "eventL ",self.eventL.is_set()
		
	def loadPageQueued(self):
		print "loadPageQueued:"
		self['name'].setText('Bitte warten...')
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		#self.eventL.clear()
		print url
		getPage(url, cookies=self.keckse, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)
		
	def dataError(self, error):
		self.eventL.clear()
		print "dataError:"
		print error
		self.musicListe.append(("No audio drama found !","","",""))
		self.chooseMenuList.setList(map(HSH_FilmListEntry, self.musicListe))
		
	def loadPageData(self, data):
		print "loadPageData:"
		
		if self.genreSpecials:
			print "Specials suche..."
			m=re.search('<div id="content">(.*?)<!-- #content -->',data,re.S)
		else:
			print "Normal search.."
			m=re.search('<div id="content">(.*?)<!-- #content -->',data,re.S)
			
		if m:
			music = re.findall('<h2 class="title"><a href="(.*?)".*?rel="bookmark">(.*?)</a>.*?class="entry clearfix">'\
								'.*?<p>(.*?)</p>', m.group(1), re.S)
		else:
			music = None
		
		if music:
			print "Music found !"
			if not self.pages:
				m = re.findall('class=\'pages\'>Seite.*?von (.*?)</', data)
				if m:
					self.pages = int(m[0])
				else:
					self.pages = 1
				self.page = 1
				print "Page: %d / %d" % (self.page,self.pages)
				self['page'].setText("%d / %d" % (self.page,self.pages))
			
			self.musicListe = []
			for	(url,name,desc) in music:
				#print	"Url: ", url, "Name: ", name
				self.musicListe.append((decodeHtml(name), url, desc.lstrip().rstrip()))
			self.chooseMenuList.setList(map(HSH_FilmListEntry, self.musicListe))
			
		else:
			print "No audio drama found !"
			self.musicListe.append(("No audio drama found !","",""))
			self.chooseMenuList.setList(map(HSH_FilmListEntry, self.musicListe))
		self.loadPic()

	def loadPic(self):
		print "loadPic:"
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		desc = self['liste'].getCurrent()[0][2]
		#print "streamName: ",streamName
		#print "streamUrl: ",streamUrl
		self.getHandlung(desc)
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
		self.keyLocked	= False
		
	def getHandlung(self, desc):
		print "getHandlung:"
		if desc == None:
			print "No Infos found !"
			self['handlung'].setText("Keine weiteren Info's gefunden.")
			return
		self.setHandlung(desc)
		
	def setHandlung(self, data):
		print "setHandlung:"
		self['handlung'].setText(decodeHtml(data))
		
	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return

		streamLink = self['liste'].getCurrent()[0][1]
		streamName = self['liste'].getCurrent()[0][0]
		print "Open HSH_Streams:"
		print "Name: ",streamName
		print "Link: ",streamLink
		self.session.open(HSH_Streams, streamLink, streamName)
	
	def keyUp(self):
		if self.keyLocked:
			return
		self['liste'].up()
		
	def keyDown(self):
		if self.keyLocked:
			return
		self['liste'].down()
		
	def keyUpRepeated(self):
		#print "keyUpRepeated"
		if self.keyLocked:
			return
		self['liste'].up()
		
	def keyDownRepeated(self):
		#print "keyDownRepeated"
		if self.keyLocked:
			return
		self['liste'].down()
		
	def key_repeatedUp(self):
		#print "key_repeatedUp"
		if self.keyLocked:
			return
		self.loadPic()
		
	def keyLeft(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()
		
	def keyRight(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()
			
	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()
		
	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()
			
	def keyPageDown(self):
		#print "keyPageDown()"
		if self.seekTimerRun:
			self.seekTimerRun = False
		self.keyPageDownFast(1)
			
	def keyPageUp(self):
		#print "keyPageUp()"
		if self.seekTimerRun:
			self.seekTimerRun = False
		self.keyPageUpFast(1)
			
	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		#print "keyPageUpFast: ",step
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page += self.pages - self.page
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()
		
	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		print "keyPageDownFast: ",step
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page -=  -1 + self.page
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		#print "keyPageDownFast(2)"
		self.keyPageDownFast(2)
		
	def key_4(self):
		#print "keyPageDownFast(5)"
		self.keyPageDownFast(5)
		
	def key_7(self):
		#print "keyPageDownFast(10)"
		self.keyPageDownFast(10)
		
	def key_3(self):
		#print "keyPageUpFast(2)"
		self.keyPageUpFast(2)
		
	def key_6(self):
		#print "keyPageUpFast(5)"
		self.keyPageUpFast(5)
		
	def key_9(self):
		#print "keyPageUpFast(10)"
		self.keyPageUpFast(10)

	def keyTxtPageUp(self):
		self['handlung'].pageUp()
			
	def keyTxtPageDown(self):
		self['handlung'].pageDown()
			
	def keyCancel(self):
		self.close()

def HSH_StreamListEntry(entry):
	return [entry,
		(eListboxPythonMultiContent.TYPE_TEXT, 20, 0, 860, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
		] 
class HSH_Streams(Screen, ConfigListScreen):
	
	def __init__(self, session, dokuUrl, dokuName):
		self.session = session
		self.dokuUrl = dokuUrl
		self.dokuName = dokuName
		
		self.plugin_path = mp_globals.pluginPath
		self.skin_path =  mp_globals.pluginPath + "/skins"
		
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + "/original/dokuListScreen.xml"

		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
			
		Screen.__init__(self, session)

		self["actions"]  = ActionMap(["OkCancelActions", "ShortcutActions", "EPGSelectActions", "WizardActions", "ColorActions", "NumberActions", "MenuActions", "MoviePlayerActions", "InfobarSeekActions"], {
			"ok"    	: self.keyOK,
			"cancel"	: self.keyCancel,
			"up" 		: self.keyUp,
			"down" 		: self.keyDown,
			"right" 	: self.keyRight,
			"left" 		: self.keyLeft,
			"red" 		: self.keyTxtPageUp,
			"blue" 		: self.keyTxtPageDown,
			"yellow"	: self.keyYellow
		}, -1)
		
		self['title'] = Label(HSH_Version)
		self['ContentTitle'] = Label("Streams für "+dokuName)
		self['handlung'] = ScrollLabel("")
		self['name'] = Label(dokuName)
		self['vPrio'] = Label("")
		self['F1'] = Label("Text-")
		self['F2'] = Label("")
		self['F3'] = Label("VidPrio")
		self['F4'] = Label("Text+")
		self['Page'] = Label("")
		self['page'] = Label("")
		self['coverArt'] = Pixmap()
		self['VideoPrio'] = Label("VideoPrio")
		
		self.videoPrio = int(config.mediaportal.youtubeprio.value)-1
		self.videoPrioS = ['L','M','H']
		self.setVideoPrio()
		self.streamListe = []
		self.desc = ""
		self.streamMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.streamMenuList.l.setFont(0, gFont('mediaportal', 24))
		self.streamMenuList.l.setItemHeight(25)
		self['liste'] = self.streamMenuList
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)
		
	def loadPage(self):
		print "loadPage:"
		streamUrl = self.dokuUrl
		getPage(streamUrl, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)
		
	def parseData(self, data):
		print "parseData:"
		m = re.search('<!-- aeBeginAds -->(.*?)<!-- aeEndAds -->', data, re.S)
		movie = None
		if m:
			mdesc = re.search('<p>(.*?)</p>', m.group(1), re.S)
			movie = re.findall('<object.*?"movie" value=".*?/v/(.*?)\?vers', m.group(1))
			
		self.streamListe = []
		if movie:
			print "Streams found"
			if mdesc:
				print "Descr. found"
				self.desc = mdesc.group(1).replace('<br />','')
			else:
				self.desc = ""
			
			i = 1
			j = len(movie)
			for vid in movie:
				self.streamListe.append(("Teil %d / %d" % (i,j),vid))
				i += 1
		else:
			print "No audio streams found !"
			self.streamListe.append(("No audio streams found !",""))
		self.streamMenuList.setList(map(HSH_StreamListEntry, self.streamListe))
		self.loadPic()

	def youtubeErr(self, error):
		self.keyLocked = True
		print "youtubeErr: "
		self.streamListe = []
		self.streamListe.append(("Das Video kann leider nicht abgespielt werden !","",""))
		self.streamMenuList.setList(map(HSH_StreamListEntry, self.streamListe))
		self['handlung'].setText(str(error))
		
	def getHandlung(self, desc):
		print "getHandlung:"
		if desc == None:
			print "No Infos found !"
			self['handlung'].setText("Keine weiteren Info's vorhanden")
		else:
			self.setHandlung(desc)
		
	def setHandlung(self, data):
		#print "setHandlung:"
		self['handlung'].setText(decodeHtml(data))
		
	def loadPic(self):
		print "loadPic:"
		self['name'].setText(self.dokuName)
		print "streamName: ",self.dokuName
		self.getHandlung(self.desc)
		self.keyLocked = False
		
	def dataError(self, error):
		print "dataError:"
		print error
		self.streamListe.append(("Read error !",""))			
		self.streamMenuList.setList(map(HSH_StreamListEntry, self.streamListe))
			
	def setVideoPrio(self):
		if self.videoPrio+1 > 2:
			self.videoPrio = 0
		else:
			self.videoPrio += 1
		self['vPrio'].setText(self.videoPrioS[self.videoPrio])

	def keyOK(self):
		print "keyOK:"
		if self.keyLocked:
			return
		dhTitle = self.dokuName + ' - ' + self['liste'].getCurrent()[0][0]
		dhVideoId = self['liste'].getCurrent()[0][1]
		print "Title: ",dhTitle
		#print "VideoId: ",dhVideoId
		y = youtubeUrl(self.session)
		y.addErrback(self.youtubeErr)
		dhLink = y.getVideoUrl(dhVideoId, self.videoPrio)
		if dhLink:
			print dhLink
			sref = eServiceReference(0x1001, 0, dhLink)
			sref.setName(dhTitle)
			self.session.open(MoviePlayer, sref)
			
	def keyYellow(self):
		self.setVideoPrio()
		
	def keyUp(self):
		if self.keyLocked:
			return
		self['liste'].up()
		self.loadPic()
		
	def keyDown(self):
		if self.keyLocked:
			return
		self['liste'].down()
		self.loadPic()
		
	def keyLeft(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()
		self.loadPic()
		
	def keyRight(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()
		self.loadPic()
	
	def keyTxtPageUp(self):
		self['handlung'].pageUp()
			
	def keyTxtPageDown(self):
		self['handlung'].pageDown()
			
	def keyCancel(self):
		self.close()
		