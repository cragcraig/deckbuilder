import math
import random
import re
import urllib2

from bs4 import BeautifulSoup

import cards


def filename(name):
    """Returns the filename associated with the deck name."""
    return name.replace(' ', '_').lower() + '.deck'

def choose(n, r):
    """N choose R."""
    return math.factorial(n) / (math.factorial(r) * math.factorial(n - r))


class Deck:
    """A deck of MtG cards.
    
    Includes a deck, sideboard, and card data.
    """
    def __init__(self, name):
        self.name = name
        self.cardData = CardData()
        self.deck = CardPile(self.cardData)
        self.sideboard = CardPile(self.cardData)

    def prob_draw(self, z, n, handsize):
        """Probability of drawing >= z of a specific card with n copies."""
        decksize = self.deck.size()
        # Sanity check.
        if z > min(n, handsize) or max(z, n, handsize) > decksize:
            return 0.
        # Compute prob.
        c = 0
        for i in xrange(z, min(n, handsize) + 1):
            c += choose(handsize, i) * choose(decksize - handsize, n - i)
        return float(c) / float(choose(decksize, n))

    def prob_notdraw(self, n, handsize):
        """Probability of not drawing any of a specific card with n copies."""
        decksize = self.deck.size()
        return float(choose(decksize - handsize, n)) / float(choose(decksize, n))

    def prob_countways(self, n, handsize):
        """Return number of ways to draw at least one of n cards in a hand."""
        decksize = self.deck.size()
        return choose(decksize, n) - choose(decksize - handsize, n)

    def _recurseprob(self, nlist, drawn, undrawn, handsize):
        decksize = self.deck.size()
        c = 0
        if nlist[0][0] > nlist[0][1]:
            return 0.
        for n in xrange(nlist[0][0], nlist[0][1] + 1):
            if n > handsize - drawn or\
               nlist[0][1] - n > decksize - handsize - undrawn:
                continue
            c += (choose(handsize - drawn, n) *
                  choose(decksize - handsize - undrawn, nlist[0][1] - n)) *\
                  (self._recurseprob(nlist[1:], drawn + n,
                                     undrawn + nlist[0][1] - n,
                                     handsize)
                   if len(nlist) > 1 else 1)
        return c

    def _totalways(self, nlist):
        decksize = self.deck.size()
        c = 1
        u = 0
        for n in nlist:
            c *= choose(decksize - u, n[1])
            u += n[1]
        return c

    def prob_anddraw(self, nlist, handsize):
        """Probability of drawing at least one of each specific card in list."""
        n = self._recurseprob(nlist, 0, 0, handsize)
        d = self._totalways(nlist)
        return float(n) / float(d)

    def refreshData(self):
        """Refresh all data from gatherer."""
        for k in self.cardData.data.iterkeys():
            c = cards.Card(k)
            c.load()
            if c.loaded:
                self.cardData.data[k] = c
            else:
                print('Unable to load data for ' + k + '.')


class CardPile:
    """A collection of cards by name."""
    def __init__(self, cardData=None):
        self.cards = dict()
        self.cardData = cardData if cardData else CardData()

    def list(self):
        """Return a list of the cards in the deck."""
        r = []
        for k,v in self.cards.iteritems():
            r.extend([k] * v)
        return r

    def size(self):
        """Get the deck size."""
        return sum(self.cards.values())

    def add(self, card, num=1):
        """Add a card by name."""
        card = card.lower()
        if num < 1:
            return
        if card in self.cards:
            self.cards[card] += num
            return True
        elif self.cardData.fetch(card):
            self.cards[card] = num
            return True
        return False

    def remove(self, card, num=1):
        """Remove a card by name."""
        if num < 1:
            return
        card = card.lower()
        if card not in self.cards:
            return
        self.cards[card] -= num
        if self.cards[card] <= 0:
            del self.cards[card]

    def clear(self, card):
        """Remove all copies of a card by name."""
        card = card.lower()
        if card in self.cards:
            del self.cards[card]

    def manaSorted(self):
        """Return a list of cards sorted by converted mana cost."""
        return sorted(self.cards.iterkeys(),
                      key=lambda c: self.cardData.data[c].convertedCost)

    def randCards(self, num):
        """Generate a random draw of num cards from the deck."""
        num = min(num, self.size())
        return random.sample(self.list(), num)

    def countConvertedManaFilter(self, cost):
        """Count the number of cards in the deck with the given mana cost."""
        return len(filter(lambda c: self.cardData.data[c].convertedCost ==\
                                    str(cost),
                   self.list()))

    def maxConvertedManaCost(self):
        """Get the highest converted mana cost in the deck."""
        return max(((int(self.cardData.data[c].convertedCost)
                     if self.cardData.data[c].convertedCost is not None else 0)
                     for c in self.cards))

    def countColorSymbol(self, colorSymbol):
        """Count the number of the specified color symbol in the deck."""
        if not re.match('^[RGBWU]$',colorSymbol): 
            return None
        n = 0
        for c in self.list():
            n += str(self.cardData.data[c].cost).count(colorSymbol)
        return n
        
    def countColor(self, color):
        """Count the number of cards of the specified color in the deck."""
        if not re.match('^[RGBWU]$',color): 
            return None
        return len(filter(lambda c: re.search(color, 
                            str(self.cardData.data[c].cost)), 
                   self.list()))

    def listType(self, type):
        """Count the number of cards of the specified type in the deck."""
        return filter(lambda c: re.search(type, 
                        ' '.join(self.cardData.data[c].types), 
                        re.IGNORECASE), 
               self.list())


class CardData:
    """Holds a dictionary of card data."""
    def __init__(self):
        self.data = dict()

    def fetch(self, card):
        """Fetch card data for a card by name."""
        card = card.lower()
        if card in self.data:
            return True
        data = cards.Card(card)
        data.load()
        if not data.loaded:
            return False
        self.data[card] = data
        return True

    def cardNames(self):
        """List of all card names, both lowercase and original versions."""
        l = [c.name for c in self.data.itervalues()]
        l.extend(self.data.keys())
        return list(set(l))


def scrapeDeckListing(id):
    """Scrapes a deck-listing from mtgdeckbuilder.net given its ID."""
    try:
        page = urllib2.urlopen(
            'http://www.mtgdeckbuilder.net/Decks/PrintableDeck/' + id)
        html = page.read()
    except urllib2.URLError:
        raise cards.ScrapeError('Unable to read deck data url.')
    soup = BeautifulSoup(html)
    err = soup.find('div', {'class':'innerContentFrame'})
    if err is not None:
        raise cards.ScrapeError(err.string.strip())
    dl = []
    dl.append(soup.span.strong.string)
    tr = soup.find_all('tr', style='line-height: 18px')[1]
    dl += [s.replace(u'\xa0', u'') 
               for s in tr.stripped_strings
               if not re.search('Creatures|Lands|Spells|Cards$', s)]
    return dl
