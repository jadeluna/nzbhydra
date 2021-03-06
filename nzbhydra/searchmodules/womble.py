from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import str
from builtins import int
from future import standard_library
#standard_library.install_aliases()
from builtins import *
import logging
import re
import arrow
from furl import furl
import xml.etree.ElementTree as ET

from nzbhydra.categories import getUnknownCategory, getCategoryByName
from nzbhydra.exceptions import IndexerResultParsingException
from nzbhydra.nzb_search_result import NzbSearchResult

from nzbhydra.search_module import SearchModule, IndexerProcessingResult

logger = logging.getLogger('root')


class Womble(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, indexer):
        super(Womble, self).__init__(indexer)
        self.module = "Womble"
        
        self.settings.generate_queries = False
        self.needs_queries = False
        self.category_search = True
        self.supports_queries = False  # Only as support for general tv search

    def build_base_url(self):
        f = furl(self.host)
        f.path.add("rss")
        url = f.add(args={"fr": "false"})
        return url

    def get_search_urls(self, search_request):
        self.error("This indexer does not support queries")
        return []

    def get_showsearch_urls(self, search_request):
        urls = []
        if search_request.query or search_request.identifier_key or search_request.identifier_value or search_request.season or search_request.episode:
            self.error("This indexer does not support specific searches")
            return []
        if search_request.category is not None:
            if any(x in search_request.category.category.newznabCategories for x in [5030, 5000]):
                urls.append(self.build_base_url().add({"sec": "tv-dvd"}).tostr())
                urls.append(self.build_base_url().add({"sec": "tv-sd"}).tostr())
            if any(x in search_request.category.category.newznabCategories for x in [5040, 5000]):
                urls.append(self.build_base_url().add({"sec": "tv-x264"}).tostr())
                urls.append(self.build_base_url().add({"sec": "tv-hd"}).tostr())
        else:
            urls.append(self.build_base_url().tostr())
        return urls

    def get_moviesearch_urls(self, search_request):
        self.error("This indexer does not support movie search")
        return []

    def get_ebook_urls(self, search_request):
        self.error("This indexer does not support ebook search")
        return []

    def get_audiobook_urls(self, search_request):
        self.error("This indexer does not support audiobook search")
        return []

    def get_comic_urls(self, search_request):
        self.error("This indexer does not support comic search")
        return []

    def get_anime_urls(self, search_request):
        self.error("This indexer does not support anime search")
        return []
    
    def get_details_link(self, guid):
        self.info("This indexer does not provide details on releases")
        return None


    def process_query_result(self, xml, searchRequest, maxResults=None):
        entries = []
        countRejected = self.getRejectedCountDict()
        try:
            tree = ET.fromstring(xml)
        except Exception:
            self.exception("Error parsing XML: %s..." % xml[:500])
            logger.debug(xml)
            raise IndexerResultParsingException("Error parsing XML", self)
        for elem in tree.iter('item'):
            title = elem.find("title")
            url = elem.find("enclosure")
            pubdate = elem.find("pubDate")
            if title is None or url is None or pubdate is None:
                continue
            
            entry = self.create_nzb_search_result()
            entry.title = title.text
            entry.link = url.attrib["url"]
            entry.has_nfo = NzbSearchResult.HAS_NFO_NO
            
            p = re.compile("(.*)\(Size:(\d*)")
            m = p.search(elem.find("description").text)
            if m:
                entry.description = m.group(1)
                entry.size = int(m.group(2)) * 1024 * 1024 #megabyte to byte
            if elem.find("category").text.lower() == "tv-dvdrip" or elem.find("category").text.lower() == "tv-sd":
                entry.category = getCategoryByName("tvsd")
            elif elem.find("category").text.lower() == "tv-x264" or elem.find("category").text.lower == "tv-hd":
                entry.category = getCategoryByName("tvhd")
            else:
                entry.category = getUnknownCategory()
                
            
            entry.indexerguid = elem.find("guid").text[30:] #39a/The.Almighty.Johnsons.S03E06.720p.BluRay.x264-YELLOWBiRD.nzb is the GUID, only the 39a doesn't work
            
            pubdate = arrow.get(pubdate.text, 'M/D/YYYY h:mm:ss A')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.pubDate = pubdate.format("ddd, DD MMM YYYY HH:mm:ss Z")
            entry.age_days = (arrow.utcnow() - pubdate).days

            accepted, reason, ri = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                entries.append(entry)
            else:
                countRejected[ri] += 1
                self.debug("Rejected search result. Reason: %s" % reason)
        
        return IndexerProcessingResult(entries=entries, queries=[], total_known=True, has_more=False, total=len(entries), rejected=countRejected)
    
    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host)
        f.path.add("nzb")
        f.path.add(guid)
        return f.tostr()


def get_instance(indexer):
    return Womble(indexer)
