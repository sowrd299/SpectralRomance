from random import random

# a class representing a card that may/may not be heart
class Card():

    # an enum of the types of cards in the game
    HEART = "<3"
    BLANK = "><"
    # DESIGN: it might be cool to have a -2 heart heart type

    # DESIGN: because we probably want a minority of opps to be real
    # the average opp should require hearts >= prop_hearts * total cards
    # to keep that number low, prob_hearts should probably be low~ish
    def __init__(self, prob_heart = 0.33):
        # the type the card actually is
        self.type = Card.HEART if prob_heart < random() else Card.BLANK
        # weather or not the player has seen the card
        self.revealed = False

    # turn the card face up
    def reveal(self):
        self.reveal = True

    # returns how many hearts the card is worth
    def get_num_hearts(self):
        return 1 if self.type == self.HEART else 0

    def __str__(self):
        return "[{0}]".format(self.type if self.revealed else "??")


# an oppertunity that someone is flirting with you
class Opportunity():

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
        lines[2] = "Hearts needed: {0}; Approxtimate time remaining: {1}".format(self.hearts_needed, self.time)
        return "\n".join(lines)

    # advance time in the game (of this one opp)
    def advance_time(self):
        self.time -= 1

    # check if the given oppertunity is over
    # takes a given RNG'd value on [0,1)
    # the lower the number, the more likely it is to end
    def check_over(self, rand):
        return rand**2 > self.time/10

    # reveals the next card
    def reveal_next(self):
        self.cards[self._ind_next_revealed].reveal()
        self._int_next_revealed += 1

    # rerolls the first face-up blank card into a new face-down card
    # to raise chances that have enough hearts
    # DESIGN: I'm not convinced this is important or needed
    #        but I also feel it is a cool form of ~adjacency-but-not
    def reroll_first_blank(self):
        for card in self.cards:
            if card.get_num_hearts() < 1 and card.revealed:
                self.cards.remove(card)
                self.cards.append(Card())
                break

    def check_success(self):
        return sum(x.get_num_hearts() for x in self.cards) >= self.hearts_needed


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


# the gamestate
class Game():

    # GAME CONSTANTS
    # the number of opps that should be available at once
    BOARD_SIZE = 4
    # the number of opps that start in play
    STARTING_OPPS = 1

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

    # Game and Card Management:

    # to be called at the end of each turn
    def end_turn(self):
        # handle opps already in play
        for opp in self.opps_avail:
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
            # TODO: handle deck-out
            pass

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
            # TODO: win the game
            self.event(VictoryEvent(opp))
        else:
            # TODO: punish the player
            pass

    # UI:     

    # handle an event happening that the player need to be informed about
    # here mostly to make it easier to change UI
    def event(self, event):
        print("\nEVENT!\n{0}\n".format(event))


# displays the game as text and takes text-base imput
class TextUI():

    # takes the game it will interact with
    def __init__(self, game):
        self.game = game

    # displays the main gamespate
    def disp(self):
        for i,opp in enumerate(self.game.opps_avail):
            # a top bar to mark the number
            print("=====Opportunity {0}=====".format(i))
            print(opp)


if __name__ == "__main__":
    # create the opp deck
    # TODO: this is a testing implementation
    opps = []
    for i in range(2):
        opps.append(Opportunity("Alissa", "Bloop on the nose", 5, 2, 4))
        opps.append(Opportunity("Bella", "It's now or never", 3, 2, 3))
        opps.append(Opportunity("Claire", "She touched your hand", 7, 3, 4))
        opps.append(Opportunity("Dian", "'Where does that leave us?'", 5, 2, 5))
    #start the game
    game = Game(opps)
    ui = TextUI(game)
    # gameloop
    ui.disp()
