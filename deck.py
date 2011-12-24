def filename(name):
    """Returns the filename associated with the deck name."""
    return name.replace(' ', '_').lower() + '.deck'


class Deck:
    """A deck of MtG cards."""
    def __init__(self, name):
        self.name = name
        self.cards = dict()

    def list(self):
        """Return a list of the cards in the deck."""
        return [k for i in xrange(v) for k,v in self.cards.iteritems()]

    def size(self):
        """Get the deck size."""
        return sum(self.cards.values())

    def add(self, card, num=1):
        """Add a card by name."""
        if card in self.cards:
            self.cards[card] += num
        else:
            self.cards[card] = num

    def remove(self, card, num=1):
        """Remove a card by name."""
        if card not in self.cards:
            return
        self.cards[card] -= num
        if self.cards[card] <= 0:
            del self.cards[card]

    def clear(self, card):
        """Remove all copies of a card by name."""
        if card in self.cards:
            del self.cards[card]
