import sys


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


class BlackjackAgent:
    def __init__(self, bankroll=100.0, num_decks=8, min_bet=2.0, max_bet=5000.0, kelly_fraction=0.5):
        self.initial_bankroll = bankroll
        self.bankroll = bankroll
        self.num_decks = num_decks
        self.min_bet = min_bet
        self.max_bet = max_bet
        self.kelly_fraction = kelly_fraction

        self.running_count = 0
        self.cards_dealt = 0
        self.total_cards = num_decks * 52

    def reset_shoe(self):
        """Wywoływane po przetasowaniu buta (Reshuffle)."""
        self.running_count = 0
        self.cards_dealt = 0
        print("\n" + "=" * 50)
        print(" [!] BUT ZOSTAL PRZETASOWANY. COUNT ZRESETOWANY DO 0.")
        print("=" * 50 + "\n")

    def register_card(self, card_rank):
        """Rejestruje dowolną kartę i aktualizuje Hi-Lo."""
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

    def get_recommended_bet(self):
        """Oblicza stawkę Kelly przed nowym rozdaniem."""
        tc = self.get_true_count()
        if tc <= 1.0:
            return self.min_bet

        edge = (tc - 1.0) * 0.0048  # Estymacja przewagi dla 8 talii S17
        raw_bet = self.bankroll * edge * self.kelly_fraction
        final_bet = max(self.min_bet, min(round(raw_bet, 0), self.max_bet))
        return float(final_bet)

    def get_insurance_recommendation(self, dealer_up_card_rank):
        if Card(dealer_up_card_rank).rank != 'A':
            return None

        tc = self.get_true_count()
        if tc >= 3.0:
            return "TAK (TAKE INSURANCE) - TC >= +3.0"
        else:
            return "NIE (DECLINE INSURANCE) - TC < +3.0"

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

        # 1. Rozdzielanie par (Split)
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

        # 2. Odchylenia Illustrious 18
        dev = self.check_illustrious_18(score, dealer_val, tc, is_soft, can_double)
        if dev is not None:
            return dev

        # 3. Strategia Podstawowa
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


def calculate_hand_score(player_cards):
    """Zwraca łączną wartość punktową kart gracza."""
    cards = [Card(r) for r in player_cards]
    val = sum(c.value for c in cards)
    aces = sum(1 for c in cards if c.rank == 'A')
    while val > 21 and aces > 0:
        val -= 10
        aces -= 1
    return val


def is_natural_blackjack(player_cards):
    """Sprawdza, czy układ dwóch kart to naturalny Blackjack (21 pkt)."""
    if len(player_cards) == 2:
        return calculate_hand_score(player_cards) == 21
    return False


def parse_card_input(prompt_text):
    valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '1']
    while True:
        val = input(prompt_text).strip().upper()
        if val in ['R', 'RESET']:
            return 'RESET'
        if val in valid_ranks:
            return '10' if val in ['J', 'Q', 'K'] else ('A' if val == '1' else val)
        print("  [!] Nieprawidłowa karta. Użyj: 2-10, J, Q, K, A (lub 'R' aby zresetować but).")


def get_user_action_choice(suggested_action, allow_split=True):
    """Pozwala graczowi zaakceptować sugerowany ruch (ENTER) lub wybrać własny."""
    mapping = {
        "H": "DOBIERAJ (HIT)",
        "S": "STOJ (STAND)",
        "D": "PODWOJ (DOUBLE)",
        "P": "ROZDIEL (SPLIT)"
    }
    while True:
        prompt = f" [>] Wybierz ruch [ENTER = Sugerowany ({suggested_action}), H=Hit, S=Stand, D=Double"
        if allow_split:
            prompt += ", P=Split]: "
        else:
            prompt += "]: "

        user_in = input(prompt).strip().upper()
        if not user_in:
            return suggested_action
        if user_in in mapping:
            if user_in == "P" and not allow_split:
                print("  [!] Nie możesz powtórnie rozdzielić tej ręki.")
                continue
            return mapping[user_in]
        print("  [!] Nieprawidłowy wybór. Wpisz H, S, D, P lub wciśnij ENTER.")


def play_single_hand(hand_label, hand_cards, dealer_card, agent, can_split=True):
    """Obsługuje cykl decyzyjny dla pojedynczej ręki z obsługą ponownego spiltu."""
    print(f"\n--- {hand_label.upper()} (Pierwsza karta: {hand_cards[0]}) ---")

    if len(hand_cards) == 1:
        c2 = parse_card_input(f" [>] Podaj DRUGĄ kartę dla {hand_label}: ")
        if c2 == 'RESET':
            return 'RESET', hand_cards
        agent.register_card(c2)
        hand_cards.append(c2)

    if hand_cards[0] == 'A' and len(hand_cards) == 2 and not can_split:
        print(f" [I] Rozdzielone Asy otrzymują tylko po 1 karcie. Wynik: {calculate_hand_score(hand_cards)} pkt.")
        return 'OK', hand_cards

    if is_natural_blackjack(hand_cards) and can_split:
        print(f"\n [★] BLACKJACK! {hand_label} ma 21 pkt ({hand_cards}). Koniec tej ręki.")
        return 'OK', hand_cards

    while True:
        score = calculate_hand_score(hand_cards)

        if score == 21:
            print(f" [★] 21 PKT! {hand_label} ma 21 pkt ({hand_cards}). Koniec tej ręki.")
            break
        elif score > 21:
            print(f" [!] FURA! {hand_label} ma {score} pkt ({hand_cards}). Koniec tej ręki.")
            break

        can_dbl = (len(hand_cards) == 2)
        can_spl = (can_split and len(hand_cards) == 2 and Card(hand_cards[0]).value == Card(hand_cards[1]).value)

        suggested_action = agent.get_best_action(hand_cards, dealer_card, can_double=can_dbl, can_split=can_spl)

        print(
            f"\n >>> SUGEROWANY RUCH [{hand_label}]: {suggested_action} <<< (Karty: {hand_cards}, Wynik: {score} pkt)")

        chosen_action = get_user_action_choice(suggested_action, allow_split=can_spl)

        if chosen_action == "ROZDIEL (SPLIT)":
            return 'SPLIT', hand_cards

        if chosen_action in ["STOJ (STAND)", "PODWOJ (DOUBLE)"]:
            if chosen_action == "PODWOJ (DOUBLE)":
                extra_c = parse_card_input(f" [>] Podaj dociągniętą kartę po podwojeniu dla {hand_label}: ")
                if extra_c == 'RESET':
                    return 'RESET', hand_cards
                agent.register_card(extra_c)
                hand_cards.append(extra_c)
                final_score = calculate_hand_score(hand_cards)
                print(f" [I] Końcowy wynik dla {hand_label}: {final_score} pkt.")
            break

        elif chosen_action == "DOBIERAJ (HIT)":
            extra_c = parse_card_input(f" [>] Podaj dociągniętą kartę dla {hand_label}: ")
            if extra_c == 'RESET':
                return 'RESET', hand_cards
            agent.register_card(extra_c)
            hand_cards.append(extra_c)

    return 'OK', hand_cards


def process_player_hands(initial_cards, dealer_card, agent, max_hands=4):
    """Zarządza dynamiczną listą rąk gracza przy ponownych splitach (Resplit)."""
    hands = [initial_cards]
    completed_count = 0

    while completed_count < len(hands):
        current_hand_index = completed_count
        hand_label = f"Ręka {current_hand_index + 1}/{len(hands)}"
        can_split = (len(hands) < max_hands)

        status, updated_hand = play_single_hand(
            hand_label,
            hands[current_hand_index],
            dealer_card,
            agent,
            can_split=can_split
        )

        if status == 'RESET':
            return 'RESET'

        if status == 'SPLIT':
            print("\n" + "=" * 50)
            print(f" [!] NASTĄPIŁO ROZDZIELENIE KART W {hand_label.upper()}!")
            print("=" * 50)

            card1, card2 = updated_hand[0], updated_hand[1]
            hands[current_hand_index] = [card1]
            hands.insert(current_hand_index + 1, [card2])
            continue

        completed_count += 1

    return 'OK'


def main():
    print("\n" + "=" * 60)
    print("      BLACKJACK REAL-TIME ADVISOR AGENT (8 DECKS, S17)")
    print("=" * 60)

    try:
        init_bankroll = float(input(" [>] Podaj Twój początkowy kapitał (domyślnie 100): ") or 100)
        min_bet = float(input(" [>] Podaj minimalną stawkę stołu (domyślnie 2): ") or 2)
        max_bet = float(input(" [>] Podaj maksymalną stawkę stołu (domyślnie 5000): ") or 5000)
    except ValueError:
        print("  [!] Błąd danych. Uruchamiam z wartościami domyślnymi.")
        init_bankroll, min_bet, max_bet = 100.0, 2.0, 5000.0

    agent = BlackjackAgent(
        bankroll=init_bankroll,
        min_bet=min_bet,
        max_bet=max_bet,
        kelly_fraction=0.5
    )

    print("\n Instrukcja wprowadzania kart:")
    print(" - Karty wpisuj jako: 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A")
    print(" - Wpisz 'R' w dowolnym momencie, gdy nastąpi przetasowanie kart.")
    print("=" * 60 + "\n")

    round_num = 1

    while True:
        tc = agent.get_true_count()
        rec_bet = agent.get_recommended_bet()

        print(f"\n--- ROZDANIE #{round_num} ---")
        print(f" STAN STOŁU  | RC (Running Count): {agent.running_count:+d} | TC (True Count): {tc:+.2f}")
        print(f" PROPOZYCJA  | SUGEROWANA STAWKA: >>> {rec_bet:.0f} PLN <<<")
        print("-" * 40)

        c1 = parse_card_input(" [>] 1. Podaj Twoją PIERWSZĄ kartę: ")
        if c1 == 'RESET':
            agent.reset_shoe()
            continue
        agent.register_card(c1)

        dealer_card = parse_card_input(" [>] 2. Podaj odkrytą kartę KRUPIERA: ")
        if dealer_card == 'RESET':
            agent.reset_shoe()
            continue
        agent.register_card(dealer_card)

        insurance_rec = agent.get_insurance_recommendation(dealer_card)
        if insurance_rec:
            print(f"\n [!] KRUPIER POKAZUJE ASA!")
            print(f" >>> REKOMENDACJA UBEZPIECZENIA (INSURANCE): {insurance_rec} <<<\n")

        c2 = parse_card_input(" [>] 3. Podaj Twoją DRUGĄ kartę: ")
        if c2 == 'RESET':
            agent.reset_shoe()
            continue
        agent.register_card(c2)

        player_cards = [c1, c2]

        if is_natural_blackjack(player_cards):
            print("\n" + "=" * 50)
            print(f" [★] BLACKJACK! Masz 21 pkt ({player_cards}). Rozdanie zakończone automatycznie.")
            print("=" * 50)
        else:
            res = process_player_hands(player_cards, dealer_card, agent, max_hands=4)
            if res == 'RESET':
                agent.reset_shoe()
                continue

        print("\n [opcjonalnie] Wpisz pozostałe widoczne karty (krupiera/graczy) po zakończeniu rozdania.")
        others = input(" [>] Wpisz karty rozdzielone spacją (np. '10 7 K 2') lub naciśnij ENTER: ").strip().upper()
        if others == 'R':
            agent.reset_shoe()
            continue
        elif others:
            for rank in others.split():
                if rank in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']:
                    agent.register_card(rank)

        round_num += 1


if __name__ == "__main__":
    main()