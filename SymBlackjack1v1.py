import random
import matplotlib.pyplot as plt


# ==========================================
# 1. STRUKTURY DANYCH I KLASA AGENTA
# ==========================================

class Card:
    __slots__ = ['rank', 'value']

    def __init__(self, rank):
        self.rank = str(rank).upper()
        if self.rank in ['J', 'Q', 'K', '10']:
            self.value = 10
            self.rank = '10'
        elif self.rank in ['A', '1']:
            self.value = 11
            self.rank = 'A'
        else:
            self.value = int(self.rank)


class Deck:
    def __init__(self, num_decks=8):
        self.num_decks = num_decks
        self.cards = []
        self.reset()

    def reset(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = [Card(r) for _ in range(self.num_decks * 4) for r in ranks]
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def needs_reshuffle(self, penetration=0.75):
        cards_played = (self.num_decks * 52) - len(self.cards)
        return cards_played >= (self.num_decks * 52 * penetration)


class Hand:
    def __init__(self, bet=0.0):
        self.cards = []
        self.bet = bet

    def add_card(self, card):
        self.cards.append(card)

    def get_value(self):
        val = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == 'A')
        while val > 21 and aces > 0:
            val -= 10
            aces -= 1
        return val

    def is_pair(self):
        return len(self.cards) == 2 and self.cards[0].value == self.cards[1].value

    def split_hand(self):
        new_h = Hand(bet=self.bet)
        new_h.add_card(self.cards.pop())
        return new_h


class BlackjackAgent:
    def __init__(self, num_decks=8):
        self.num_decks = num_decks
        self.running_count = 0
        self.cards_dealt = 0
        self.total_cards = num_decks * 52

    def reset_shoe(self):
        self.running_count = 0
        self.cards_dealt = 0

    def register_card(self, card_rank):
        c = Card(card_rank)
        self.cards_dealt += 1
        if c.rank in ['2', '3', '4', '5', '6']:
            self.running_count += 1
        elif c.rank in ['10', 'A']:
            self.running_count -= 1

    def get_true_count(self):
        cards_left = max(self.total_cards - self.cards_dealt, 26)
        decks_left = cards_left / 52.0
        return self.running_count / decks_left

    def get_recommended_bet(self, bankroll, min_bet, max_bet, kelly_fraction=0.5):
        tc = self.get_true_count()
        if tc <= 1.0:
            return min_bet

        edge = (tc - 1.0) * 0.0048
        raw_bet = bankroll * edge * kelly_fraction
        final_bet = max(min_bet, min(round(raw_bet, 0), max_bet))
        return float(final_bet)

    def get_insurance_recommendation(self, dealer_up_card_rank):
        if Card(dealer_up_card_rank).rank != 'A':
            return False
        return self.get_true_count() >= 3.0

    def check_illustrious_18(self, score, dealer_val, tc, is_soft, can_double):
        if is_soft:
            return None
        if score == 16 and dealer_val == 10: return "STOJ (STAND)" if tc >= 0.0 else "DOBIERAJ (HIT)"
        if score == 15 and dealer_val == 10: return "STOJ (STAND)" if tc >= 4.0 else "DOBIERAJ (HIT)"
        if score == 10 and dealer_val == 10: return "PODWOJ (DOUBLE)" if (tc >= 4.0 and can_double) else None
        if score == 12 and dealer_val == 3: return "STOJ (STAND)" if tc >= 2.0 else "DOBIERAJ (HIT)"
        if score == 12 and dealer_val == 2: return "STOJ (STAND)" if tc >= 3.0 else "DOBIERAJ (HIT)"
        if score == 11 and dealer_val == 11: return "PODWOJ (DOUBLE)" if (tc >= 1.0 and can_double) else None
        if score == 9 and dealer_val == 2: return "PODWOJ (DOUBLE)" if (tc >= 1.0 and can_double) else None
        return None

    def get_best_action(self, player_cards, dealer_up_card_rank, can_double=True, can_split=True):
        tc = self.get_true_count()
        dealer_val = Card(dealer_up_card_rank).value
        cards = [Card(r) for r in player_cards]

        score = sum(c.value for c in cards)
        aces = sum(1 for c in cards if c.rank == 'A')
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1

        is_soft = (aces > 0 and len(cards) == 2)
        is_pair = (len(cards) == 2 and (cards[0].value == cards[1].value))

        if can_split and is_pair:
            p_val = cards[0].value
            if p_val in [11, 8]: return "ROZDIEL (SPLIT)"
            if p_val == 10 and dealer_val == 5 and tc >= 5.0: return "ROZDIEL (SPLIT)"
            if p_val == 10 and dealer_val == 6 and tc >= 4.0: return "ROZDIEL (SPLIT)"
            if p_val in [2, 3] and dealer_val in [2, 3, 4, 5, 6, 7]: return "ROZDIEL (SPLIT)"
            if p_val == 4 and dealer_val in [5, 6]: return "ROZDIEL (SPLIT)"
            if p_val == 6 and dealer_val in [2, 3, 4, 5, 6]: return "ROZDIEL (SPLIT)"
            if p_val == 7 and dealer_val in [2, 3, 4, 5, 6, 7]: return "ROZDIEL (SPLIT)"
            if p_val == 9 and dealer_val in [2, 3, 4, 5, 6, 8, 9]: return "ROZDIEL (SPLIT)"

        dev = self.check_illustrious_18(score, dealer_val, tc, is_soft, can_double)
        if dev is not None:
            return dev

        if is_soft:
            if score >= 19: return "STOJ (STAND)"
            if score == 18:
                if dealer_val in [2, 3, 4, 5, 6] and can_double: return "PODWOJ (DOUBLE)"
                return "STOJ (STAND)" if dealer_val in [7, 8] else "DOBIERAJ (HIT)"
            if score <= 17:
                return "PODWOJ (DOUBLE)" if (dealer_val in [5, 6] and can_double) else "DOBIERAJ (HIT)"
        else:
            if score >= 17: return "STOJ (STAND)"
            if score in [13, 14, 15, 16]: return "STOJ (STAND)" if dealer_val in [2, 3, 4, 5, 6] else "DOBIERAJ (HIT)"
            if score == 12: return "STOJ (STAND)" if dealer_val in [4, 5, 6] else "DOBIERAJ (HIT)"
            if score == 11: return "PODWOJ (DOUBLE)" if can_double else "DOBIERAJ (HIT)"
            if score == 10: return "PODWOJ (DOUBLE)" if (dealer_val <= 9 and can_double) else "DOBIERAJ (HIT)"
            if score == 9: return "PODWOJ (DOUBLE)" if (dealer_val in [3, 4, 5, 6] and can_double) else "DOBIERAJ (HIT)"
            return "DOBIERAJ (HIT)"


# ==========================================
# 2. SILNIK SYMULACJI POJEDYNCZEJ SESJI (1v1)
# ==========================================

def run_single_game(initial_bankroll, rounds, min_bet=10.0, max_bet=500.0):
    deck = Deck(num_decks=8)
    agent = BlackjackAgent(num_decks=8)

    bankroll = initial_bankroll
    history = [bankroll]

    for round_num in range(rounds):
        if bankroll < min_bet:
            break

        if deck.needs_reshuffle():
            deck.reset()
            agent.reset_shoe()

        # Pobranie stawki od Agenta
        bet = agent.get_recommended_bet(bankroll, min_bet, max_bet)
        bet = min(bet, bankroll)

        # Rozdanie kart: Gracz, Krupier, Gracz, Krupier
        p_card1, d_card1 = deck.draw(), deck.draw()
        p_card2, d_card2 = deck.draw(), deck.draw()

        agent.register_card(p_card1.rank)
        agent.register_card(d_card1.rank)
        agent.register_card(p_card2.rank)

        player_hand = Hand(bet=bet)
        player_hand.add_card(p_card1)
        player_hand.add_card(p_card2)

        dealer_hand = Hand()
        dealer_hand.add_card(d_card1)
        dealer_hand.add_card(d_card2)

        bankroll -= bet

        # Ubezpieczenie
        insurance_bet = 0.0
        if d_card1.rank == 'A':
            take_ins = agent.get_insurance_recommendation(d_card1.rank)
            if take_ins and bankroll >= (bet * 0.5):
                insurance_bet = bet * 0.5
                bankroll -= insurance_bet

        # Sprawdzenie Blackjacków
        player_bj = (player_hand.get_value() == 21 and len(player_hand.cards) == 2)
        dealer_bj = (dealer_hand.get_value() == 21 and len(dealer_hand.cards) == 2)

        if dealer_bj:
            agent.register_card(d_card2.rank)
            if insurance_bet > 0:
                bankroll += insurance_bet * 3.0
            if player_bj:
                bankroll += bet
            history.append(bankroll)
            continue

        if player_bj:
            agent.register_card(d_card2.rank)
            bankroll += bet * 2.5
            history.append(bankroll)
            continue

        # Rozgrywka Gracza
        player_hands = [player_hand]
        h_idx = 0
        all_busted = True

        while h_idx < len(player_hands):
            cur_h = player_hands[h_idx]
            while cur_h.get_value() < 21:
                p_ranks = [c.rank for c in cur_h.cards]
                can_dbl = (bankroll >= cur_h.bet) and (len(cur_h.cards) == 2)
                can_spl = (bankroll >= cur_h.bet) and cur_h.is_pair() and (len(cur_h.cards) == 2)

                action = agent.get_best_action(p_ranks, d_card1.rank, can_double=can_dbl, can_split=can_spl)

                if action == "ROZDIEL (SPLIT)":
                    bankroll -= cur_h.bet
                    new_h = cur_h.split_hand()

                    c_ex1 = deck.draw()
                    cur_h.add_card(c_ex1)
                    agent.register_card(c_ex1.rank)

                    c_ex2 = deck.draw()
                    new_h.add_card(c_ex2)
                    agent.register_card(c_ex2.rank)

                    player_hands.insert(h_idx + 1, new_h)

                elif action == "PODWOJ (DOUBLE)":
                    bankroll -= cur_h.bet
                    cur_h.bet *= 2
                    c_drawn = deck.draw()
                    cur_h.add_card(c_drawn)
                    agent.register_card(c_drawn.rank)
                    break

                elif action == "DOBIERAJ (HIT)":
                    c_drawn = deck.draw()
                    cur_h.add_card(c_drawn)
                    agent.register_card(c_drawn.rank)

                elif action == "STOJ (STAND)":
                    break

            if cur_h.get_value() <= 21:
                all_busted = False
            h_idx += 1

        # Tura Krupiera
        agent.register_card(d_card2.rank)
        if not all_busted:
            while dealer_hand.get_value() < 17:
                c_drawn = deck.draw()
                dealer_hand.add_card(c_drawn)
                agent.register_card(c_drawn.rank)

        # Rozliczenie
        d_score = dealer_hand.get_value()
        for h in player_hands:
            p_score = h.get_value()
            if p_score <= 21:
                if d_score > 21 or p_score > d_score:
                    bankroll += h.bet * 2.0
                elif p_score == d_score:
                    bankroll += h.bet

        history.append(bankroll)

    return history


# ==========================================
# 3. INTERFEJS I SYMULACJA MONTE CARLO
# ==========================================

def main():
    print("\n" + "=" * 60)
    print("   MONTE CARLO BLACKJACK SIMULATOR (1v1: GRACZ VS KRUPIER)")
    print("=" * 60)

    try:
        initial_bankroll = float(input(" [>] Podaj kapitał początkowy (np. 10000): "))
        rounds = int(input(" [>] Podaj liczbę rund na 1 grę (np. 1000): "))
        num_games = int(input(" [>] Podaj liczbę powtórzeń/gier (np. 100): "))
    except ValueError:
        print(" Error: Wprowadzono niepoprawne dane cyfrowe. Uruchamiam z domyślnymi.")
        initial_bankroll, rounds, num_games = 10000.0, 1000, 100

    print(f"\n Uruchamianie symulacji {num_games} gier po {rounds} rund...")

    all_games_histories = []
    final_bankrolls = []

    for g in range(num_games):
        history = run_single_game(initial_bankroll, rounds)
        all_games_histories.append(history)
        final_bankrolls.append(history[-1])

    # Statystyki
    ruin_count = sum(1 for res in final_bankrolls if res <= 10.0)
    avg_final = sum(final_bankrolls) / len(final_bankrolls)
    max_final = max(final_bankrolls)
    min_final = min(final_bankrolls)
    avg_roi = ((avg_final - initial_bankroll) / initial_bankroll) * 100

    print("\n" + "=" * 60)
    print("               PODSUMOWANIE STATYSTYCZNE")
    print("=" * 60)
    print(f" Liczba symulowanych gier:   {num_games}")
    print(f" Liczba rund w każdej grze:  {rounds}")
    print(f" Kapitał startowy:           {initial_bankroll:.2f} PLN")
    print("-" * 60)
    print(f" Średni kapitał końcowy:    {avg_final:.2f} PLN")
    print(f" Średnia stopa zwrotu (ROI): {avg_roi:+.2f}%")
    print(f" Najwyższy wynik w serii:    {max_final:.2f} PLN")
    print(f" Najniższy wynik w serii:    {min_final:.2f} PLN")
    print(f" Ryzyko bankructwa (Ruin):   {(ruin_count / num_games) * 100:.2f}%")
    print("=" * 60 + "\n")

    # Wykresy
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Wykres 1: Trajektorie pierwszych 10 gier
    for i in range(min(10, num_games)):
        ax1.plot(all_games_histories[i], alpha=0.7, label=f'Gra #{i + 1}')
    ax1.axhline(y=initial_bankroll, color='r', linestyle='--', label='Start')
    ax1.set_title("Przebieg kapitału (Próbka pierwszych 10 gier)")
    ax1.set_xlabel("Rundy")
    ax1.set_ylabel("Kapitał (PLN)")
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', fontsize='small')

    # Wykres 2: Rozkład końcowych sald ze wszystkich gier
    ax2.hist(final_bankrolls, bins=15, color='#2ca02c', edgecolor='black', alpha=0.7)
    ax2.axvline(x=initial_bankroll, color='r', linestyle='--', label='Start')
    ax2.axvline(x=avg_final, color='b', linestyle='-', label=f'Średnia: {avg_final:.0f}')
    ax2.set_title(f"Rozkład wyników z {num_games} gier (Monte Carlo)")
    ax2.set_xlabel("Końcowy kapitał (PLN)")
    ax2.set_ylabel("Częstość (Liczba gier)")
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()