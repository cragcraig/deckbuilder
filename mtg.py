import re
import sys
import cPickle as pickle

import cards
import deck

def main():
    """Prompt and execute commands."""
    print('MtG Deck Builder')
    cont = True
    while exec_cmd(prompt_cmd()):
        pass

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
            print('Type a command.')
        elif cmd in cmd_dict:
            for i in xrange(num):
                if not cmd_dict[cmd](arg):
                    break
        else:
            print('%s is not a command.' % str(cmd))
    return True

def prompt_cmd():
    """Print command prompt for the current state."""
    s = ''
    if active_deck:
        s = '[' + active_deck.name + ']'
    return raw_input(s + '# ')

# Executeable commands.
def cmd_exit(arg):
    """Exit the program."""
    sys.exit(0)
    return False

def cmd_help(arg):
    """Print help text."""
    print('Avaliable commands:')
    for cmd in sorted(cmd_dict.keys()):
        print(cmd.ljust(10) + " - " + cmd_dict[cmd].__doc__)
    return False

def cmd_deck(arg):
    """Set the active deck."""
    global active_deck
    if not arg:
        print('usage: deck <NAME>')
        return False
    try:
        with open(deck.filename(arg), "rb") as f:
            active_deck = pickle.load(f)
            print('Loaded deck \'' + active_deck.name + '\'.')
    except IOError:
        active_deck = deck.Deck(arg)
        print('Created new deck \'' + active_deck.name + '\'.')
    return False

def cmd_save(arg):
    """Save the active deck."""
    if not active_deck:
        print('No active deck.')
        return False
    with open(deck.filename(active_deck.name), "wb") as f:
        pickle.dump(active_deck, f)
    print('Saved deck \'' + active_deck.name + '\'.')
    return False

def cmd_deckname(arg):
    """Change the name of the active deck."""
    if not arg:
        print('usage: deckname <NAME>')
        return False
    active_deck.name = arg
    print('Renamed active deck \'' + active_deck.name + '\'.')
    return False

def cmd_add(arg):
    """Add a card to the active deck."""
    if not arg:
        print('usage: add [<NUM>] <CARD>')
        return False
    if not active_deck:
        print('No active deck.')
        return False
    active_deck.add(arg)
    return True

def cmd_remove(arg):
    """Remove a card from the active deck."""
    if not arg:
        print('usage: remove [<NUM>] <CARD>')
        return False
    if not active_deck:
        print('No active deck.')
        return False
    active_deck.remove(arg)
    return True

def cmd_stats(arg):
    """Print active deck stats."""
    if not active_deck:
        print('No active deck.')
        return False
    print('size: %d' % active_deck.size())
    return False

def cmd_list(arg):
    """Print active deck list."""
    if not active_deck:
        print('No active deck.')
        return False
    for k,v in active_deck.cards.iteritems():
        print(str(v).rjust(3) + ' ' + k)
    return False

def cmd_link(arg):
    """Print the Gatherer link for a card."""
    if not arg:
        print('usage: link <CARD>')
        return False
    print(cards.url(arg))

def cmd_card(arg):
    """Display card info from database."""
    card = cards.Card(arg)
    card.load()
    if not card.loaded:
        print('Unable to find card data.')
        return False
    if card.cardback:
        print('\n### FRONT ###\n' + str(card))
    else:
        print('\n' + str(card))
    if card.cardback:
        print('\n### BACK ###\n' + str(card.cardback))
    return False

# Global state.
active_deck = None
cmd_dict = {
    'help': cmd_help,
    'deck': cmd_deck,
    'deckname': cmd_deckname,
    'save': cmd_save,
    'add': cmd_add,
    'remove': cmd_remove,
    'stats': cmd_stats,
    'card': cmd_card,
    'link': cmd_link,
    'list': cmd_list,
    'exit': cmd_exit}

if __name__ == "__main__":
    main()
