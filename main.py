from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
import traceback
import time
import re

log = CPLog(__name__)


class xbytes(TorrentProvider, MovieProvider):

    urls = {
        'test' : 'http://www.xbytes.li',
        'login' : 'http://www.xbytes.li/takelogin.php?username=%s&password=%s',
        'login_check': 'http://www.xbytes.li/browse.php',
        'search' : 'http://www.xbytes.li/browse.php?search=%s&cat=%d&incldead=0',
        'download' : 'http://www.xbytes.li/%s',
    }

    cat_ids = [
        ([9], ['720p', '1080p']),
        ([8], ['720p']),
        ([7], ['1080p']),
        ([4], ['dvdrip']),
        ([6], ['brrip']),
    ]

    http_time_between_calls = 1 #seconds
    cat_backup_id = None

    def _searchOnTitle(self, title, movie, quality, results):
		log.info('Searching xbytes for %s, %d' % (title,self.getCatId(quality)[0]))
		url = self.urls['search'] % (title.replace(':', ''), self.getCatId(quality)[0] )
		data = self.getHTMLData(url)
		
		log.debug('Received data from xbytes')
		if data:
			log.debug('Data is valid from xbytes')
			data=re.sub('<br />',' ',data)
			html = BeautifulSoup(data)
						
			try:
				result_table = html.find('tbody', attrs = {'id' : 'highlighted'})
			#	result_table = result_table[3]
				if not result_table:
					log.error('No table results from xbytes')
					return
					
				torrents = result_table.find_all('tr')
				
				for result in torrents:
					columnas = result.find_all('td')
			
					release_name = columnas[1].find('a').find('b').contents[0]
					url = columnas[2].find('a')
					link = url['href']
					id = link[link.index('id=')+3:link.index('&')]
					size = columnas[5].contents[0]
					num_seeders = columnas[6].find('a').find('font').contents[0]
					release_name=re.sub('/',')(',release_name)
					results.append({
						'id': id,
						'name': release_name,
						'url': self.urls['download'] % (link),
						'size': self.parseSize(size.replace(',','.')),
						'seeders': num_seeders,
						'leechers': '0',
					})

			except:
				log.error('Failed to parse xbytes: %s' % (traceback.format_exc()))
	
    def login(self):
		# Check if we are still logged in every hour
		now = time.time()
		if self.last_login_check and self.last_login_check < (now - 3600):
			try:
				output = self.urlopen(self.urls['login_check'])
				if self.loginCheckSuccess(output):
					self.last_login_check = now
					return True
			except: pass
			self.last_login_check = None
			
		if self.last_login_check:
			return True
			
		try:
			params = self.getLoginParams()
			login_url = self.urls['login'] % (params['username'],params['password']) 
			log.info('Failed to login %s', (login_url))
			output = self.urlopen(login_url)
			
			if self.loginSuccess(output):
				self.last_login_check = now
				return True
				
			error = 'unknown'
		except:
			error = traceback.format_exc()
			
		self.last_login_check = None
		log.error('Failed to login %s: %s', (self.getName(), error))
		return False	
		
    def getLoginParams(self):
        log.debug('Getting login params for xbytes')
        return {
            'username': self.conf('username'),
            'password': self.conf('password'),
        }

    def loginSuccess(self, output):
		log.info('Checking login success for xbytes: %s' % ('True' if ('Hola' in output.lower() or 'logout' in output.lower()) else 'False'))
		return 'Hola' in output.lower() or 'logout' in output.lower()

    loginCheckSuccess = loginSuccess