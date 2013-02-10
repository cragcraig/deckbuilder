#!/usr/bin/python
from __future__ import print_function, with_statement

import itertools
import re
import string
import sys
import time
import cPickle as pickle
import webbrowser
import os

import cards
import deck
import utils

try:
    import readline
except ImportError:
    pass

# Readline
_READLINE_REGEX = re.compile('(.+(?:AND|OR|\d+)\s+|\w+\s+)(.+)$')

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
    # Arguments
    try:
        import argparse
    except ImportError:
        print('Missing module argparse, arguments not supported.')
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('deck', metavar='DECKFILE', type=str, nargs='?',
                            default=None, help='an optional deckfile to load')
        args = parser.parse_args()
        if args.deck is not None:
            try:
                with open(args.deck, "rb") as f:
                    global active_deck
                    active_deck = pickle.load(f)
            except IOError:
                print('Unable to load deckfile: %s' % args.deck)
    # Warning for Python below 2.7
    if sys.version_info[:2] < (2, 7):
        print('Data scraping may fail with Python prior to version 2.7.')
        print('You are using Python %d.%d.' % sys.version_info[:2])
    # Init readline, if avaliable
    if 'readline' in sys.modules:
        readline_init()
    else:
        print('\nThe readline module is not avaliable,')
        print('line editing and tab completion has been disabled.')
    # Main loop.
    cont = True
    cmd = ''
    prev = ''
    while cont:
        cmd = prompt_cmd()
        if cmd == '':
            cmd = prev
        cont = exec_cmd(cmd)
        prev = cmd

def _parse_cmdline(cmdline):
    """Parse a command line string. 

    Returns:
      Tuple (cmd, arg)
    """
    m = re.match('(\w+)(?:\s+(.*))?$', cmdline)
    if not m:
      return (None, None)
    return (m.group(1), m.group(2))

# Command interpreter.
def exec_cmd(cmdline):
    """Interpret a command."""
    cmd, arg = _parse_cmdline(cmdline)
    if not cmd:
        print('Bad command.')
    else:
        cmd_callable = get_cmd(cmd)
        if not cmd:
            print('Type a command. Try \'help\'.')
        elif cmd_callable:
            try:
                cmd_callable(arg)
            except ImproperArgError as e:
                print(str(e))
            except UsageError as e:
                print('usage: ' + cmd + ' ' + str(e))
            except MissingDeckError:
                print('No active deck. Create a new deck with the \'deck\' '
                      'command.')
            except cards.ScrapeError as e:
                print('Scrape failed: ' + str(e))
            if 'readline' in sys.modules:
                readline.add_history(cmdline)
        else:
            print('%s is not a command. Try \'help\'.' % str(cmd))
    return True

def get_cmd(cmd_name):
    """Get the command function for cmd_name."""
    for cmds in cmd_dict.itervalues():
        if cmd_name in cmds:
            return cmds[cmd_name]
    return None
    
def get_prompt():
    """Get the command prompt text."""
    if active_deck:
        return active_deck.name + '> '
    else:
        return 'mtg> '

def prompt_cmd():
    """Print command prompt for the current state."""
    try:
        return utils.asciify_decode(raw_input(get_prompt())).strip()
    except EOFError:
        cmd_exit('')
    except KeyboardInterrupt:
        cmd_exit('')
    return ''

def parse_numarg(arg, default_num=1):
    """Parse an argument of the form [NUM] ARG. Returns (num, arg)."""
    if not arg:
        return (None, None)
    m = re.match('(\d*)\s*(.*)$', arg)
    if m:
        num = int(m.group(1)) if m.group(1) else default_num
        return (m.group(2), num)
    raise ImproperArgError('Argument should be of the form [<NUM>] <ARG>.')

def print_deckcardline(count, card, star=' ', reqType=None):
    """Print a snippet line for a card in the active deck.
    
    If reqType is not none, skips printing the line if card does not have the
    specified Type.
    """
    if reqType and not card.hasTypes(reqType.split()):
        return False
    print(str(count).rjust(3), end='')
    print(' %s ' % star, end='')

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
    """Detailed help for a command; with no arguments lists all cmds.

    Optional: Command for which to provide detailed help.
    """
    # Detailed help for a command.
    if arg:
        cmd_callable = get_cmd(arg)
        if cmd_callable:
            print(cmd_callable.__doc__)
            return
    # Comprehensive short help listing.
    cprint('bold', 'Avaliable commands:\n')
    w = max((len(h) for h in
             itertools.chain.from_iterable(cmd_dict.itervalues()))) + 1
    for title, cmds in sorted(cmd_dict.iteritems(), key=lambda t: t[0]):
        boldprint(title)
        for name, cmd in sorted(cmds.iteritems(), key=lambda t: t[0]):
            print(' ' + name.ljust(w) + ' - ' + cmd.__doc__.split('\n')[0])
        print('')

def _print_slowly(s, end='\n'):
    for c in s:
        print(c, end='')
        sys.stdout.flush()
        time.sleep(0.1)
    print('', end=end)

def _run_tutorial_cmd(cmdline):
    """Runs a command string as if the user had typed it."""
    cmd, arg = _parse_cmdline(cmdline)
    cmd_callable = get_cmd(cmd)
    if cmd_callable is None:
        raise Exception('Bad tutorial command: %s' % cmd)
    print(get_prompt(), end='')
    sys.stdout.flush()
    _print_slowly(cmdline)
    cmd_callable(arg)


def cmd_tutorial(arg):
    """Run an introductory tutorial."""
    _run_tutorial_cmd('deck tutorial')
    time.sleep(0.25)
    _run_tutorial_cmd('card Verdant Force')
    time.sleep(1)
    _run_tutorial_cmd('add 4 Verdant Force')
    _run_tutorial_cmd('add 4 Fireball')
    _run_tutorial_cmd('add 4 Goblin Sharpshooter')
    _run_tutorial_cmd('add 4 Llanowar Elves')
    _run_tutorial_cmd('add 4 Birds of Paradise')
    _run_tutorial_cmd('add 4 Shivan Dragon')
    _run_tutorial_cmd('add 4 Biomass Mutation')
    _run_tutorial_cmd('add 4 Huntmaster of the Fells')
    _run_tutorial_cmd('add 14 Forest')
    _run_tutorial_cmd('add 14 Island')
    _run_tutorial_cmd('prob 2 Island OR Forest')
    time.sleep(1)
    _run_tutorial_cmd('prob 5 Llanowar Elves OR Birds of Paradise '
                      'OR Forest OR Island AND 2 Fireball')
    time.sleep(1)
    _run_tutorial_cmd('card Huntmaster of the Fells')
    time.sleep(1)
    _run_tutorial_cmd('summ Creature')
    print('')
    print('Try \'help\' to view the full list of avaliable commands.')

def cmd_deck(arg):
    """Create or load an active deck.

    Required: Deck name to load, or to create if it does not exist.
    """
    global active_deck
    if not arg:
        raise UsageError('NAME')
    try:
        with open(deck.filename(arg), "rb") as f:
            active_deck = pickle.load(f)
            print('Loaded deck \'' + active_deck.name + '\'.')
    except IOError:
        active_deck = deck.Deck(arg)
        print('Created new deck \'' + active_deck.name + '\'.')

def cmd_decklist(arg):
    """List the saved decks in the current directory."""
    print('')
    for fn in os.listdir('.'):
        if fn.endswith('.deck'):
            print(pickle.load(open(fn, "rb")).name)

def cmd_save(arg):
    """Save the active deck."""
    assert_activedeck()
    with open(deck.filename(active_deck.name), "wb") as f:
        pickle.dump(active_deck, f)
    print('Saved deck \'' + active_deck.name + '\'.')

def cmd_deckname(arg):
    """Change the name of the active deck.

    Required: The new deck name.
    """
    if not arg or len(arg) == 0:
        raise UsageError('NAME')
    assert_activedeck()
    active_deck.name = arg
    print('Renamed active deck \'' + active_deck.name + '\'.')

def cmd_side(arg):
    """Move a card from the active deck to its sideboard.

    Required: The card name.
    """
    if not arg:
        raise UsageError('CARD')
    assert_activedeck()
    card = arg.lower()
    if card not in active_deck.deck.cards:
        raise ImproperArgError('Card is not in active deck.')
    num = active_deck.deck.cards[card]
    active_deck.deck.remove(card, num)
    active_deck.sideboard.add(card, num)
    cmd_listall('')

def cmd_add(arg):
    """Add a card to the active deck.

    Required: The card name.
    """
    card, num = parse_numarg(arg, 1)
    if not card or not num:
        raise UsageError('[NUM] CARD')
    assert_activedeck()
    if active_deck.deck.add(card, num):
        cmd_listall('')
    else:
        print('Unable to find card data.')

def cmd_addside(arg):
    """Add a card to the active deck's sideboard.

    Required: The card name.
    """
    card, num = parse_numarg(arg, 1)
    if not card or not num:
        raise UsageError('[NUM] CARD')
    assert_activedeck()
    if active_deck.sideboard.add(card, num):
        cmd_listall('')
    else:
        print('Unable to find card data.')

def cmd_remove(arg):
    """Remove a card from the active deck.

    Required: The card name.
    """
    card, num = parse_numarg(arg, None)
    if not card:
        raise UsageError('[NUM] CARD')
    assert_activedeck()
    if card.lower() not in active_deck.deck.cards:
        raise ImproperArgError('Card is not in active deck.')
    if num is None:
      num = active_deck.deck.cards[card]
    active_deck.deck.remove(card, num)
    cmd_listall('')

def cmd_removeside(arg):
    """Remove a card from the active deck's sideboard.

    Required: The card name.
    """
    card, num = parse_numarg(arg, None)
    if not card:
        raise UsageError('[NUM] CARD')
    assert_activedeck()
    if card.lower() not in active_deck.sideboard.cards:
        raise ImproperArgError('Card is not in active deck\'s sideboard.')
    if num is None:
      num = active_deck.sideboard.cards[card]
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
    """Print active deck's deck listing, optionally filtered by Type.

    Optional: A card Type or Sub-Type by which to filter.
    """
    assert_activedeck()
    sep = '-' * 80
    print(sep)
    boldprint(active_deck.name.center(80))
    print(sep)
    ip = 0
    for c in active_deck.deck.manaSorted():
        card = active_deck.cardData.data[c]
        if print_deckcardline(active_deck.deck.cards[c], card,
                              active_deck.deck.getStar(c), reqType=arg):
            if summarize:
                if card.summary():
                    print('       ' + card.summary())
                print('')
            ip += active_deck.deck.cards[c]
    print('Total: ' + str(ip))

def cmd_listside(arg, summarize=False):
    """Print active deck's sideboad listing, optionally filtered by Type.

    Optional: A card Type or Sub-Type by which to filter.
    """
    assert_activedeck()
    sep = '-' * 80
    print(string.center(' Sideboard ', 80, '-'))
    ip = 0
    for c in active_deck.sideboard.manaSorted():
        card = active_deck.cardData.data[c]
        if print_deckcardline(active_deck.sideboard.cards[c], card,
                              active_deck.sideboard.getStar(c), reqType=arg):
            if summarize:
                if card.summary():
                    print('       ' + card.summary())
                print('')
            ip += 1
    if ip == 0:
        print('-nothing-'.center(80))

def cmd_listall(arg):
    """Print active deck listing, optionally filtered by Type.

    Optional: A card Type or Sub-Type by which to filter.
    """
    assert_activedeck()
    cmd_list(arg)
    cmd_listside(arg)

def cmd_summary(arg):
    """Print a summary of cards in the deck, filtered by Type.

    Optional: A card Type or Sub-Type by which to filter.
    """
    assert_activedeck()
    cmd_list(arg, summarize=True)

def cmd_sidesummary(arg):
    """Print a summary of sideboarded cards, filtered by Type.

    Optional: A card Type or Sub-Type by which to filter.
    """
    assert_activedeck()
    cmd_listside(arg, summarize=True)

def cmd_link(arg):
    """Display a Gatherer link for a card.

    Required: The card name.
    """
    if not arg:
        raise UsageError('CARD')
    print(cards.url(arg))

def cmd_web(arg):
    """Open default web browser to a card or mtgdeckbuilder deck.

    Required: The card name or mtgdeckbuilder deck ID number.
    """
    if not arg:
        raise UsageError('CARD|DECK_ID')
    elif re.match('\d+$',arg):
        webbrowser.open_new_tab(
            'http://www.mtgdeckbuilder.net/Decks/ViewDeck/' + arg)
    else:
        webbrowser.open_new_tab(cards.url(arg))

def cmd_card(arg):
    """Display card info from an online database.

    Required: The card name.
    """
    if not arg:
        raise UsageError('CARD')
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
        print('\n--- FRONT/TOP FACE ---')
        mprint(card.color(), str(card))
        print('\n--- BACK/BOTTOM FACE ---')
        mprint(card.cardback.color(), str(card.cardback))
    else:
        print('')
        mprint(card.color(), str(card))

def cmd_star(arg):
    """Mark a card with the optionally provided symbol.

    Required: The card name.
    """
    if not arg:
        raise UsageError('CARD [SYMBOL]')
    m = re.match('(.+?)(?:\s+(\S))?$', arg)
    if not m:
        raise UsageError('CARD [SYMBOL]')
    card = m.group(1)
    star = m.group(2) if m.group(2) else '*'
    if len(star) != 1:
        raise ImproperArgError('SYMBOL must be exactly one character.')
    assert_activedeck()
    if not card.lower() in active_deck.deck.cards:
        raise ImproperArgError('Card doesn\'t exist in deck.')
    active_deck.deck.star(card, star)

def cmd_unstar(arg):
    """Unmark a card.

    Required: The card name.
    """
    if not arg:
        raise UsageError('CARD')
    assert_activedeck()
    if not arg.lower() in active_deck.deck.cards:
        raise ImproperArgError('Card doesn\'t exist in deck.')
    active_deck.deck.unstar(arg)

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

def cmd_uberprob(arg):
    """Incomplete, see 'help uberprob'.
    
    Supports expresson-style strings following this format:
      Card Name -> The full card name.
      P/T -> Power and Toughness as Integer expressions.
      'Type' -> Card Type or Sub-Type.
      "Text" -> Card has Text in the body of the card.
      |Cost| -> Coverted mana cost as an Integer expression.
      .C -> Card color, C is one of B,W,R,G,U.

    Operators:
      () -> Group multiple expressions.
      | -> OR
      & -> AND
      ~ -> NOT

    Integer expressions:
      * -> Any value.
      >X -> Any value greater than X, inclusive.
      <X -> Any value less than X, inclusive.
      [X,Y] -> Any value between X and Y, inclusive.
      X -> Exactly the value X.
      v -> A variable value (usually "X" or "*").
    """
    pass

def cmd_prob(arg):
    """Probability of drawing a certain selection of cards.

    Required: Expression following this format:
      NUM CARD [OR CARD [OR ...]] [AND NUM CARD [OR CARD [OR ...]] [AND ...]]

    Operator precedence from high to low:
      OR, NUM, AND

    Example precedence:
      (2 (card OR card)) AND (3 (card OR card OR card) AND card)

    Note: NUM indicates drawing a MINIMUM of that number. So "3 Fireball" will
      match a hand with 3 OR MORE Fireballs.
    """
    if not arg:
        raise UsageError('Invalid expression, see \'help prob\'.')
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
    orlist = [c.lower() for c in orlist]
    
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
        mprint(color, ' {' + color + '} x ' + str(n) + 
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
        mprint(color, ' {' + color + '} x ' + str(n) + 
                '\t(%.0f' % (float(n) / tot * 100) + '% of colors, ' +
                '%.0f' % (float(n) / len(active_deck.deck.list()) * 100) +\
                '% of cards)') if n else ''

def cmd_import(arg):
    """Import a deck from mtgdeckbuilder.net by ID number.

    Required: mtgdeckbuilder ID number.
    """
    if not arg:
        raise UsageError('DECK_ID')
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
    """Display the price for a card.

    Required: The card name.
    """
    if not arg:
        raise UsageError('CARD')
    prices = cards.scrape_card_price(arg)
    if prices:
        print('-' * 20)
        print('  Low:\t$%.2f\n' % prices['L']
                + '  Avg:\t$%.2f\n' % prices['M']
                + '  High:\t$%.2f\n' % prices['H'])
    else:
        print('Unable to find card data.')

def cmd_costall(arg):
    """Shows the estimated cost of the active deck."""
    if not arg:
        arg = 'M'
    if not re.match('low|avg|high$', arg):
        raise UsageError('[low|avg|high]')
    assert_activedeck()
    tot = cmd_cost(arg)
    print('')
    tot += cmd_costside(arg)
    print('\n' + str('Total:').rjust(39) + str('$%.2f' % tot).rjust(9))

def cmd_cost(arg):
    """Shows the estimated cost of the active main deck."""
    if not arg:
        arg = 'M'
    if not re.match('low|avg|high$',arg):
        raise UsageError('[low|avg|high]')
    assert_activedeck()
    sep = '-' * 80
    print(sep)
    boldprint(active_deck.name.center(80))
    print(sep)
    tot = 0
    # print(str('Per Card').rjust(38) + str('Card Set').rjust(11))
    for c in active_deck.deck.manaSorted():
        card = active_deck.cardData.data[c]
        cost = print_deckcardprice(active_deck.deck.cards[c], card, arg)
        tot += cost if cost else 0
    print('\n' + str('Deck Subtotal:').rjust(39) + str('$%.2f' % tot).rjust(9))
    return tot

def cmd_costside(arg):
    """Shows the estimated cost of the active sideboard."""
    if not arg:
        arg = 'M'
    if not re.match('L|M|H$',arg):
        raise UsageError('[L|M|H]')
    assert_activedeck()
    sep = '-' * 80
    print(string.center(' Sideboard ', 80, '-'))
    tot = 0
    # print(str('Per Card').rjust(38) + str('Card Set').rjust(11))
    for c in active_deck.sideboard.manaSorted():
        card = active_deck.cardData.data[c]
        cost = print_deckcardprice(active_deck.sideboard.cards[c], card, arg)
        tot += cost if cost else 0
    if tot == 0:
        print('-nothing-'.center(80))
    print('\n' + str('Sideboard Subtotal:').rjust(39) + str('$%.2f' % tot).rjust(9))
    return tot
    
def print_deckcardprice(count, card, p='avg'):
    """Print the price for a cardset in the active deck."""
    if p is None:
        return None
    price = cards.scrape_card_price(card.name, p)
    if price is None:
        print('Unable to get price for %s' % card.name)
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
    'Save, Load, or Import Deck': {
        'deck': cmd_deck,
        'deckname': cmd_deckname,
        'save': cmd_save,
        'import': cmd_import,
        'decklist': cmd_decklist,
    },
    'Modify Deck': {
        'add': cmd_add,
        'rm': cmd_remove,
        'star': cmd_star,
        'unstar': cmd_unstar,
    },
    'Modify Sideboard': {
        'sideadd': cmd_addside,
        'siderm': cmd_removeside,
        'side': cmd_side,
    },
    'Display Deck': {
        'list': cmd_listall,
        'summ': cmd_summary,
        'summside': cmd_sidesummary,
#        'cost': cmd_costall,  # Site changed.
    },
    'Statistics': {
        'size': cmd_stats,
        'randhand': cmd_hand,
        'managram': cmd_managram,
        'prob': cmd_prob,
        'uberprob': cmd_uberprob,
        'csdist': cmd_csdist,
        'cdist': cmd_cdist,
    },
    'Individual Cards': {
        'card': cmd_card,
#        'price': cmd_price,  # Site changed.
        'link': cmd_link,
        'web': cmd_web,
    },
    'System Commands': {
        'refreshdata': cmd_refreshdata,
        'togglecolor': cmd_togglecolor,
        'help': cmd_help,
        'tutorial': cmd_tutorial,
        'exit': cmd_exit,
    },
}

def iter_commands():
    for t in cmd_dict.itervalues():
        for c in t.iterkeys():
            yield c

def readline_completer(text, state):
    """The GNU readline completer function."""
    l = []
    if not re.search('\s', text):
        l = filter(lambda k: re.match(text, k), iter_commands())
    elif active_deck:
        m = _READLINE_REGEX.match(text)
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
    m = _READLINE_REGEX.match(substitution)
    printmatches = []
    for mtext in matches:
        s = mtext
        if m:
            k = _READLINE_REGEX.match(mtext)
            s = k.group(2)
        printmatches.append(s)
    # Print matches.
    spacing = max((len(s) for s in printmatches))
    for s in printmatches:
        print(s.ljust(spacing), end='   ')
    print('\n' + get_prompt() + substitution, end='')

def readline_init():
    """Initialize readline."""
    readline.set_completer_delims('')
    readline.parse_and_bind('tab: complete')
    readline.set_completer(readline_completer)
    readline.set_completion_display_matches_hook(readline_printmatches)


if __name__ == "__main__":
    main()
