import json
import os
import random
import re
import time
from enum import Enum
from time import sleep

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, run_async, Handler

from common import *
from reputation import update_reputation


with open(os.path.join(asset_folder, 'good_citizen_test', 'questions.json'), 'r') as handle:
    questions = json.load(handle)


question_correct_responses = [
    'That is correct! Maybe there is some hope for you after all...',
    'That\'s right! Guess you\'re not getting sent to Xinjiang today...',
    'Correct! Good boy!',
    'That\'s right, UwU',
    'That is the correct answer. Keep it up and your social credit score might not be complete garbage at the end of this...'
]

question_wrong_responses = [
    'You fool. You absolute buffoon, the correct answer was ${CORRECT}.',
    'Really? You really thought it was ${ANSWER} and not ${CORRECT}? You are deranged.',
    'What? No. Are you braindead? It\'s ${CORRECT} obviously...',
    'You\'d have to be some real degenerate piece of capitalist scum if you really thought ${ANSWER} was the correct answer...',
    'No it\'s ${CORRECT}, idiot.'
]


class Question:
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)


class ConversationState:
    conversations = dict() # user => state

    def __init__(self, user):
        self.user = user
        self.questions_right = 0
        self.questions_wrong = 0
        self.previous_answer_wrong = False

    def questions_answered(self):
        return self.questions_wrong + self.questions_right

    @staticmethod
    def get_conversation(user):
        if user not in ConversationState.conversations:
            ConversationState.conversations[user] = ConversationState(user)

        return ConversationState.conversations[user]

    @staticmethod
    def close_conversation(user):
        if user in ConversationState.conversations:
            del ConversationState.conversations[user]

    @staticmethod
    def get_next_question(user):
        conversation = ConversationState.get_conversation(user)
        question     = conversation.questions_answered()

        return question, Question(**questions[question])


class QuestionProgressState(Enum):
    SHOWED_QUESTION = 0


def print_current_question(update, context):
    index, question = ConversationState.get_next_question(update.message.from_user.id)

    send_message(update, context, f'Question {index + 1}: {question.question}')

    if hasattr(question, 'image'):
        send_image_message_with_context(update, context, f'good_citizen_test/{question.image}')

    send_message(update, context, '\n'.join(question.answers))


def get_post_answer_state(update, context):
    state = ConversationState.get_conversation(update.message.from_user.id)

    if state.questions_answered() == 10:
        handle_test_passed(update, context)
        return ConversationHandler.END
    else:
        print_current_question(update, context)
        return QuestionProgressState.SHOWED_QUESTION


def handle_correct_answer(update, context, responses = question_correct_responses):
    state = ConversationState.get_conversation(update.message.from_user.id)

    send_reply(update, context, random.choice(responses))

    update_reputation(+5, update)
    state.questions_right += 1
    state.previous_answer_wrong = False

    return get_post_answer_state(update, context)


def handle_wrong_answer(update, context, responses = question_wrong_responses):
    index, question = ConversationState.get_next_question(update.message.from_user.id)
    given_answer    = update.message.text.upper()
    state           = ConversationState.get_conversation(update.message.from_user.id)

    send_reply(
        update,
        context,
        random.choice(responses)
            .replace('${CORRECT}', question.correct_answer)
            .replace('${ANSWER}', given_answer)
    )

    update_reputation(-20, update)
    state.questions_wrong += 1

    if state.previous_answer_wrong:
        handle_test_failed(update, context)
        return ConversationHandler.END

    state.previous_answer_wrong = True
    return get_post_answer_state(update, context)


def handle_question_answer(update, context):
    index, question  = ConversationState.get_next_question(update.message.from_user.id)
    given_answer     = update.message.text.upper()
    possible_answers = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")[0:len(question.answers)]


    if len(given_answer) == 1 and given_answer in possible_answers:
        if given_answer == question.correct_answer:
           return handle_correct_answer(update, context)
        else:
            return handle_wrong_answer(update, context)
    else:
        send_reply(update, context, f'Please answer with one of the following: {", ".join(possible_answers)}')
        return QuestionProgressState.SHOWED_QUESTION


def handle_test_passed(update, context):
    send_reply(
        update,
        context,
        f'Thank you {display_user(update.message.from_user)} for completing the good citizen test. ' +
        f'Your social credit score will be adjusted accordingly...'
    )

    ConversationState.close_conversation(update.message.from_user.id)
    update_reputation(+500, update)
    on_gct_completed(update)


def handle_test_failed(update, context):
    send_reply(
        update,
        context,
        f'That\'s enough {display_user(update.message.from_user)}, it is obvious that you are nothing but capitalist scum. ' +
        f'Your social credit score will be adjusted accordingly...'
    )

    ConversationState.close_conversation(update.message.from_user.id)
    update_reputation(-1000, update)
    on_gct_completed(update)


def handle_conversation_start(update, context):
    may_start, reason = may_start_gct(update)

    if not may_start:
        update.message.reply_text(reason)
        return ConversationHandler.END
    else:
        on_gct_started(update)

        update.message.reply_text(read_text('good_citizen_test/prelude.txt')),
        sleep(30),

        print_current_question(update, context),
        return QuestionProgressState.SHOWED_QUESTION



def make_handler():
    return ConversationHandler(
        entry_points = [MessageHandler(
            Filters.regex(re.compile(r'good citizen', re.IGNORECASE)),
            handle_conversation_start
        )],
        fallbacks = [CommandHandler(
            'cancel',
            lambda u, c: (
                ConversationState.close_conversation(u.message.from_user.id),
                u.message.reply_text('The test has been cancelled. For not completing the Good Citizen Test, you will be deducted 100 Social Credit.'),
                update_reputation(-100, u),
                on_gct_completed(u),
                ConversationHandler.END
            )[-1]
        )],
        states = {
            QuestionProgressState.SHOWED_QUESTION: [ MessageHandler(
                Filters.text & ~Filters.command,
                handle_question_answer
            )]
        },
        run_async = True
    )


class GCT_SERVER_STATE(Enum):
    IN_PROGRESS = 0
    DONE        = 1

# Not really important enough to serialize.
# Format: Server ID => (Username, Timestamp, State)
last_gct_for_server = dict()


# Returns (bool, reason).
def may_start_gct(update):
    # May trigger at most once per day per chat.
    id = update.effective_chat.id

    if id not in last_gct_for_server:
        return True, None
    else:
        user, timestamp, state = last_gct_for_server[id]

        if state == GCT_SERVER_STATE.IN_PROGRESS:
            return False, f"I am kinda busy with {user} at the moment..."

        if time.time() - timestamp < (24 * 60 * 60):
            return False, "The CCP Social Credit System is still processing the results of the previous Good Citizen Test that took place in this server. Please try again later."

        return True, None


def on_gct_started(update):
    last_gct_for_server[update.effective_chat.id] = (update.message.from_user.full_name, time.time(), GCT_SERVER_STATE.IN_PROGRESS)

def on_gct_completed(update):
    last_gct_for_server[update.effective_chat.id] = (update.message.from_user.full_name, time.time(), GCT_SERVER_STATE.DONE)