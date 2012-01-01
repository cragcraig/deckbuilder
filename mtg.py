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
    m = re.match('(\w+)\s*(\d*)\s*(.*)', cmdstr)
    if not m:
        print('Bad command.')
    else:
        cmd = m.group(1)
        num = 1
        if m.group(2) and m.group(2) > 0:
            num = int(m.group(2))
        arg = m.group(3)
        if not cmd:
            print('Type a command. Try \'help\'.')
        elif cmd in cmd_dict:
            cmd_dict[cmd](arg, num)
        else:
            print('%s is not a command.' % str(cmd))
    return True

def prompt_cmd():
    """Print command prompt for the current state."""
    s = ''
    if active_deck:
        s = '[' + active_deck.name + ']'
    return raw_input(s + '# ')

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
    else:
        print(s)

def boldprint(s):
    """Print a string in bold."""
    if global_coloron:
        print(_ansicode['bold'] + s + _ansicode['reset'])
    else:
        print(s)

# Executeable commands.
def cmd_exit(arg, num):
    """Exit the program."""
    sys.exit(0)

def cmd_help(arg, num):
    """Print help text."""
    print('Avaliable commands:')
    w = max((len(h) for h in cmd_dict.iterkeys())) + 1
    for cmd in sorted(cmd_dict.keys()):
        print(cmd.ljust(w) + " - " + cmd_dict[cmd].__doc__)

def cmd_deck(arg, num):
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

def cmd_save(arg, num):
    """Save the active deck."""
    if not active_deck:
        print('No active deck.')
        return
    with open(deck.filename(active_deck.name), "wb") as f:
        pickle.dump(active_deck, f)
    print('Saved deck \'' + active_deck.name + '\'.')

def cmd_deckname(arg, num):
    """Change the name of the active deck."""
    if not arg:
        print('usage: deckname <NAME>')
        return
    active_deck.name = arg
    print('Renamed active deck \'' + active_deck.name + '\'.')

def cmd_add(arg, num):
    """Add a card to the active deck."""
    if not arg:
        print('usage: add [<NUM>] <CARD>')
        return
    elif not active_deck:
        print('No active deck.')
        return
    if active_deck.deck.add(arg, num):
        cmd_list('', 0)
    else:
        print('Unable to find card data.')

def cmd_addside(arg, num):
    """Add a card to the active deck's sideboard."""
    if not arg:
        print('usage: addside [<NUM>] <CARD>')
        return
    elif not active_deck:
        print('No active deck.')
        return
    if active_deck.sideboard.add(arg, num):
        cmd_listside('', 0)
    else:
        print('Unable to find card data.')

def cmd_remove(arg, num):
    """Remove a card from the active deck."""
    if not arg:
        print('usage: rm [<NUM>] <CARD>')
        return
    if not active_deck:
        print('No active deck.')
        return
    active_deck.deck.remove(arg, num)
    cmd_list('', 0)

def cmd_removeside(arg, num):
    """Remove a card from the active deck's sideboard."""
    if not arg:
        print('usage: rmside [<NUM>] <CARD>')
        return
    if not active_deck:
        print('No active deck.')
        return
    active_deck.sideboard.remove(arg, num)
    cmd_listside('', 0)

def cmd_stats(arg, num):
    """Print active deck stats."""
    if not active_deck:
        print('No active deck.')
        return
    print('deck size: %d' % active_deck.deck.size())
    print('sideboard size: %d' % active_deck.sideboard.size())

def cmd_list(arg, num):
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

def cmd_listside(arg, num):
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

def cmd_listall(arg, num):
    """Print active deck listing."""
    if not active_deck:
        print('No active deck.')
        return
    cmd_list('', 0)
    cmd_listside('', 0)

def cmd_link(arg, num):
    """Print the Gatherer link for a card."""
    if not arg:
        print('usage: link <CARD>')
        return
    print(cards.url(arg))

def cmd_card(arg, num):
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
        print('\n### FRONT ###')
        mprint(card.color(), str(card))
        print('\n### BACK ###')
        mprint(card.cardback.color(), str(card.cardback))
    else:
        print('')
        mprint(card.color(), str(card))

def cmd_hand(arg, num):
    """Generate a random draw hand."""
    if not active_deck:
        print('No active deck.')
        return
    print('')
    for c in active_deck.deck.randCards(7):
        d = active_deck.cardData.data[c]
        mprint(d.color(), d.snippet())
    print('')

def cmd_managram(arg, num):
    """Display the managram."""
    if not active_deck:
        print('No active deck.')
        return
    m = active_deck.deck.maxConvertedManaCost()
    print('Cost | Cards')
    for i in xrange(m + 1):
        c = active_deck.deck.countConvertedManaFilter(i)
        print(str(i).rjust(4) + ' | ' + ('=' * c))

def cmd_togglecolor(arg, num):
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
    'card': cmd_card,
    'link': cmd_link,
    'ls': cmd_listall,
    'togglecolor': cmd_togglecolor,
    'exit': cmd_exit}

if __name__ == "__main__":
    main()
