import html
import random

from telegram import Update, MessageEntity
from telegram.ext import Filters, CallbackContext
from telegram.error import BadRequest
from .sql import afk_sql as sql
from .users import get_user_id
from .helper_funcs.decorators import kigcmd, kigmsg


@kigmsg(Filters.regex("(?i)^brb"), friendly="afk", group=3)
@kigcmd(command="afk", group=3)
def afk(update: Update, _: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user

    if not user or user.id in (777000, 1087968824, 136817688):  # ignore channels
        return

    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text("{} is now away!{}".format(fname, notice))
    except BadRequest:
        pass


@kigmsg((Filters.all & Filters.chat_type.groups), friendly='afk', group=1)
def no_longer_afk(update: Update, _: CallbackContext):
    user = update.effective_user
    message = update.effective_message

    if not user or user.id in (777000, 1087968824, 136817688):  # ignore channels
        return

    if sql.rm_afk(user.id):
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} is here!",
                "{} is back!",
                "{} is now in the chat!",
                "{} is awake!",
                "{} is back online!",
                "{} is finally here!",
                "Welcome back! {}",
                "Where is {}?\nIn the chat!",
            ]
            chosen_option = random.choice(options)
            update.effective_message.reply_text(
                chosen_option.format(firstname), parse_mode=None
            )
        except:
            return


@kigmsg(
        (Filters.entity(MessageEntity.MENTION) | Filters.entity(MessageEntity.TEXT_MENTION) & Filters.chat_type.groups),
        friendly='afk', group=8)
def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type != MessageEntity.MENTION:
                return

            user_id = get_user_id(
                message.text[ent.offset : ent.offset + ent.length]
            )
            if not user_id:
                # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                return

            if user_id in chk_users:
                return
            chk_users.append(user_id)

            try:
                chat = bot.get_chat(user_id)
            except BadRequest:
                print(
                    "Error: Could not fetch userid {} for AFK module".format(
                        user_id
                    )
                )
                return
            fst_name = chat.first_name

            check_afk(update, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, user_id, fst_name, userc_id)


def check_afk(update, user_id, fst_name, userc_id):
    if int(userc_id) == int(user_id):
        return
    is_afk, reason = sql.check_afk_status(user_id)
    if is_afk:
        if not reason:
            res = "{} is afk".format(fst_name)
            update.effective_message.reply_text(res, parse_mode=None)
        else:
            res = "{} is afk.\nReason: <code>{}</code>".format(
                html.escape(fst_name), html.escape(reason)
            )
            update.effective_message.reply_text(res, parse_mode="html")


def __gdpr__(user_id):
    sql.rm_afk(user_id)


# from .language import gs
#
# def get_help(chat):
#     return gs(chat, "afk_help")


__mod_name__ = "AFK"
