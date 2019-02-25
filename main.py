from random import random

# a class representing a card that may/may not be heart
class Card():

    # the constant probability that a card is a heart
    PROB_HEART = 0.4

    # an enum of the types of cards in the game
    HEART = "<3"
    BLANK = "><"
    # DESIGN: it might be cool to have a -2 heart heart type

    # DESIGN: because we probably want a minority of opps to be real
    # the average opp should require hearts >= prop_hearts * total cards
    # to keep that number low, prob_hearts should probably be low~ish
    def __init__(self, prob_heart = None):
        prob_heart = prob_heart if prob_heart != None else self.PROB_HEART
        # the type the card actually is
        self.type = Card.HEART if prob_heart > random() else Card.BLANK
        # weather or not the player has seen the card
        self.revealed = False

    # turn the card face up
    def reveal(self):
        self.revealed = True

    # returns how many hearts the card is worth
    def get_num_hearts(self):
        return 1 if self.type == self.HEART else 0

    def __str__(self):
        return "[{0}]".format(self.type if self.revealed else "??")


# an oppertunity that someone is flirting with you
class Opportunity():

    # constants used in the punishment level equasion
    MAX_TURNS = 10
    TURNS_DIV = 3

    # takes how long the card will be around for
    # how many hearts it needs to be an oppertunity
    # how many cards are on it that may be hears
    def __init__(self, name, text, time, hearts, cards):
        self.name = name
        self.text = text
        self.time = time 
        self.hearts_needed = hearts
        self.cards = [Card() for i in range(cards)]
        self._ind_next_revealed = 0 # the index of the next card to reveal
        # DESIGN: we could introduce a conception of consistent characters
        #       and have past interactions carry into future opps with them
    
    def __str__(self):
        lines = [None, None, None]
        lines[0] = "Name: {0}; {1}".format(self.name.upper(), self.text)
        lines[1] = "Cards: "+" ".join(str(c) for c in self.cards)
        lines[2] = "Hearts needed: {0}; Approxtimate time remaining: {1} turns".format(self.hearts_needed, self.time-2)
        return "\n".join(lines)

    # advance time in the game (of this one opp)
    def advance_time(self):
        self.time -= 1

    # check if the given oppertunity is over
    # takes a given RNG'd value on [0,1)
    # the lower the number, the more likely it is to end
    def check_over(self, rand):
        return rand**3 > self.time/10

    # reveals the next card
    def reveal_next(self):
        self.cards[self._ind_next_revealed].reveal()
        self._ind_next_revealed += 1

    # rerolls the first face-up blank card into a new face-down card
    # to raise chances that have enough hearts
    # DESIGN: I'm not convinced this is important or needed
    #        but I also feel it is a cool form of ~adjacency-but-not
    def reroll_first_blank(self):
        for card in self.cards:
            if card.get_num_hearts() < 1 and card.revealed:
                self.cards.remove(card)
                self.cards.append(Card())
                self._ind_next_revealed -= 1
                break

    def get_revealed_hearts(self):
        return sum(card.get_num_hearts() for card in self.cards if card.revealed)

    # returns wether or not this person will say yes if you ask them out
    # takes whether or not to ignore the "need a face up card" rule
    def check_success(self, ignore_facing = False):
        # DESIGN: add in revealed heart req to nerf spamming
        return sum(x.get_num_hearts() for x in self.cards) >= self.hearts_needed and (self.get_revealed_hearts() > 0 or ignore_facing)

    # returns degree of punishment should be inflicted for asking out incorrectly
    def  get_punishment_level(self):
        return (self.MAX_TURNS-self.time)/self.TURNS_DIV + self._ind_next_revealed

    # lose so many cards from its state, lowering odds of getting a date
    def remove_cards(self, i):
        self.cards = self.cards[:-i]


# IMPLEMENTS INTERFACE EVENT
# represents the occurance that an opp has ended
# exists to inform the UI of such
class OppertunityOverEvent():

    def __init__(self, opp):
        self.opp = opp

    def __str__(self):
        return "{0} has left.".format(self.opp.name)


# IMPLEMENTS INTERFACE EVENT
# respresents the occurance that the player won the game
class VictoryEvent():

    # takes the opportunity you successfully took to win the game
    def __init__(self, opp):
        self.opp = opp

    def __str__(self):
        return "{0} said yes! You have a date! You win!".format(self.opp.name)

# IMPLEMENTS INTERFACE EVENT
# represent the occurance that the player was rejected when asking someone out
class RejectionEvent():

    def __init__(self, opp):
        self.opp = opp

    def __str__(self):
        text = "{0} said no :( Your reputation has gone down :(".format(self.opp.name)
        if opp.get_revealed_hearts() < 1: 
            text += "\nMaybe ask out someone you know has a heart for you next time."
        return text

# the gamestate
class Game():

    # GAME CONSTANTS
    # the number of opps that should be available at once
    BOARD_SIZE = 3
    # the number of opps that start in play
    STARTING_OPPS = 1
    # constants that govern the punishment equasion
    MIN_PUNISHMENT = 1
    PUNISHMENT_DIV = 2

    # takes the deck of oppertunities for the game
    def __init__(self, deck):
        # all oppertunities the player may run into
        # TODO: shuffle
        self.opps_deck = deck
        # the opps that the player may currently interact with
        self.opps_avail = []
        # populate starting opps
        for i in range(self.STARTING_OPPS):
            self.draw_opp()
        # whether or not the game is still going
        self.ongoing = True

    # Game and Card Management:

    # to be called at the end of each turn
    def end_turn(self):
        # handle opps already in play
        old_opps_avail = list(self.opps_avail)
        for opp in old_opps_avail:
            # do this instead of a normal for-loop to avoid tracking over new replacement opps
            opp.advance_time()
            # handle oppertunities ending
            if(opp.check_over(random())):
                self.replace_opp(opp)
                self.event(OppertunityOverEvent(opp))
        # handle slowly adding in opps
        # DESIGN: I want this mechanic to make the start of the game a bit slower
        if len(self.opps_avail) < self.BOARD_SIZE:
            self.draw_opp()
    
    # to be called after an opp is over, and should be replaced
    def replace_opp(self, opp):
        self.opps_avail.remove(opp)
        self.draw_opp()

    # put an opp into play
    def draw_opp(self):
        if len(self.opps_deck) > 0:
            self.opps_avail.append(self.opps_deck.pop())
        else:
            # TODO: testing implementation for handling deck-out
            self.event("You are out of time. Everyone has a date already. Game over.")
            self.ongoing = False

    # Game Actions:
    # use these instead of the opportunity versions directly
    # to allow us to add side-effects, costs, etc., more easily

    def reveal(self, opp):
        opp.reveal_next()

    def reroll(self, opp):
        opp.reroll_first_blank()

    # may resault in the player winning
    def ask_out(self, opp):
        if opp.check_success():
            # handle victory
            self.event(VictoryEvent(opp))
            self.ongoing = False
        else:
            # handle punishment
            self.event(RejectionEvent(opp))
            punishment_level = self.MIN_PUNISHMENT + int(opp.get_punishment_level()/self.PUNISHMENT_DIV)
            for opp in self.opps_avail:
                opp.remove_cards(punishment_level)

    # UI:     

    # handle an event happening that the player need to be informed about
    # here mostly to make it easier to change UI
    def event(self, event):
        # TODO: this should get tied into/handled by the UI class
        print("\nEVENT!\n{0}\n".format(event))


# displays the game as text and takes text-base imput
class TextUI():

    # INPUT STRINGS FOR GAME ACTIONS
    # lowercase for easy processing
    REVEAL = "talk to"
    REROLL = "joke with"
    ASK = "ask out"
    # TODO: add in reminder text for what these actions do

    # takes the game it will interact with
    def __init__(self, game):
        self.game = game
        # setup actions the player can take
        # implemented as call-backs
        self.player_actions = { self.REVEAL : game.reveal, self.REROLL : game.reroll, self.ASK : game.ask_out }

    # displays the main gamespate
    def disp(self):
        for i,opp in enumerate(self.game.opps_avail):
            # a top bar to mark the number
            top_bar = "=====Opportunity {0}=====".format(i)
            print(top_bar)
            print(opp)
            print("="*len(top_bar))

    # gets the action the player wants to take
    def get_player_action(self):
        # repeat until successfull and return
        while True:
            # get input
            print("\n[ {0} ]...".format(" | ".join(self.player_actions.keys())))
            print("...[ {0} ]".format(" | ".join(o.name for o in self.game.opps_avail)))
            action_str = input("Type your action: ").lower()
            # parse action
            action = None
            for a in self.player_actions.keys():
                # if prefixed by the action
                if action_str[:len(a)] == a.lower():
                    action = self.player_actions[a]
                    break
            # if we did not sucessfully parse to an action
            else:
                print("That action does not exist.".upper())
                continue
            # parse opp 
            opp = None
            for o in self.game.opps_avail:
                # if suffixed by the name
                if action_str[-len(o.name):] == o.name.lower():
                    opp = o
                    break
            # if failed to parse opp
            else:
                print("That person does not exist.".upper())
                continue

            return (action, opp)



if __name__ == "__main__":
    # create the opp deck
    # TODO: this is a testing implementation
    opps = []
    for i in range(2): # duplicating because lazy
        opps.append(Opportunity("Alissa", "Bloop on the nose", 7, 3, 5))
        opps.append(Opportunity("Benny", "It's now or never", 5, 2, 3))
        opps.append(Opportunity("Claire", "She touched your hand", 9, 3, 4))
        opps.append(Opportunity("Dan", "'Where does that leave us?'", 4, 2, 4))
        opps.append(Opportunity("Elain", "'You're not annoying me'", 8, 4, 8))
        opps.append(Opportunity("Fred", "'Sing for me'", 9, 4, 6))
        opps.append(Opportunity("Gianna", "Wrote on your paper", 8, 3, 6))
    num_chances = sum(1 for opp in opps if opp.check_success(True))
    #start the game
    game = Game(opps)
    ui = TextUI(game)
    # gameloop
    while game.ongoing:
        ui.disp()
        action, opp = ui.get_player_action()
        action(opp)
        game.end_turn()
        print("\n")
    # end game statistics
    print("{0} people wanted to go on a date with you".format(num_chances))