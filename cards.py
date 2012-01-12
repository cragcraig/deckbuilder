import BeautifulSoup
import re
import string
import textwrap
import unicodedata
import urllib2

def url(name):
    """Get the data url for a card."""
    url_prefix = 'http://ww2.wizards.com/gatherer/CardDetails.aspx?name='
    return url_prefix + name.replace(' ', '%20')

def _scrape(soup, title):
    """Scrape a BeautifulSoup for the value div of the div with id=title."""
    scrape = soup.find('div', id=title)
    if not scrape:
        return None
    value = scrape.find('div', attrs={'class': 'value'})
    return unicodedata.normalize('NFKD', value.text).encode('ascii', 'xmlcharrefreplace').replace('&#8212;', ' -- ')

def _scrape_replaceunicode(soup, title):
    """Scrape a BeautifulSoup for the value div of the div with id=title."""
    scrape = soup.find('div', id=title)
    if not scrape:
        return None
    value = scrape.find('div', attrs={'class': 'value'})
    return value.text.encode('ascii', 'replace')

def _scrape_raw(soup, title):
    """Scrape a BeautifulSoup for the value div of the div with id=title."""
    scrape = soup.find('div', id=title)
    if not scrape:
        return None
    value = scrape.find('div', attrs={'class': 'value'})
    return value

def _scrape_cost(soup, manaid):
    """Scrape mana cost as a list."""
    value = _scrape_raw(soup, manaid)
    if not value:
        return None
    imgs = value.findAll('img')
    l = [_alt_to_id(t['alt']) for t in imgs]
    return ''.join(l)

def _scrape_pt(soup, ptid):
    """Scrape power / toughness."""
    content = _scrape(soup, ptid)
    m = re.search('(.+)\s+.+\s+(.+)', content)
    return (m.group(1), m.group(2))

def _scrape_text(soup, title):
    """Scrape card text."""
    value = _scrape_raw(soup, title)
    if not value:
        return None
    boxes = value.findAll('div', attrs={'class': 'cardtextbox'})
    retl = [_replace_scrape_imgs(str(l)) for l in boxes]
    return string.join(retl, sep='\n')

def _scrape_cind(soup, title):
    """Scrape color indicator."""
    cind = _scrape(soup, title)
    if not cind:
        return None
    l = re.findall('\w+', cind)
    return ''.join(_conv_all_alt(l))

def _replace_scrape_imgs(s):
    """Replace imgs in a scrape string with the ascii representation."""
    tmp = re.sub('<.*?>', '', re.sub('<img.*?alt="(.*?)".*?>', '|\\1|', s))
    return ''.join(_conv_all_alt(string.split(tmp, '|')))

def _conv_all_alt(l):
    """Converts all alt types to symbols."""
    r = []
    for s in l:
        if s in _alt_to_sym:
            r.append(_alt_to_sym[s])
        else:
            r.append(s)
    return r

def _alt_to_id(mana):
    """Converts a mana type from alt name to symbol. Ignores ints."""
    if re.match('\d+$', mana):
        return str(int(mana))
    else:
        if mana not in _alt_to_sym:
            return '?'
        else:
            return _alt_to_sym[mana]

# Gatherer scrape alt tags.
_alt_to_sym = {'Green': '{G}', 'Red': '{R}', 'Black': '{B}', 'Blue': '{U}',
               'White': '{W}', 'Variable Colorless': '{X}', 'Tap': '{T}',
               'None': 'None', 'Phyrexian Green': '{GP}',
               'Phyrexian Red': '{RP}', 'Phyrexian Black': '{BP}',
               'Phyrexian Blue': '{UP}', 'Phyrexian White': '{WP}'}

# Gatherer scrape div ids.
scrapeid_cardstyles = ['', '_ctl05', '_ctl06']
scrapeid_name = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_nameRow'
scrapeid_mana = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_manaRow'
scrapeid_cind =\
    'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_colorIndicatorRow'
scrapeid_cmc = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_cmcRow'
scrapeid_type = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_typeRow'
scrapeid_text = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_textRow'
scrapeid_flvr =\
    'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_flavorRow'
scrapeid_pt = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent%s_ptRow'


class Card:
    """A MtG card."""
    def __init__(self, name):
        self.name = name
        self.cost = []
        self.convertedCost = None
        self.types = None
        self.text = None
        self.flavor = None
        self.power = None
        self.toughness = None
        self.colorIndicator = None
        self.cardback = None
        self.loaded = False

    def load(self, soup=None):
        """Attempts to scrape card data from gatherer.wizards.com.
        
        Reuses the given BeautifulSoup if not None. This is so double-sided
        cards do not need to request the gather page data twice.
        """
        self.loaded = False
        if not soup:
            response = urllib2.urlopen(url(self.name))
            html = response.read()
            soup = BeautifulSoup.BeautifulSoup(html)
        # Scrape data.
        style = self._checkCardstyle(soup)
        if style is None:
            return
        # Scrape card back, if needed.
        if style == scrapeid_cardstyles[1]:
            self.cardback = Card(_scrape(soup, scrapeid_name
                                               % scrapeid_cardstyles[2]))
            self.cardback.load(soup=soup)
            if not self.cardback.loaded:
                return
        # Scrape card data.
        name = _scrape(soup, scrapeid_name % style)
        self.name = name
        self.cost = _scrape_cost(soup, scrapeid_mana % style)
        self.convertedCost = _scrape(soup, scrapeid_cmc % style)
        types = _scrape_replaceunicode(soup, scrapeid_type % style).split('?')
        self.types = types[0].split()
        if (len(types) > 1):
            self.subtypes = types[1].split()
        else:
            self.subtypes = []
        self.text = _scrape_text(soup, scrapeid_text % style)
        self.flavor = _scrape(soup, scrapeid_flvr % style)
        self.colorIndicator = _scrape_cind(soup, scrapeid_cind % style)
        if self.isCreature():
            self.power, self.toughness = _scrape_pt(soup, scrapeid_pt % style)
        self.loaded = True

    def _checkCardstyle(self, soup):
        """Check the card style.

        Currently normal single sided cards and Innistrad double-faced cards
        are supported.
        """
        for s in scrapeid_cardstyles:
            name =_scrape(soup, scrapeid_name % s)
            if name and self.name and self.name.lower() == name.lower():
                return s
        return None

    def isCreature(self):
        """Return True if card is of type Creature."""
        return 'Creature' in self.types

    def hasType(self, t):
        """Return True if card has Type t as a major or subtype."""
        tc = t.capitalize()
        return tc in self.types or tc in self.subtypes

    def hasTypes(self, tlist):
        """Return True if card has all Types in t as a major or subtype."""
        return not any((not self.hasType(t) for t in tlist))

    def __str__(self):
        ret = str(self.name) + '\n' +\
              'cost: '.ljust(10) + str(self.cost) +\
              ' (' + str(self.convertedCost) + ')'
        if len(self.types):
            ret += '\n' + 'type:'.ljust(10)
        ret += ' '.join(self.types)
        if len(self.subtypes):
            ret += '\n' + 'subtype:'.ljust(10)
        ret += ' '.join(self.subtypes)
        if self.colorIndicator:
              ret += '\n' + 'color:'.ljust(10) + str(self.colorIndicator)
        if self.isCreature():
              ret += '\n' + 'P/T:'.ljust(10) + str(self.power) +\
                     ' / ' + str(self.toughness)
        if self.text:
            ret += '\n'
            for l in string.split(str(self.text), '\n'):
                ret += '\n' + textwrap.fill(l, 50)
        if self.flavor:
            ret += '\n'
            for l in string.split(str(self.flavor), '\n'):
                ret += '\n"' + textwrap.fill(l, 50) + '"'
        return ret

    def snippet(self):
        """Return a one line text snippet summarizing card."""
        return str(self.name).ljust(25) +\
               ('   ' + ' '.join(self.types)).ljust(25) +\
               str(self.cost if self.cost is not None else '').ljust(17) +\
               str(str(self.power) + ' / ' + str(self.toughness)\
                   if self.isCreature() else '').rjust(4)

    def color(self):
        """Get the card color."""
        if not self.cost and not self.colorIndicator:
            return None
        cost = self.cost if self.cost else self.colorIndicator
        s = re.findall('[RGBWU]', cost)
        if not s:
            return None
        return ''.join(sorted(list(set(s))))
