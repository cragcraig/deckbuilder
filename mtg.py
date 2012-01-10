from __future__ import print_function, with_statement

import re
import string
import sys
import cPickle as pickle

import cards
import deck

def main():
    """Prompt and execute commands."""
    print('MtG Deck Builder')
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
            cmd_dict[cmd](arg)
        else:
            print('%s is not a command.' % str(cmd))
    return True

def prompt_cmd():
    """Print command prompt for the current state."""
    s = ''
    if active_deck:
        s = '[' + active_deck.name + ']'
    return raw_input(s + '# ')

def parse_numarg(arg):
    """Parse an argument of the form <NUM> <ARG>. Returns (num, arg)."""
    if not arg:
        return (None, None)
    m = re.match('(\d*)\s*(.*)$', arg)
    if m and m.group(1) and m.group(1) > 0:
        return (m.group(2), int(m.group(1)))
    return (None, None)

def print_deckcardline(card):
    """Print a snippet line for a card in the active deck."""
    print(str(active_deck.deck.cards[card]).rjust(3) + ' | ', end='')
    mprint(active_deck.cardData.data[card].color(),
           active_deck.cardData.data[card].snippet())

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

def cprint(color, s):
    """Print a string in color."""
    if global_coloron:
        print(_ansicode['bold'] + _ansicode[color] + s + _ansicode['reset'])
    else:
        print(s)

def mprint(cardcolor, s):
    """Print a string in the specified Magic card color."""
    if cardcolor and cardcolor in _cardcolors:
        cprint(_cardcolors[cardcolor], s)
    elif cardcolor and len(cardcolor) > 1:
        cprint('yellow', s)
    else:
        print(s)

def boldprint(s):
    """Print a string in bold."""
    if global_coloron:
        print(_ansicode['bold'] + s + _ansicode['reset'])
    else:
        print(s)

# Executeable commands.
def cmd_exit(arg):
    """Exit the program."""
    sys.exit(0)

def cmd_help(arg):
    """Print help text."""
    print('Avaliable commands:')
    w = max((len(h) for h in cmd_dict.iterkeys())) + 1
    for cmd in sorted(cmd_dict.keys()):
        print(cmd.ljust(w) + " - " + cmd_dict[cmd].__doc__)

def cmd_deck(arg):
    """Set the active deck."""
    global active_deck
    if not arg:
        print('usage: deck <NAME>')
        return
    try:
        with open(deck.filename(arg), "rb") as f:
            active_deck = pickle.load(f)
            print('Loaded deck \'' + active_deck.name + '\'.')
    except IOError:
        active_deck = deck.Deck(arg)
        print('Created new deck \'' + active_deck.name + '\'.')

def cmd_save(arg):
    """Save the active deck."""
    if not active_deck:
        print('No active deck.')
        return
    with open(deck.filename(active_deck.name), "wb") as f:
        pickle.dump(active_deck, f)
    print('Saved deck \'' + active_deck.name + '\'.')

def cmd_deckname(arg):
    """Change the name of the active deck."""
    if not arg:
        print('usage: deckname <NAME>')
        return
    active_deck.name = arg
    print('Renamed active deck \'' + active_deck.name + '\'.')

def cmd_add(arg):
    """Add a card to the active deck."""
    card, num = parse_numarg(arg)
    if not card or not num:
        print('usage: add [<NUM>] <CARD>')
        return
    elif not active_deck:
        print('No active deck.')
        return
    if active_deck.deck.add(card, num):
        cmd_list('')
    else:
        print('Unable to find card data.')

def cmd_addside(arg):
    """Add a card to the active deck's sideboard."""
    card, num = parse_numarg(arg)
    if not card or not num:
        print('usage: addside [<NUM>] <CARD>')
        return
    elif not active_deck:
        print('No active deck.')
        return
    if active_deck.sideboard.add(card, num):
        cmd_listside('')
    else:
        print('Unable to find card data.')

def cmd_remove(arg):
    """Remove a card from the active deck."""
    card, num = parse_numarg(arg)
    if not card or not num:
        print('usage: rm [<NUM>] <CARD>')
        return
    if not active_deck:
        print('No active deck.')
        return
    print(str(card) + ': ' + str(num))
    active_deck.deck.remove(card, num)
    cmd_list('')

def cmd_removeside(arg):
    """Remove a card from the active deck's sideboard."""
    card, num = parse_numarg(arg)
    if not card or not num:
        print('usage: rmside [<NUM>] <CARD>')
        return
    if not active_deck:
        print('No active deck.')
        return
    active_deck.sideboard.remove(card, num)
    cmd_listside('')

def cmd_stats(arg):
    """Print active deck stats."""
    if not active_deck:
        print('No active deck.')
        return
    print('deck size: %d' % active_deck.deck.size())
    print('sideboard size: %d' % active_deck.sideboard.size())

def cmd_refreshdata(arg):
    """Refresh all card data from gatherer."""
    if not active_deck:
        print('No active deck.')
        return
    active_deck.refreshData()
    print('Done.')

def cmd_list(arg):
    """Print active deck's main deck listing."""
    if not active_deck:
        print('No active deck.')
        return
    sep = '-' * 80
    print(sep)
    boldprint(active_deck.name.center(80))
    print(sep)
    for c in active_deck.deck.manaSorted():
        print_deckcardline(c)
    print('Deck: ' + str(active_deck.deck.size()))

def cmd_listside(arg):
    """Print active deck's sideboad listing."""
    if not active_deck:
        print('No active deck.')
        return
    sep = '-' * 80
    print(string.center(' Sideboard ', 80, '-'))
    for c in active_deck.sideboard.manaSorted():
        print_deckcardline(c)
    if active_deck.sideboard.size() == 0:
        print('-empty-'.center(80))

def cmd_listall(arg):
    """Print active deck listing."""
    if not active_deck:
        print('No active deck.')
        return
    cmd_list('')
    cmd_listside('')

def cmd_link(arg):
    """Print the Gatherer link for a card."""
    if not arg:
        print('usage: link <CARD>')
        return
    print(cards.url(arg))

def cmd_card(arg):
    """Display card info from database."""
    if not arg:
        print('usage: card <CARD>')
        return
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
    if not active_deck:
        print('No active deck.')
        return
    print('')
    for c in active_deck.deck.randCards(7):
        d = active_deck.cardData.data[c]
        mprint(d.color(), d.snippet())
    print('')

def cmd_managram(arg):
    """Display the managram."""
    if not active_deck:
        print('No active deck.')
        return
    m = active_deck.deck.maxConvertedManaCost()
    print('Cost | Cards')
    for i in xrange(m + 1):
        c = active_deck.deck.countConvertedManaFilter(i)
        print(str(i).rjust(4) + ' | ' + ('=' * c))

def cmd_prob(arg):
    """Probability of drawing a certain selection of cards on a turn."""
    if not arg or not re.match('\d+(\s*and\s*\d+)*$', arg):
        print('usage: prob <NUM> [and <NUM> [...]]')
        return
    if not active_deck:
        print('No active deck.')
        return
    n = re.split('\s+and\s+', arg)
    n = [int(i) for i in n]
    print('Turn | Prob')
    for i in xrange(16):
        print(str(i).rjust(3) + '  - ' +
              str(active_deck.prob_draw(n[0], 7 + i) * 100)[:5].rjust(5) + '%')

def cmd_togglecolor(arg):
    """Toggle use of ANSI color escape sequences."""
    global global_coloron
    global_coloron = not global_coloron


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
    'sideboard': cmd_addside,
    'sideboardrm': cmd_removeside,
    'size': cmd_stats,
    'managram': cmd_managram,
    'prob': cmd_prob,
    'card': cmd_card,
    'link': cmd_link,
    'list': cmd_listall,
    'togglecolor': cmd_togglecolor,
    'refreshdata': cmd_refreshdata,
    'exit': cmd_exit}

if __name__ == "__main__":
    main()
