import cards

def filename(name):
    """Returns the filename associated with the deck name."""
    return name.replace(' ', '_').lower() + '.deck'


class Deck:
    """A deck of MtG cards."""
    def __init__(self, name):
        self.name = name
        self.cards = dict()
        self.cardData = dict()

    def list(self):
        """Return a list of the cards in the deck."""
        return [k for i in xrange(v) for k,v in self.cards.iteritems()]

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
        elif self.fetch(card):
            self.cards[card] = num

    def remove(self, card, num=1):
        """Remove a card by name."""
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

    def fetch(self, card):
        """Fetch card data for a card by name."""
        card = card.lower()
        if card in self.cardData:
            return True
        data = cards.Card(card)
        data.load()
        if not data.loaded:
            return False
        self.cardData[card] = data
        return True

    def manaSorted(self):
        """Return a list of cards sorted by converted mana cost."""
        return sorted(self.cards.iterkeys(),
                      key=lambda c: self.cardData[c].convertedCost)
