#!/usr/bin/python
from __future__ import print_function, with_statement

import re
import string
import sys
import cPickle as pickle
import webbrowser
import os

import cards
import deck

# Custom exceptions
class ImproperArgError(Exception):
    pass

class UsageError(Exception):
    pass

class MissingDeckError(Exception):
    pass

# Main routine
def main():
    """Prompt and execute commands."""
    boldprint('\n*** Magic: The Gathering Deck Builder ***')
    if 'readline' not in sys.modules:
        print('\n> The readline module is not avaliable.\n'
              '> Line editing and tab completion is disabled.')
    cont = True
    cmd = ''
    prev = ''
    while cont:
        cmd = prompt_cmd()
        if cmd == '':
            cmd = prev
        cont = exec_cmd(cmd)
        prev = cmd

# Command interpreter.
def exec_cmd(cmdstr):
    """Interpret a command."""
    m = re.match('(\w+)\s*(.*)$', cmdstr)
    if not m:
        print('Bad command.')
    else:
        cmd = m.group(1)
        arg = m.group(2)
        if not cmd:
            print('Type a command. Try \'help\'.')
        elif cmd in cmd_dict:
            try:
                cmd_dict[cmd](arg)
            except ImproperArgError as e:
                print(str(e))
            except UsageError as e:
                print('usage: ' + cmd + ' ' + str(e))
            except MissingDeckError:
                print('No active deck.')
            if 'readline' in sys.modules:
                readline.add_history(cmdstr)
        else:
            print('%s is not a command. Try \'help\'.' % str(cmd))
    return True

def get_prompt():
    s = ''
    if active_deck:
        s = '[' + active_deck.name + ']'
    return s + '# '

def prompt_cmd():
    """Print command prompt for the current state."""
    try:
        return raw_input(get_prompt()).strip()
    except EOFError:
        cmd_exit('')
    except KeyboardInterrupt:
        cmd_exit('')
    return ''

def parse_numarg(arg):
    """Parse an argument of the form <NUM> <ARG>. Returns (num, arg)."""
    if not arg:
        return (None, None)
    m = re.match('(\d*)\s*(.*)$', arg)
    if m and m.group(1) and m.group(1) > 0:
        return (m.group(2), int(m.group(1)))
    raise ImproperArgError('Argument should be of the form <NUM> <ARG>.')

def print_deckcardline(count, card, reqType=None):
    """Print a snippet line for a card in the active deck.
    
    If reqType is not none, skips printing the line if card does not have the
    specified Type.
    """
    if reqType and not card.hasTypes(reqType.split()):
        return False
    print(str(count).rjust(3), end=' '*3)
    mprint(card.color(),
           card.snippet())
    return True

def assert_activedeck():
    """Raise a MissingDeckError if there is not an active deck."""
    if not active_deck:
        raise MissingDeckError

_ansicode = {
    'black': '\x1b[30m',
    'red': '\x1b[31m',
    'green': '\x1b[32m',
    'yellow': '\x1b[33m',
    'blue': '\x1b[34m',
    'purple': '\x1b[35m',
    'cyan': '\x1b[36m',
    'white': '\x1b[37m',
    'default': '\x1b[39m',
    'reset': '\x1b[0m',
    'bold': '\x1b[1m',
    'italics': '\x1b[3m',
    'underline': '\x1b[4m'}

_cardcolors = {
    'B': 'black',
    'R': 'red',
    'G': 'green',
    'W': 'white',
    'U': 'blue'}

def cprint(color, s, bold=True):
    """Print a string in color."""
    if global_coloron:
        assert color in _ansicode
        print((_ansicode['bold'] if bold else '') +
              _ansicode[color] + s + _ansicode['reset'])
    else:
        print(s)

def mprint(cardcolor, s, bold=True):
    """Print a string in the specified Magic card color."""
    if cardcolor and cardcolor in _cardcolors:
        cprint(_cardcolors[cardcolor], s, bold=bold)
    elif cardcolor and len(cardcolor) > 1:
        cprint('yellow', s, bold=bold)
    else:
        print(s)

def boldprint(s):
    """Print a string in bold."""
    print(boldstring(s))

def boldstring(s):
    """Return a string formatted with bold ansi codes."""
    if global_coloron:
        return _ansicode['bold'] + s + _ansicode['reset']
    else:
        return s

# Executeable commands.
def cmd_exit(arg):
    """Exit the program."""
    sys.exit(0)

def cmd_help(arg):
    """Print help text."""
    cprint('bold', '\nAvaliable commands:')
    w = max((len(h) for h in cmd_dict.iterkeys())) + 1
    for cmd in sorted(cmd_dict.keys()):
        print(boldstring(cmd.ljust(w)) + " - " + cmd_dict[cmd].__doc__)

def cmd_deck(arg):
    """Set the active deck."""
    global active_deck
    if not arg:
        raise UsageError('<NAME>')
    try:
        with open(deck.filename(arg), "rb") as f:
            active_deck = pickle.load(f)
            print('Loaded deck \'' + active_deck.name + '\'.')
    except IOError:
        active_deck = deck.Deck(arg)
        print('Created new deck \'' + active_deck.name + '\'.')

def cmd_decklist(arg):
    """List the decks in the current directory."""
    print('-' * 20)
    for fn in os.listdir('.'):
        if fn.endswith('.deck'):
            print(pickle.load(open(fn, "rb")).name)
    print('')

def cmd_save(arg):
    """Save the active deck."""
    assert_activedeck()
    with open(deck.filename(active_deck.name), "wb") as f:
        pickle.dump(active_deck, f)
    print('Saved deck \'' + active_deck.name + '\'.')
    print('To load use command \'deck ' + active_deck.name +'\'.')

def cmd_deckname(arg):
    """Change the name of the active deck."""
    if not arg or len(arg) == 0:
        raise UsageError('<NAME>')
    assert_activedeck()
    active_deck.name = arg
    print('Renamed active deck \'' + active_deck.name + '\'.')

def cmd_side(arg):
    """Move a card from the active deck to its sideboard."""
    if not arg:
        raise UsageError('<CARD>')
    assert_activedeck()
    card = arg.lower()
    if card not in active_deck.deck.cards:
        raise ImproperArgError('Card is not in active deck.')
    num = active_deck.deck.cards[card]
    active_deck.deck.remove(card, num)
    active_deck.sideboard.add(card, num)
    cmd_listall('')

def cmd_add(arg):
    """Add a card to the active deck."""
    card, num = parse_numarg(arg)
    if not card or not num:
        raise UsageError('<NUM> <CARD>')
    assert_activedeck()
    if active_deck.deck.add(card, num):
        cmd_listall('')
    else:
        print('Unable to find card data.')

def cmd_addside(arg):
    """Add a card to the active deck's sideboard."""
    card, num = parse_numarg(arg)
    if not card or not num:
        raise UsageError('<NUM> <CARD>')
    assert_activedeck()
    if active_deck.sideboard.add(card, num):
        cmd_listall('')
    else:
        print('Unable to find card data.')

def cmd_remove(arg):
    """Remove a card from the active deck."""
    card, num = parse_numarg(arg)
    if not card or not num:
        raise UsageError('<NUM> <CARD>')
    assert_activedeck()
    if card.lower() not in active_deck.deck.cards:
        raise ImproperArgError('Card is not in active deck.')
    active_deck.deck.remove(card, num)
    cmd_listall('')

def cmd_removeside(arg):
    """Remove a card from the active deck's sideboard."""
    card, num = parse_numarg(arg)
    if not card or not num:
        raise UsageError('<NUM> <CARD>')
    assert_activedeck()
    if card.lower() not in active_deck.sideboard.cards:
        raise ImproperArgError('Card is not in active deck\'s sideboard.')
    active_deck.sideboard.remove(card, num)
    cmd_listall('')

def cmd_stats(arg):
    """Print active deck and sideboard size."""
    assert_activedeck()
    print('deck size: %d' % active_deck.deck.size())
    print('sideboard size: %d' % active_deck.sideboard.size())
    print('total size: %d' %
          (active_deck.deck.size() + active_deck.sideboard.size()))

def cmd_refreshdata(arg):
    """Refresh all card data from gatherer."""
    assert_activedeck()
    active_deck.refreshData()
    print('Done.')

def cmd_list(arg, summarize=False):
    """Print active deck's deck listing. Show only cards with Type <ARG>."""
    assert_activedeck()
    sep = '-' * 80
    print(sep)
    boldprint(active_deck.name.center(80))
    print(sep)
    ip = 0
    for c in active_deck.deck.manaSorted():
        card = active_deck.cardData.data[c]
        if print_deckcardline(active_deck.deck.cards[c], card,
                              reqType=arg):
            if summarize:
                if card.summary():
                    print('       ' + card.summary())
                print('')
            ip += active_deck.deck.cards[c]
    print('Total: ' + str(ip))

def cmd_listside(arg, summarize=False):
    """Print active deck's sideboad listing. Show only cards with Type <ARG>."""
    assert_activedeck()
    sep = '-' * 80
    print(string.center(' Sideboard ', 80, '-'))
    ip = 0
    for c in active_deck.sideboard.manaSorted():
        card = active_deck.cardData.data[c]
        if print_deckcardline(active_deck.sideboard.cards[c], card,
                              reqType=arg):
            if summarize:
                if card.summary():
                    print('       ' + card.summary())
                print('')
            ip += 1
    if ip == 0:
        print('-nothing-'.center(80))

def cmd_listall(arg):
    """Print active deck listing, optionally filtered by Type."""
    assert_activedeck()
    cmd_list(arg)
    cmd_listside(arg)

def cmd_summary(arg):
    """Print a summary of cards in the deck, filtered by Type."""
    assert_activedeck()
    cmd_list(arg, summarize=True)

def cmd_sidesummary(arg):
    """Print a summary of sideboarded cards, filtered by Type."""
    assert_activedeck()
    cmd_listside(arg, summarize=True)

def cmd_link(arg):
    """Display a Gatherer link for a card."""
    if not arg:
        raise UsageError('<CARD>')
    print(cards.url(arg))

def cmd_web(arg):
    """Open default web browser to a card or mtgdeckbuilder deck."""
    if not arg:
        raise UsageError('<CARD|DECK_ID>')
    elif re.match('\d+$',arg):
        webbrowser.open_new_tab(
            'http://www.mtgdeckbuilder.net/Decks/ViewDeck/' + arg)
    else:
        webbrowser.open_new_tab(cards.url(arg))

def cmd_card(arg):
    """Display card info from an online database."""
    if not arg:
        raise UsageError('<CARD>')
    # Use preloaded data if already in active deck, otherwise fetch.
    if active_deck and arg.lower() in active_deck.cardData.data:
        card = active_deck.cardData.data[arg.lower()]
    else:
        card = cards.Card(arg)
        card.load()
    if not card.loaded:
        print('Unable to find card data.')
        return
    if card.cardback:
        print('\n--- SIDE ONE ---')
        mprint(card.color(), str(card))
        print('\n--- SIDE TWO ---')
        mprint(card.cardback.color(), str(card.cardback))
    else:
        print('')
        mprint(card.color(), str(card))

def cmd_hand(arg):
    """Generate a random draw hand."""
    assert_activedeck()
    print('')
    for c in active_deck.deck.randCards(7):
        d = active_deck.cardData.data[c]
        mprint(d.color(), d.snippet())
    print('')

def cmd_managram(arg):
    """Display the managram."""
    assert_activedeck()
    m = active_deck.deck.maxConvertedManaCost()
    cprint('bold', '\n Cost   Cards')
    print('------|-------')
    for i in xrange(m + 1):
        c = active_deck.deck.countConvertedManaFilter(i)
        print(str(i).rjust(4) + str(c).rjust(8) + '  ' + ('=' * c))

def cmd_prob(arg):
    """Probability of drawing a certain selection of cards."""
    if not arg:
        raise UsageError('<NUM> <CARD> [OR <CARD> [OR ...]] [AND <NUM> '
                             '<CARD> [OR <CARD> [OR ...]] [AND ...]]')
    assert_activedeck()
    nlist = parse_andlist(arg)
    # Print actual probabilities.
    cprint('bold', '\n Turn   Cards   Probability')
    print('------|-------|-------------')
    for i in xrange(16):
        print(str(i).rjust(4) + str(7 + i).rjust(8) + '    ' +
              ('%.2f' % (active_deck.prob_anddraw(nlist, 7 + i)*100)).rjust(8) +
              '%')

def parse_andlist(arg):
    """Parse a list of draw AND requirements."""
    cl = []
    l = [parse_orlist(s, cl) for s in re.split('\s+AND\s+', arg)]
    if len(cl) != len(set(cl)):
        raise ImproperArgError('Each card may appear only once.')
    return l

def parse_orlist(arg, cardlist=None):
    """Parse a list of card OR tuples."""
    assert_activedeck()
    d = 1
    m = re.match('(\d+)\s+(.*$)', arg)
    if m:
        d = int(m.group(1))
        arg = m.group(2)
    orlist = re.split('\s+OR\s+', arg)
    
    if any((c not in active_deck.deck.cards for c in orlist)):
        raise ImproperArgError('Cards are not in active deck.')
    s = sum((active_deck.deck.cards[c] for c in orlist))
    if cardlist is not None:
        cardlist.extend(orlist)
    return (d, s)

def cmd_togglecolor(arg):
    """Toggle use of ANSI color escape sequences."""
    global global_coloron
    global_coloron = not global_coloron

def cmd_csdist(arg):
    """Display color symbol distribution for the active deck."""
    assert_activedeck()
    mdict = {}
    for color in _cardcolors.keys():
        mdict[color] = active_deck.deck.countColorSymbol(color)
    tot = sum(mdict.values())
    cprint('bold','\n' + str.center('Color Symbol Distribution',34))
    print('-' * 34)
    for color in mdict.keys():
        n = mdict[color];
        mprint(color, '  {' + color + '} x' + str(n) + 
                '\t(%.0f' % (float(n) / tot * 100) + 
                '% of symbols)' ) if n else ''

def cmd_cdist(arg):
    """Display card color distribution for the active deck."""
    assert_activedeck()
    mdict = {}
    for color in _cardcolors.keys():
        mdict[color] = active_deck.deck.countColor(color)
    tot = sum(mdict.values())
    cprint('bold','\n' + str.center('Card Color Distribution',47))
    print('-' * 47)
    for color in mdict.keys():
        n = mdict[color];
        mprint(color, '  {' + color + '} x' + str(n) + 
                '\t(%.0f' % (float(n) / tot * 100) + '% of colors, ' +
                '%.0f' % (float(n) / len(active_deck.deck.list()) * 100) +\
                '% of cards)') if n else ''

def cmd_import(arg):
    """Import a deck from mtgdeckbuilder.net by ID number."""
    if not arg:
        raise UsageError('<DECK_ID>')
    dl = deck.scrapeDeckListing(arg)
    if dl is None:
        return
    cmd_deck(dl.pop(0))
    assert_activedeck()
    pile = active_deck.deck
    i = 0
    tot = len(dl)-1
    for cardset in dl:
        m = re.match('(\d+)\s+(.*)$', cardset)
        if m:
            num = int(m.group(1))
            cname = m.group(2)
            sys.stdout.write('  Importing... {0:.0f}% complete\r' 
                    .format(float(i)/tot*100))
            sys.stdout.flush()
            if not pile.add(cname, num):
                print('Unable to find card data for \'' + cname + '\'.')
            i += 1
        elif re.match('Sideboard$', cardset):
            pile = active_deck.sideboard
        else:
            print('Problem parsing \'' + cardset + '\'.')
    cmd_listall('')

def cmd_price(arg):
    """Display the price for a card."""
    if not arg:
        raise UsageError('<CARD>')
    prices = cards.scrapeCardPrice(arg)
    if prices:
        print('-' * 20)
        print('  Low:\t$%.2f\n' % prices['L']
                + '  Mean:\t$%.2f\n' % prices['M']
                + '  High:\t$%.2f\n' % prices['H'])
    else:
        print('Unable to find card data.')

def cmd_cost(arg):
    """Shows the estimated cost of a deck."""
    if not arg:
        arg = 'M'
    if not re.match('L|M|H$',arg):
        raise UsageError('[L|M|H]')
    assert_activedeck()
    sep = '-' * 80
    print(sep)
    boldprint(active_deck.name.center(80))
    print(sep)
    tot = 0
    # print(str('Per Card').rjust(38) + str('Card Set').rjust(11))
    for c in active_deck.deck.manaSorted():
        card = active_deck.cardData.data[c]
        tot += print_deckcardprice(active_deck.deck.cards[c], card, arg)
    print('\n' + str('Total:').rjust(39) + str('$%.2f' % tot).rjust(9))

def print_deckcardprice(count, card, p='M'):
    """Print the price for a cardset in the active deck."""
    if p is None:
        return None
    price = cards.scrapeCardPrice(card.name, p)
    if price is None:
        return None
    tot = price * count
    mprint(card.color(), ' ' +\
           cards.cutoff_text(card.name, 24).ljust(25) +\
           str('$%.2f x' % price).rjust(8) + str(count).rjust(3) + ' = ' +\
           str('$%.2f' % tot).rjust(8))
    return tot

# Global state.
global_coloron = True
active_deck = None
cmd_dict = {
    'help': cmd_help,
    'deck': cmd_deck,
    'deckname': cmd_deckname,
    'save': cmd_save,
    'randhand': cmd_hand,
    'add': cmd_add,
    'rm': cmd_remove,
    'side': cmd_side,
    'sideadd': cmd_addside,
    'siderm': cmd_removeside,
    'size': cmd_stats,
    'managram': cmd_managram,
    'prob': cmd_prob,
    'card': cmd_card,
    'link': cmd_link,
    'list': cmd_listall,
    'summ': cmd_summary,
    'summside': cmd_sidesummary,
    'togglecolor': cmd_togglecolor,
    'refreshdata': cmd_refreshdata,
    'exit': cmd_exit,
    'web': cmd_web,
    'decklist': cmd_decklist,
    'csdist': cmd_csdist,
    'cdist': cmd_cdist,
    'import': cmd_import,
    'price': cmd_price,
    'cost':cmd_cost}


# Readline
_readline_regexp = '(.+(?:AND|OR|\d+)\s+|\w+\s+)(.+)$'

def readline_completer(text, state):
    """The GNU readline completer function."""
    l = []
    if not re.search('\s', text):
        l = filter(lambda k: re.match(text, k), cmd_dict.iterkeys())
    elif active_deck:
        m = re.match(_readline_regexp, text)
        if m:
            cards = active_deck.cardData.cardNames()
            l = [m.group(1) + c for c in
                 filter(lambda k: re.match(m.group(2), k), cards)]
    if state < len(l):
        return l[state]
    return  None

def readline_printmatches(substitution, matches, longest_match_length):
    """Print multiple readline matches."""
    print('')
    m = re.match(_readline_regexp, substitution)
    printmatches = []
    for mtext in matches:
        s = mtext
        if m:
            k = re.match(_readline_regexp, mtext)
            s = k.group(2)
        printmatches.append(s)
    # Print matches.
    spacing = max((len(s) for s in printmatches))
    for s in printmatches:
        print(s.ljust(spacing), end='  ')
    print('\n' + get_prompt() + substitution, end='')

def readline_init():
    """Initialize readline."""
    readline.set_completer_delims('')
    readline.parse_and_bind('tab: complete')
    readline.set_completer(readline_completer)
    readline.set_completion_display_matches_hook(readline_printmatches)


# Import readline, if avaliable
try:
    import readline
except ImportError:
    pass
else:
    readline_init()


if __name__ == "__main__":
    main()
