
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 17:01:51 2026

@author: pierr
"""


from otree.api import *
import random


TEST_MODE = False


class C(BaseConstants):
    NAME_IN_URL = 'investment_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 21

    ENDOWMENT = 100
    INFO_COST = 15

    PUBLIC_SIGNAL_PRECISION = 0.60
    PRIVATE_SIGNAL_PRECISION = 0.80

    DELTA_MIN = 0.85
    DELTA_MAX = 0.90

    TOKENS_PER_EURO = 100

    # Only cases 3, 4, and 5 are now used.
    CASES = [3, 4, 5]
    ROUNDS_PER_BLOCK = 7

    # Reduced Holt-Laury payoffs.
    HL_A_HIGH = 120
    HL_A_LOW = 90
    HL_B_HIGH = 220
    HL_B_LOW = 10


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    environment = models.StringField()
    case = models.IntegerField()
    block_number = models.IntegerField()
    delta = models.FloatField()

    state = models.StringField()
    public_signal = models.StringField()
    private_signal = models.StringField(blank=True)

    belief_good = models.IntegerField(
        min=0,
        max=100,
        label="What is your estimate that the project is in the good state?"
    )

    confidence_tau = models.IntegerField(
        min=0,
        max=100,
        label="After seeing the public signal, how much do you feel that buying additional information would not help you much to make your investment decision?"
    )

    kappa = models.IntegerField(
        min=0,
        max=100,
        label="When deciding whether to buy additional information, how much will you rely on the feeling you reported above?"
    )

    belief_touched = models.IntegerField(initial=0)
    confidence_touched = models.IntegerField(initial=0)
    kappa_touched = models.IntegerField(initial=0)
    investment_touched = models.IntegerField(initial=0)

    buy_info = models.BooleanField(
        choices=[
            [True, "Yes, buy additional information for 15 tokens"],
            [False, "No, do not buy additional information"],
        ],
        label="Do you want to buy additional information?"
    )

    investment = models.IntegerField(min=0, blank=True)

    survival_periods = models.IntegerField()
    round_tokens = models.FloatField()

    holt_laury_choice_1 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_2 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_3 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_4 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_5 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_6 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_7 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_8 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_9 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)
    holt_laury_choice_10 = models.StringField(choices=[['A', 'Option A'], ['B', 'Option B']], widget=widgets.RadioSelect)

    risk_aversion_level = models.IntegerField(blank=True)

    holt_laury_paid_row = models.IntegerField(blank=True)
    holt_laury_payoff = models.FloatField(blank=True)


PAYOFFS = {
    1: {
        'F': {'H': [5.2, 1.0, 0, 0], 'L': [1.0, 0, 0, 0]},
        'B': {'H': [0, 0, 1.0, 5.2], 'L': [0, 0, 0, 1.0]},
    },
    2: {
        'F': {'H': [3.0, 2.0, 0.75, 0.25], 'L': [0.5, 0.5, 0, 0]},
        'B': {'H': [0.25, 0.75, 2.0, 3.0], 'L': [0, 0, 0.5, 0.5]},
    },
    3: {
        'F': {'H': [5.2, 1.0, 0, 0], 'L': [1.0, 0, 0, 0]},
        'B': {'H': [0, 0, 2.1, 5.7], 'L': [0, 0, 0, 1.0]},
    },
    4: {
        'F': {'H': [3.0, 2.0, 0.75, 0.25], 'L': [0.5, 0.5, 0, 0]},
        'B': {'H': [0.9, 1.4, 1.8, 2.5], 'L': [0, 0, 0.5, 0.95]},
    },
    5: {
        'F': {'H': [2.1, 1.5, 1.0, 0.5], 'L': [1.5, 1.0, 0.8, 0.5]},
        'B': {'H': [0, 0, 2.6, 6.2], 'L': [0, 0, 0.5, 1.0]},
    },
}


def get_block_number(round_number):
    return ((round_number - 1) // C.ROUNDS_PER_BLOCK) + 1


def get_payoff_stream(player: Player, state):
    return PAYOFFS[player.case][player.environment][state]


def discounted_return(player: Player, state):
    payoff_stream = get_payoff_stream(player, state)
    return sum((player.delta ** (t + 1)) * payoff_stream[t] for t in range(4))


def payoff_spread(player: Player):
    return discounted_return(player, 'H') - discounted_return(player, 'L')


def public_belief_good(player: Player):
    if player.public_signal == 'Good':
        return C.PUBLIC_SIGNAL_PRECISION
    return 1 - C.PUBLIC_SIGNAL_PRECISION


def expected_return_public(player: Player):
    belief = public_belief_good(player)
    r_h = discounted_return(player, 'H')
    r_l = discounted_return(player, 'L')
    return belief * r_h + (1 - belief) * r_l


def max_investment_allowed(player: Player):
    return C.ENDOWMENT - C.INFO_COST if player.buy_info else C.ENDOWMENT


def survival_probabilities(player: Player):
    return [
        round((player.delta ** 1) * 100),
        round((player.delta ** 2) * 100),
        round((player.delta ** 3) * 100),
        round((player.delta ** 4) * 100),
    ]


def creating_session(subsession: Subsession):
    for player in subsession.get_players():
        participant = player.participant

        if subsession.round_number == 1:
            participant.environment = random.choice(['F', 'B'])

            selected_cases = random.sample(C.CASES, 3)
            participant.case_block_1 = selected_cases[0]
            participant.case_block_2 = selected_cases[1]
            participant.case_block_3 = selected_cases[2]

            participant.paid_rounds = random.sample(
                range(1, C.NUM_ROUNDS + 1),
                3
            )

        player.environment = participant.environment

        player.block_number = get_block_number(subsession.round_number)

        if player.block_number == 1:
            player.case = participant.case_block_1
        elif player.block_number == 2:
            player.case = participant.case_block_2
        else:
            player.case = participant.case_block_3

        player.delta = round(random.uniform(C.DELTA_MIN, C.DELTA_MAX), 2)

        player.state = random.choice(['H', 'L'])

        if random.random() < C.PUBLIC_SIGNAL_PRECISION:
            player.public_signal = 'Good' if player.state == 'H' else 'Bad'
        else:
            player.public_signal = 'Bad' if player.state == 'H' else 'Good'


def generate_private_signal(player: Player):
    if random.random() < C.PRIVATE_SIGNAL_PRECISION:
        player.private_signal = 'Good' if player.state == 'H' else 'Bad'
    else:
        player.private_signal = 'Bad' if player.state == 'H' else 'Good'


def calculate_survival_periods(player: Player):
    survival = 0

    for period in range(4):
        if random.random() < player.delta:
            survival += 1
        else:
            break

    player.survival_periods = survival


def calculate_payoff(player: Player):
    info_cost = C.INFO_COST if player.buy_info else 0
    kept_tokens = C.ENDOWMENT - info_cost - player.investment

    payoff_stream = PAYOFFS[player.case][player.environment][player.state]

    investment_return = 0
    for t in range(player.survival_periods):
        investment_return += player.investment * payoff_stream[t]

    player.round_tokens = kept_tokens + investment_return
    player.payoff = 0


class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Example(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class HoltLaury(Page):
    form_model = 'player'
    form_fields = [
        'holt_laury_choice_1',
        'holt_laury_choice_2',
        'holt_laury_choice_3',
        'holt_laury_choice_4',
        'holt_laury_choice_5',
        'holt_laury_choice_6',
        'holt_laury_choice_7',
        'holt_laury_choice_8',
        'holt_laury_choice_9',
        'holt_laury_choice_10',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        choices = [
            player.holt_laury_choice_1,
            player.holt_laury_choice_2,
            player.holt_laury_choice_3,
            player.holt_laury_choice_4,
            player.holt_laury_choice_5,
            player.holt_laury_choice_6,
            player.holt_laury_choice_7,
            player.holt_laury_choice_8,
            player.holt_laury_choice_9,
            player.holt_laury_choice_10,
        ]

        risk_level = choices.count('A')
        player.risk_aversion_level = risk_level
        player.participant.risk_aversion_level = risk_level

        paid_row = random.randint(1, 10)
        player.holt_laury_paid_row = paid_row
        player.participant.holt_laury_paid_row = paid_row

        selected_choice = choices[paid_row - 1]
        high_probability = paid_row / 10

        if selected_choice == 'A':
            if random.random() < high_probability:
                payoff = C.HL_A_HIGH
            else:
                payoff = C.HL_A_LOW
        else:
            if random.random() < high_probability:
                payoff = C.HL_B_HIGH
            else:
                payoff = C.HL_B_LOW

        player.holt_laury_payoff = payoff
        player.participant.holt_laury_payoff = payoff
        player.participant.holt_laury_selected_choice = selected_choice


class StartGame(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class TreatmentInfo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def vars_for_template(player: Player):
        payoff_table = PAYOFFS[player.case][player.environment]

        return {
            'case': player.case,
            'block_number': player.block_number,
            'payoff_H': payoff_table['H'],
            'payoff_L': payoff_table['L'],
            'survival_probs': survival_probabilities(player),
        }


class PublicSignal(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'round_number': player.round_number,
            'total_rounds': C.NUM_ROUNDS,
            'public_signal': player.public_signal,
            'case': player.case,
        }


class Metacognition(Page):
    form_model = 'player'
    form_fields = [
        'belief_good',
        'confidence_tau',
        'kappa',
        'belief_touched',
        'confidence_touched',
        'kappa_touched',
    ]

    @staticmethod
    def error_message(player, values):
        if values['belief_touched'] == 0:
            return "Please move the belief slider."
        if values['confidence_touched'] == 0:
            return "Please move the second slider."
        if values['kappa_touched'] == 0:
            return "Please move the third slider."


class BuyInfo(Page):
    form_model = 'player'
    form_fields = ['buy_info']

    @staticmethod
    def vars_for_template(player: Player):
        payoff_table = PAYOFFS[player.case][player.environment]

        return {
            'public_signal': player.public_signal,
            'delta_percent': int(player.delta * 100),
            'case': player.case,
            'payoff_H': payoff_table['H'],
            'payoff_L': payoff_table['L'],
            'survival_probs': survival_probabilities(player),
        }


class PrivateSignal(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.buy_info

    @staticmethod
    def vars_for_template(player: Player):
        if player.field_maybe_none('private_signal') is None:
            generate_private_signal(player)

        return {
            'private_signal': player.field_maybe_none('private_signal'),
            'public_signal': player.public_signal,
            'delta_percent': int(player.delta * 100),
        }


class Investment(Page):
    form_model = 'player'
    form_fields = [
        'investment',
        'investment_touched',
    ]

    @staticmethod
    def error_message(player: Player, values):
        if values['investment_touched'] == 0:
            return "Please move the investment slider."

        max_investment = max_investment_allowed(player)

        if values['investment'] > max_investment:
            return f"You cannot invest more than {max_investment} tokens."

    @staticmethod
    def vars_for_template(player: Player):
        max_investment = max_investment_allowed(player)
        payoff_table = PAYOFFS[player.case][player.environment]

        return {
            'max_investment': max_investment,
            'buy_info': player.buy_info,
            'public_signal': player.public_signal,
            'private_signal': player.field_maybe_none('private_signal'),
            'delta_percent': int(player.delta * 100),
            'case': player.case,
            'payoff_H': payoff_table['H'],
            'payoff_L': payoff_table['L'],
            'survival_probs': survival_probabilities(player),
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_aversion_level = player.participant.risk_aversion_level

        calculate_survival_periods(player)
        calculate_payoff(player)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        state_display = "Good" if player.state == "H" else "Bad"

        return {
            'state': state_display,
            'survival_periods': player.survival_periods,
            'round_tokens': round(player.round_tokens, 2),
        }


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        all_players = player.in_all_rounds()

        try:
            paid_rounds = participant.paid_rounds
        except AttributeError:
            paid_rounds = random.sample(
                range(1, C.NUM_ROUNDS + 1),
                3
            )

        paid_rounds = sorted(paid_rounds)
        paid_players = [p for p in all_players if p.round_number in paid_rounds]

        investment_tokens = sum(p.round_tokens for p in paid_players) / len(paid_players)

        holt_laury_tokens = participant.holt_laury_payoff
        holt_laury_paid_row = participant.holt_laury_paid_row
        holt_laury_selected_choice = participant.holt_laury_selected_choice

        total_tokens = investment_tokens + holt_laury_tokens
        bonus_euros = total_tokens / C.TOKENS_PER_EURO

        paid_rounds_text = " and ".join([f"Round {r}" for r in paid_rounds])

        player.payoff = total_tokens

        return {
            'paid_rounds': paid_rounds,
            'paid_rounds_text': paid_rounds_text,
            'paid_players': paid_players,
            'investment_tokens': round(investment_tokens, 2),
            'holt_laury_tokens': round(holt_laury_tokens, 2),
            'holt_laury_paid_row': holt_laury_paid_row,
            'holt_laury_selected_choice': holt_laury_selected_choice,
            'total_tokens': round(total_tokens, 2),
            'bonus_euros': round(bonus_euros, 2),
        }


page_sequence = [
    Welcome,
    Instructions,
    Example,
    HoltLaury,
    StartGame,
    TreatmentInfo,
    PublicSignal,
    Metacognition,
    BuyInfo,
    PrivateSignal,
    Investment,
    Results,
    FinalResults,
]


def custom_export(players):
    yield [
        'participant_code',
        'round_number',
        'environment',
        'env_F',
        'env_B',
        'block_number',
        'case',
        'delta',
        'breakage_probability',
        'state',
        'state_H',
        'public_signal',
        'public_good',
        'private_signal',
        'private_good',
        'belief_good',
        'confidence_tau',
        'kappa',
        'belief_scaled',
        'tau_scaled',
        'kappa_scaled',
        'belief_uncertainty',
        'risk_aversion_level',
        'holt_laury_paid_row',
        'holt_laury_selected_choice',
        'holt_laury_payoff',
        'buy_info',
        'buy_info_num',
        'investment',
        'max_investment',
        'investment_share',
        'R_H',
        'R_L',
        'payoff_spread',
        'payoff_spread_squared',
        'expected_return_public',
        'lambda_term_proxy',
        'survival_periods',
        'round_tokens',
        'is_paid_round',
    ]

    for p in players:
        try:
            paid_rounds = p.participant.paid_rounds
        except AttributeError:
            paid_rounds = []

        environment = p.field_maybe_none('environment')
        state = p.field_maybe_none('state')
        public_signal = p.field_maybe_none('public_signal')
        private_signal = p.field_maybe_none('private_signal')
        buy_info = p.field_maybe_none('buy_info')
        delta = p.field_maybe_none('delta')

        belief_good = p.field_maybe_none('belief_good')
        confidence_tau = p.field_maybe_none('confidence_tau')
        kappa = p.field_maybe_none('kappa')
        investment = p.field_maybe_none('investment')

        belief_scaled = belief_good / 100 if belief_good is not None else None
        tau_scaled = confidence_tau / 100 if confidence_tau is not None else None
        kappa_scaled = kappa / 100 if kappa is not None else None

        belief_uncertainty = (
            belief_scaled * (1 - belief_scaled)
            if belief_scaled is not None
            else None
        )

        if delta is not None:
            r_h = discounted_return(p, 'H')
            r_l = discounted_return(p, 'L')
            spread = r_h - r_l
            spread_squared = spread ** 2
            expected_public = expected_return_public(p)
        else:
            r_h = None
            r_l = None
            spread = None
            spread_squared = None
            expected_public = None

        if buy_info is True:
            max_investment = C.ENDOWMENT - C.INFO_COST
        elif buy_info is False:
            max_investment = C.ENDOWMENT
        else:
            max_investment = None

        investment_share = (
            investment / max_investment
            if investment is not None and max_investment not in [None, 0]
            else None
        )

        lambda_term_proxy = (
            belief_uncertainty * spread_squared
            if belief_uncertainty is not None and spread_squared is not None
            else None
        )

        holt_laury_paid_row = getattr(p.participant, 'holt_laury_paid_row', None)
        holt_laury_selected_choice = getattr(p.participant, 'holt_laury_selected_choice', None)
        holt_laury_payoff = getattr(p.participant, 'holt_laury_payoff', None)

        yield [
            p.participant.code,
            p.round_number,
            environment,
            1 if environment == 'F' else 0,
            1 if environment == 'B' else 0,
            p.field_maybe_none('block_number'),
            p.field_maybe_none('case'),
            delta,
            round(1 - delta, 2) if delta is not None else None,
            state,
            1 if state == 'H' else 0,
            public_signal,
            1 if public_signal == 'Good' else 0,
            private_signal,
            1 if private_signal == 'Good' else 0 if private_signal == 'Bad' else None,
            belief_good,
            confidence_tau,
            kappa,
            round(belief_scaled, 4) if belief_scaled is not None else None,
            round(tau_scaled, 4) if tau_scaled is not None else None,
            round(kappa_scaled, 4) if kappa_scaled is not None else None,
            round(belief_uncertainty, 4) if belief_uncertainty is not None else None,
            p.field_maybe_none('risk_aversion_level'),
            holt_laury_paid_row,
            holt_laury_selected_choice,
            holt_laury_payoff,
            buy_info,
            1 if buy_info is True else 0 if buy_info is False else None,
            investment,
            max_investment,
            round(investment_share, 4) if investment_share is not None else None,
            round(r_h, 4) if r_h is not None else None,
            round(r_l, 4) if r_l is not None else None,
            round(spread, 4) if spread is not None else None,
            round(spread_squared, 4) if spread_squared is not None else None,
            round(expected_public, 4) if expected_public is not None else None,
            round(lambda_term_proxy, 4) if lambda_term_proxy is not None else None,
            p.field_maybe_none('survival_periods'),
            p.field_maybe_none('round_tokens'),
            1 if p.round_number in paid_rounds else 0,
        ]
