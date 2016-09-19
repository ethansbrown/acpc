# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 22:52:42 2016

@author: Ethan
"""

# parse bovada hh to acpc format

def get_starting_cards(cards):
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['s', 'h', 'd', 'c']
    suited = False
    if len(cards) != 4:
        print cards
        return None
    if cards[0] not in ranks or cards[2] not in ranks:
        print cards
        return None
    if cards[1] not in suits or cards[3] not in suits:
        print cards
        return None
    if cards[0] == cards[2]: # pocket pair
        return cards[0] + cards[2]
    if cards[1] == cards[3]: # suited
        suited = True
    if ranks.index(cards[0]) > ranks.index(cards[2]):
        if suited:
            return cards[0] + cards[2] + 's'
        else:   
            return cards[0] + cards[2] + 'o'
    else:
        if suited:
            return cards[2] + cards[0] + 's'
        else:
            return cards[2] + cards[0] + 'o'

def results(summary):
    '''returns list of lists of the form 
    [[hand_1, pnl_1], ..., [hand_n, pnl_n]]'''
    [hand_number, stacks, action, cards, pnl, seats] = summary.split(':')
    result = []
    cards = cards.split('|')
    pnl = pnl.split('|')
    if len(cards) == len(pnl):
        for i in range(len(cards)):
             result.append([get_starting_cards(cards[i].split('/')[0]), float(pnl[i])])
    return result

def average_aggregate(agg):
    avg = {}
    for hand in agg:
        avg[hand] = sum(agg[hand]) / len(agg[hand])
    return avg

def aggregate_results(history):
    agg = {}    
    for summary in history:
        for entry in results(summary):
            if entry[0] not in agg:
                agg[entry[0]] = []
            agg[entry[0]].append(entry[1])
    return agg

def get_history(filename):
    history = []
    with open(filename, 'r') as f:
        excerpt = ''
        for line in f.readlines():
            excerpt += line
            if line == '\n':
                #print len(excerpt)
                if len(excerpt) > 1:
                    history.append(get_hand_string(excerpt))
                excerpt = ''
    return history

def decompose(hand):
    [hand_number, stacks, action, cards, pnl, seats] = hand.split(':')
    #rake = sum(map(float, pnl.split('|')))
    return [hand_number, stacks, action, cards, pnl, seats]    
    
def get_hand_string(excerpt):
    lines = excerpt.split('\n')
    players = ['UTG', 'UTG+1', 'UTG+2', 'Dealer', 'Small Blind', 'Big Blind']
    seats = {}
    stacks = {}
    cards = {}
    pnl = {player: 0.0 for player in players}
    pre_actions = []
    flop_actions = []
    turn_actions = []
    river_actions = []
    mode = 'pre' # 'flop' 'turn' 'river'
    flop = turn = river = None    
    bb = 0
    for line in lines:
        try:
            if 'SUMMARY' in line:
                break
            if 'Bovada Hand' in line:
                hand_number = line.split(' ')[2][1:]
            if 'in chips' in line:
                dollar_split = line.split('$')
                colon_split = dollar_split[0].replace('[ME]', '').split(':')
                position = colon_split[1][1:-2].rstrip()
                seats[position] = colon_split[0][-1]
                stacks[position] = dollar_split[-1].split(' ')[0]
            else:
                if '$' in line:
                    if 'Calls' in line or 'Bets' in line or 'Raises' in line or 'All-in' in line:
                        position = line.split(':')[0].replace('[ME]', '').rstrip()                
                        amount = float(line.split('$')[-1])
                        pnl[position] -= amount
                    elif 'Return' in line or 'Hand result' in line:
                        position = line.split(':')[0].replace('[ME]', '').rstrip()                
                        amount = float(line.split('$')[-1])
                        pnl[position] += amount
                    else:
                        if 'Small' in line:
                            pnl['Small Blind'] -= float(line.split('$')[-1])
                        if 'Big' in line:
                            bb = float(line.split('$')[-1])
                            pnl['Big Blind'] -= bb
            if 'spot' in line:
                position = line.split(':')[0].replace('[ME]', '')[:-1].rstrip()
                hand = line.split('[')[-1].replace(' ', '').replace(']', '')
                cards[position] = hand        
            if 'FLOP' in line and '*' in line:            
                mode = 'flop'
                flop = line.split('[')[-1].replace(' ', '').replace(']', '')
            if 'TURN' in line and '*' in line:
                mode = 'turn'
                turn = line.split('[')[-1].replace(']', '')
            if 'RIVER' in line and '*' in line:
                mode = 'river'
                river = line.split('[')[-1].replace(']', '')
            action = None
            if 'Folds' in line:
                action = 'f'
            if 'Calls' in line or 'Checks' in line: 
                action = 'c'
            if 'All-in' in line:
                action = 'a'
            if 'Bets' in line:
                action = 'r' + line.split('$')[1]
            if 'raise' in line.lower():
                action = 'r' + line.split('to')[1].split('$')[1]
            if action is not None:
                action = action.rstrip()
            if action is not None:
                if mode == 'pre':
                    if action == 'a':
                        if sum([a.count('r') for a in pre_actions]) == 0:
                            action = 'r' + line.split('$')[1].rstrip()
                        else:
                            action = 'c'
                    pre_actions.append(action)
                if mode == 'flop':
                    if action == 'a':
                        if sum([a.count('r') for a in flop_actions]) == 0:
                            action = 'r' + line.split('$')[1].rstrip()
                        else:
                            action = 'c'
                    flop_actions.append(action)
                if mode == 'turn':
                    if action == 'a':
                        if sum([a.count('r') for a in turn_actions]) == 0:
                            action = 'r' + line.split('$')[1].rstrip()
                        else:
                            action = 'c'
                    turn_actions.append(action)
                if mode == 'river':
                    if action == 'a':
                        if sum([a.count('r') for a in river_actions]) == 0:
                            action = 'r' + line.split('$')[1].rstrip()
                        else:
                            action = 'c'
                    river_actions.append(action)
        except:
            print line

    players = [player for player in players if player in cards]
    
    current_bet = 0                
    hand_string = ''            
    hand_string += hand_number
    hand_string += ':'
    hand_string += '|'.join([stacks[player] for player in players])
    hand_string += ':'
    hand_string += ''.join(pre_actions)
    if any('r' in x for x in pre_actions):
        current_bet = [float(x[1:]) for x in pre_actions if 'r' in x][-1]
    else:
        current_bet = bb
    if len(flop_actions) > 0:
        # adjust by current bet
        flop_actions = ['r' + str(float(x[1:]) + current_bet) if 'r' in x else x for x in flop_actions]
        flop_actions = [x[:-2] if x.endswith('.0') else x for x in flop_actions]
        if any('r' in x for x in flop_actions):
            current_bet = [float(x[1:]) for x in flop_actions if 'r' in x][-1]
        hand_string += '/'
        hand_string += ''.join(flop_actions)
        if len(turn_actions) > 0:
            # adjust by current bet
            turn_actions = ['r' + str(float(x[1:]) + current_bet) if 'r' in x else x for x in turn_actions]            
            turn_actions = [x[:-2] if x.endswith('.0') else x for x in turn_actions]
            if any('r' in x for x in turn_actions):
                current_bet = [float(x[1:]) for x in turn_actions if 'r' in x][-1]
                
            hand_string += '/'
            hand_string += ''.join(turn_actions)
            if len(river_actions) > 0:
                # adjust by current bet
                river_actions = ['r' + str(float(x[1:]) + current_bet) if 'r' in x else x for x in river_actions]            
                river_actions = [x[:-2] if x.endswith('.0') else x for x in river_actions]
                hand_string += '/'
                hand_string += ''.join(river_actions)
    hand_string += ':'
    hand_string += '|'.join([cards[player] for player in players])
    if flop is not None:
        hand_string += '/' + flop
    if turn is not None:
        hand_string += '/' + turn
    if river is not None:
        hand_string += '/' + river
    hand_string += ':'
    hand_string += '|'.join([str(pnl[player]) for player in players])
    hand_string += ':'
    hand_string += '|'.join([seats[player] for player in players])
    return hand_string


hh = get_history('hh.txt')
hh[:10]
#rr = [hand for hand in hh if len(analyze(hand).split('/')) > 0 and analyze(hand).split('/')[0].count('r') > 1]