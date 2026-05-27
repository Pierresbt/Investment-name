# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 17:01:51 2026

@author: pierr
"""


from otree.api import *
import random
from datetime import datetime


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
    POUNDS_PER_EURO = 0.85
    BONUS_CAP_EUROS = 6

    # Prolific completion URL. Use this in FinalResults.html as {{ prolific_completion_url }}.
    PROLIFIC_COMPLETION_URL = 'https://app.prolific.com/submissions/complete?cc=C1OT5Q2B'

    CASES = [3, 4, 5]
    ROUNDS_PER_BLOCK = 7

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


def get_round_in_block(round_number):
    return ((round_number - 1) % C.ROUNDS_PER_BLOCK) + 1


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

            # Deterministic balanced assignment
            participant_id = participant.id_in_session

            if participant_id % 2 == 1:
                environment = 'F'
            else:
                environment = 'B'

            selected_cases = random.sample(C.CASES, 3)
            paid_rounds = random.sample(range(1, C.NUM_ROUNDS + 1), 3)

            participant.vars['environment'] = environment

            participant.vars['case_block_1'] = selected_cases[0]
            participant.vars['case_block_2'] = selected_cases[1]
            participant.vars['case_block_3'] = selected_cases[2]

            participant.vars['case_order_1'] = selected_cases[0]
            participant.vars['case_order_2'] = selected_cases[1]
            participant.vars['case_order_3'] = selected_cases[2]

            participant.vars['paid_rounds'] = paid_rounds

        player.environment = participant.vars['environment']

        player.block_number = get_block_number(subsession.round_number)

        if player.block_number == 1:
            player.case = participant.vars['case_block_1']
        elif player.block_number == 2:
            player.case = participant.vars['case_block_2']
        else:
            player.case = participant.vars['case_block_3']

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


def store_prolific_identifiers(player: Player):
    """Store Prolific identifiers in participant.vars when available.

    Important:
    - The safest way to capture PROLIFIC_PID in oTree is to include
      participant_label={{%PROLIFIC_PID%}} in the Prolific study URL.
    - The export also checks PROLIFIC_PID / STUDY_ID / SESSION_ID in
      participant.vars in case they are provided by the deployment/setup.
    """
    participant = player.participant

    prolific_pid = (
        participant.vars.get('prolific_pid')
        or participant.vars.get('PROLIFIC_PID')
        or participant.label
    )

    study_id = (
        participant.vars.get('study_id')
        or participant.vars.get('STUDY_ID')
        or ''
    )

    session_id = (
        participant.vars.get('session_id')
        or participant.vars.get('SESSION_ID')
        or ''
    )

    participant.vars['prolific_pid'] = prolific_pid
    participant.vars['study_id'] = study_id
    participant.vars['session_id'] = session_id


class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        participant = player.participant

        store_prolific_identifiers(player)

        if 'experiment_start_timestamp' not in participant.vars:
            now = datetime.now()
            participant.vars['experiment_start_timestamp'] = now.timestamp()
            participant.vars['experiment_start_datetime'] = now.isoformat()


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
        player.participant.vars['risk_aversion_level'] = risk_level

        paid_row = random.randint(1, 10)
        selected_choice = choices[paid_row - 1]
        high_probability = paid_row / 10

        if selected_choice == 'A':
            payoff = C.HL_A_HIGH if random.random() < high_probability else C.HL_A_LOW
        else:
            payoff = C.HL_B_HIGH if random.random() < high_probability else C.HL_B_LOW

        player.participant.vars['holt_laury_paid_row'] = paid_row
        player.participant.vars['holt_laury_selected_choice'] = selected_choice
        player.participant.vars['holt_laury_payoff'] = payoff


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
            'round_in_block': get_round_in_block(player.round_number),
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
            'block_number': player.block_number,
            'round_in_block': get_round_in_block(player.round_number),
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
            'block_number': player.block_number,
            'round_in_block': get_round_in_block(player.round_number),
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
            'block_number': player.block_number,
            'round_in_block': get_round_in_block(player.round_number),
            'payoff_H': payoff_table['H'],
            'payoff_L': payoff_table['L'],
            'survival_probs': survival_probabilities(player),
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.risk_aversion_level = player.participant.vars.get('risk_aversion_level', None)

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
        store_prolific_identifiers(player)
        all_players = player.in_all_rounds()

        paid_rounds = participant.vars.get(
            'paid_rounds',
            random.sample(range(1, C.NUM_ROUNDS + 1), 3)
        )

        paid_rounds = sorted(paid_rounds)
        paid_players = [p for p in all_players if p.round_number in paid_rounds]

        investment_tokens = sum(p.round_tokens for p in paid_players) / len(paid_players)

        holt_laury_tokens = participant.vars.get('holt_laury_payoff', 0)
        holt_laury_paid_row = participant.vars.get('holt_laury_paid_row', None)
        holt_laury_selected_choice = participant.vars.get('holt_laury_selected_choice', None)

        # Raw theoretical payment before the cap, expressed in euros and pounds.
        raw_total_payment_tokens = investment_tokens + holt_laury_tokens
        raw_total_payment_euros = raw_total_payment_tokens / C.TOKENS_PER_EURO
        raw_total_payment_pounds = raw_total_payment_euros * C.POUNDS_PER_EURO

        # Actual performance-based bonus after the cap, expressed in euros and pounds.
        total_payment_euros = min(raw_total_payment_euros, C.BONUS_CAP_EUROS)
        total_payment_pounds = total_payment_euros * C.POUNDS_PER_EURO

        participant.vars['investment_payment_average'] = investment_tokens
        participant.vars['holt_laury_payment'] = holt_laury_tokens

        participant.vars['raw_total_payment_euros'] = raw_total_payment_euros
        participant.vars['raw_total_payment_pounds'] = raw_total_payment_pounds

        participant.vars['total_payment_euros'] = total_payment_euros
        participant.vars['total_payment_pounds'] = total_payment_pounds

        if 'experiment_end_timestamp' not in participant.vars:
            now = datetime.now()
            participant.vars['experiment_end_timestamp'] = now.timestamp()
            participant.vars['experiment_end_datetime'] = now.isoformat()

            start_timestamp = participant.vars.get('experiment_start_timestamp', None)
            if start_timestamp is not None:
                participant.vars['total_experiment_seconds'] = (
                    participant.vars['experiment_end_timestamp'] - start_timestamp
                )
            else:
                participant.vars['total_experiment_seconds'] = None

        paid_rounds_text = " and ".join([f"Round {r}" for r in paid_rounds])

        # oTree payoff records the actual capped bonus in pounds.
        player.payoff = total_payment_pounds

        return {
            'paid_rounds': paid_rounds,
            'paid_rounds_text': paid_rounds_text,
            'paid_players': paid_players,
            'investment_tokens': round(investment_tokens, 2),
            'holt_laury_tokens': round(holt_laury_tokens, 2),
            'holt_laury_paid_row': holt_laury_paid_row,
            'holt_laury_selected_choice': holt_laury_selected_choice,
            'raw_total_payment_euros': round(raw_total_payment_euros, 2),
            'raw_total_payment_pounds': round(raw_total_payment_pounds, 2),
            'total_payment_euros': round(total_payment_euros, 2),
            'total_payment_pounds': round(total_payment_pounds, 2),
            'prolific_completion_url': C.PROLIFIC_COMPLETION_URL,
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
        # Identification
        'participant_code',
        'session_code',
        'prolific_pid',
        'study_id',
        'prolific_session_id',
        'round_number',
        'round_in_block',
        'completed_participant',

        # Treatment structure
        'environment',
        'env_F',
        'env_B',
        'block_number',
        'project_type_seen_by_subject',
        'case',
        'case_order_1',
        'case_order_2',
        'case_order_3',

        # State, signals, and timing
        'delta',
        'breakage_probability',
        'state',
        'state_H',
        'public_signal',
        'public_good',
        'private_signal',
        'private_good',

        # Beliefs and metacognition
        'belief_good',
        'confidence_tau',
        'kappa',
        'belief_scaled',
        'tau_scaled',
        'kappa_scaled',
        'belief_uncertainty',
        'posterior_public',
        'perceived_qy',
        'posterior_private_v6',

        # Risk task
        'risk_aversion_level',
        'risk_aversion_scaled',
        'holt_laury_paid_row',
        'holt_laury_selected_choice',
        'holt_laury_payoff',

        # Information and investment choices
        'buy_info',
        'buy_info_num',
        'investment',
        'max_investment',
        'investment_share',

        # Payoff environment variables
        'R_H',
        'R_L',
        'payoff_spread',
        'payoff_spread_squared',
        'expected_return_public',
        'lambda_term_proxy',

        # Realized outcome
        'survival_periods',
        'round_tokens',
        'is_paid_round',

        # Final payment variables
        'investment_payment_average',
        'holt_laury_payment_final',
        'total_payment_tokens',
        'total_payment_euros',

        # Completion timing
        'experiment_start_datetime',
        'experiment_end_datetime',
        'total_experiment_seconds',
        'total_experiment_minutes',
    ]

    for p in players:
        participant = p.participant

        prolific_pid = participant.vars.get('prolific_pid', None)
        study_id = participant.vars.get('study_id', None)
        prolific_session_id = participant.vars.get('session_id', None)

        paid_rounds = participant.vars.get('paid_rounds', [])

        all_rounds = p.in_all_rounds()
        completed_participant = int(
            sum(r.field_maybe_none('investment') is not None for r in all_rounds) == C.NUM_ROUNDS
        )

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

        posterior_public = None
        perceived_qy = None
        posterior_private_v6 = None

        if public_signal == 'Good':
            posterior_public = C.PUBLIC_SIGNAL_PRECISION
        elif public_signal == 'Bad':
            posterior_public = 1 - C.PUBLIC_SIGNAL_PRECISION

        if tau_scaled is not None and kappa_scaled is not None:
            perceived_qy = 0.5 + (1 - kappa_scaled * tau_scaled) * (
                C.PRIVATE_SIGNAL_PRECISION - 0.5
            )

        if posterior_public is not None and perceived_qy is not None and private_signal is not None:
            if private_signal == 'Good':
                posterior_private_v6 = (
                    perceived_qy * posterior_public
                ) / (
                    perceived_qy * posterior_public
                    + (1 - perceived_qy) * (1 - posterior_public)
                )
            elif private_signal == 'Bad':
                posterior_private_v6 = (
                    (1 - perceived_qy) * posterior_public
                ) / (
                    (1 - perceived_qy) * posterior_public
                    + perceived_qy * (1 - posterior_public)
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

        risk_aversion_level = p.field_maybe_none('risk_aversion_level')
        risk_aversion_scaled = (
            risk_aversion_level / 10
            if risk_aversion_level is not None
            else None
        )

        holt_laury_paid_row = participant.vars.get('holt_laury_paid_row', None)
        holt_laury_selected_choice = participant.vars.get('holt_laury_selected_choice', None)
        holt_laury_payoff = participant.vars.get('holt_laury_payoff', None)

        investment_payment_average = participant.vars.get('investment_payment_average', None)
        holt_laury_payment_final = participant.vars.get('holt_laury_payment', None)
        total_payment_tokens = participant.vars.get('total_payment_tokens', None)
        total_payment_euros = participant.vars.get('total_payment_euros', None)

        experiment_start_datetime = participant.vars.get('experiment_start_datetime', None)
        experiment_end_datetime = participant.vars.get('experiment_end_datetime', None)
        total_experiment_seconds = participant.vars.get('total_experiment_seconds', None)

        total_experiment_minutes = (
            total_experiment_seconds / 60
            if total_experiment_seconds is not None
            else None
        )

        yield [
            # Identification
            participant.code,
            p.session.code,
            prolific_pid,
            study_id,
            prolific_session_id,
            p.round_number,
            get_round_in_block(p.round_number),
            completed_participant,

            # Treatment structure
            environment,
            1 if environment == 'F' else 0,
            1 if environment == 'B' else 0,
            p.field_maybe_none('block_number'),
            p.field_maybe_none('block_number'),
            p.field_maybe_none('case'),
            participant.vars.get('case_order_1', None),
            participant.vars.get('case_order_2', None),
            participant.vars.get('case_order_3', None),

            # State, signals, and timing
            delta,
            round(1 - delta, 2) if delta is not None else None,
            state,
            1 if state == 'H' else 0,
            public_signal,
            1 if public_signal == 'Good' else 0,
            private_signal,
            1 if private_signal == 'Good' else 0 if private_signal == 'Bad' else None,

            # Beliefs and metacognition
            belief_good,
            confidence_tau,
            kappa,
            round(belief_scaled, 4) if belief_scaled is not None else None,
            round(tau_scaled, 4) if tau_scaled is not None else None,
            round(kappa_scaled, 4) if kappa_scaled is not None else None,
            round(belief_uncertainty, 4) if belief_uncertainty is not None else None,
            round(posterior_public, 4) if posterior_public is not None else None,
            round(perceived_qy, 4) if perceived_qy is not None else None,
            round(posterior_private_v6, 4) if posterior_private_v6 is not None else None,

            # Risk task
            risk_aversion_level,
            round(risk_aversion_scaled, 4) if risk_aversion_scaled is not None else None,
            holt_laury_paid_row,
            holt_laury_selected_choice,
            holt_laury_payoff,

            # Information and investment choices
            buy_info,
            1 if buy_info is True else 0 if buy_info is False else None,
            investment,
            max_investment,
            round(investment_share, 4) if investment_share is not None else None,

            # Payoff environment variables
            round(r_h, 4) if r_h is not None else None,
            round(r_l, 4) if r_l is not None else None,
            round(spread, 4) if spread is not None else None,
            round(spread_squared, 4) if spread_squared is not None else None,
            round(expected_public, 4) if expected_public is not None else None,
            round(lambda_term_proxy, 4) if lambda_term_proxy is not None else None,

            # Realized outcome
            p.field_maybe_none('survival_periods'),
            p.field_maybe_none('round_tokens'),
            1 if p.round_number in paid_rounds else 0,

            # Final payment variables
            round(investment_payment_average, 2) if investment_payment_average is not None else None,
            round(holt_laury_payment_final, 2) if holt_laury_payment_final is not None else None,
            round(total_payment_tokens, 2) if total_payment_tokens is not None else None,
            round(total_payment_euros, 2) if total_payment_euros is not None else None,

            # Completion timing
            experiment_start_datetime,
            experiment_end_datetime,
            round(total_experiment_seconds, 2) if total_experiment_seconds is not None else None,
            round(total_experiment_minutes, 2) if total_experiment_minutes is not None else None,
        ]