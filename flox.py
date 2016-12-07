import pygame_sdl2 as pygame
import sys
from pygame_sdl2.locals import *
import pygame_sdl2.gfxdraw as pygamegfx
import numpy as np
import copy
from scipy.misc import comb as choose
pygame.init()

size = width, height = 640, 480
middleScreen = int(width / 2), int(height / 2)
velocity = [0, 0]
black = 0, 0, 0
red = 255, 0, 0
green = 0, 255, 0
white = 255, 255, 255

class Base(object):
    def __init__(self):
        pass

    def _normalise(self, vector):
        if np.linalg.norm(vector) != 0:
            return np.asarray(vector) / np.linalg.norm(vector)
        else:
            return vector

    def _flatten(self, vector):
        return [elem for sublist in [vector] for elem in sublist]

    def _coin_flip(self):
        return np.random.randint(2)

class Frame(Base):
    def __init__(self, agents, size=(100, 100), draw=False):
        super(Frame, self).__init__()
        if draw:
            self._initialise_screen(size)
        self.agents = agents
        self._calculate_representations()

    def _calculate_representations(self):
        #list(set( deletes duplicates. frozenset is immutable set - 
        #such that duplicate deletion ignores ordering. turn back into 
        # lists after deduplicating
        self.pairs = [list(x) for x in 
                      list(set([frozenset([agent1, agent2]) 
                                   for agent1 in self.agents 
                                   for agent2 in self.agents 
                                   if agent1 != agent2]))]


    def neighbours(self, agent):
        return list(set([elem for pair in 
                [pair for pair in self.pairs if agent in pair]
                        for elem in pair]))

    def _initialise_screen(self, size):
        self.screen = pygame.display.set_mode(size)
        self.xlim, self.ylim = self.screen.get_size()
        self.xmin, self.ymin = 0, 0

    def advance(self):
        pass

    def adjust(self):
        pass

    def report(self):
        pass

    def draw(self):
        pass

    def run(self, n_ticks):
        for _ in range(n_ticks):
            print('ADVANCING')
            self.advance()
            print('ADJUSTING')
            self.adjust()
            print('REPORTING')
            self.report()

class financial_system(Frame):

    def __init__(self, agents, size=(100, 100), draw=False):
        super(financial_system, self).__init__(agents, size, draw)
        self.system_money = sum([agent.wallet for agent in agents])

    def advance(self):
        pass

    def adjust(self):
        pass

    def report(self):
        print(self.system_money)

class Agent(Base):
    def __init__(self):
        super(Agent, self).__init__() 

    def interact(self, other_agent):
        pass

class financial_agent(Agent):
    def __init__(self, initial_money):
        super(financial_agent, self).__init__()
        self.wallet = initial_money
        self.account = 0
        self.debt = 0
        self.can_loan = False
        self.needs_loan = False
        self.can_trade = False

    def __repr__(self):
        return 'financial_agent: wallet: {}, debt: {}'.format(self.wallet, self.debt)

    def interact(self, other_agent, amount, positive = True):
        if positive:
            self.wallet += amount
            other_agent.wallet -= amount
        else:
            self.wallet -= amount
            other_agent.wallet += amount

    def balance_books(self):
        pass

#NETLOGO simulation
class sys(financial_system):

    def __init__(self, agents, i_prob=0.1, size=(100, 100), draw=False):
        super(sys, self).__init__(agents, size, draw)
        self.i_prob = i_prob
    

    def __repr__(self):
        return 'sys: n_agents: {}'.format(len(self.agents))
    
    def accept_transaction(self):
        return (np.random.randn(1) < self.i_prob).all()
    
    def advance(self):
        # perform all transactions
        for pair in self.pairs:
            if np.array([agent.can_trade for agent in pair]).all(): 
                if self.accept_transaction():
                    if self._coin_flip():
                        pair[0].interact(pair[1], 2)
                    else:
                        pair[0].interact(pair[1], 5)
    
    def adjust(self):
        # balance all agents books
        for agent in self.agents:
            agent.balance_books()
        # take out loans
        for agent in self.agents:
            if agent.needs_loan:
                for neighbour in self.neighbours(agent):
                    if neighbour.can_loan:
                        neighbour.give_loan(agent, -agent.account)
        # update system parameters
        self.system_money = sum([agent.wallet for agent in self.agents])
        self.system_loans = sum([agent.debt for agent in self.agents])
        self.system_accounts = sum([agent.account for agent in self.agents])

    def report(self):
        print(self.system_money)
        print(self.system_loans)
        print(self.system_accounts)

class bank(financial_agent):
    def __init__(self, initial_money, reserve):
        super(bank, self).__init__(initial_money)
        self.reserve = reserve
        self.wallet = initial_money
        self.to_loan = initial_money * (1-self.reserve)
        self.can_loan = True
        self.needs_loan = False
        self.can_trade = False

    def give_loan(self, agent, amount):
        amount_to_loan = min(amount, self.to_loan)
        self.interact(agent, amount_to_loan, positive=False)
        agent.debt += amount_to_loan 
            
    def balance_books(self):
        # adjust the amount available to loan
        self.to_loan = self.wallet * (1 - self.reserve)

class consumer(financial_agent):
    def __init__(self, initial_money):
        super(consumer, self).__init__(initial_money)
        self.can_loan = False
        self.needs_loan = False
        self.can_trade = True
        self.debt = 0

    def balance_books(self):
        # consumer transfers positive or negative wallet balances 
        # to their account
        self.account += self.wallet
        # if the consumers account is negative, set the needs loan flag
        if self.account <= -10:
            self.needs_loan = True
        # pay off debts with positive account balances
        if self.account >= 0:
            if self.debt:
                self.debt -= self.account
                self.account = 0
                print('paying off debt')

class tests(object):
    def __init__(self, N):
        self.wallets = 100 * np.random.rand(N)
        self.bank_money = 100 * np.random.rand(1)[0]
        agents = [consumer(X) for X in self.wallets] + [bank(self.bank_money, 0.2)]
        self.financial_system = financial_system(agents)
        self.test_system = sys(agents)

    def total_system_money(self):
        return (self.financial_system.system_money == sum(self.wallets)+self.bank_money)

    def run_test_system(self, n):
        self.test_system.run(n)

    def run_all_tests(self, n=1):
        assert np.array([self.total_system_money() for _ in range(n)]).all()
        #pairs are full
        assert np.array([len(self.financial_system.pairs) == 
                         choose(len(self.financial_system.agents), 2) 
                         for _ in range(n)]).all()
        #neighbourlists are full
        assert np.array([[len(self.financial_system.neighbourlist[agent]) == 
                        (len(self.financial_system.agents) - 1) 
                        for agent in self.financial_system.agents]
                        for _ in range(n)]).all()

m = tests(5)
m.run_test_system(5)
