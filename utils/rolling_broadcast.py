from database import (
    save_broadcast_message,
    get_broadcast_messages,
    delete_broadcast_message,
)


MAX_MESSAGES_PER_EVENT = 7


async def send_rolling_broadcast(
    bot,
    chat_id,
    text,
    event_type,
    parse_mode="HTML",
):
    """
    Send an event broadcast and keep only
    the latest 7 messages for each event type.
    """

    # =====================================
    # SEND NEW MESSAGE
    # =====================================

    message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )

    # =====================================
    # SAVE MESSAGE
    # =====================================

    save_broadcast_message(
        event_type=event_type,
        chat_id=chat_id,
        message_id=message.message_id,
    )

    # =====================================
    # GET EVENT MESSAGES
    # =====================================

    messages = get_broadcast_messages(
        event_type=event_type,
        chat_id=chat_id,
    )

    # =====================================
    # KEEP ONLY LATEST 7
    # =====================================

    if len(messages) > MAX_MESSAGES_PER_EVENT:

        old_messages = messages[
            :-MAX_MESSAGES_PER_EVENT
        ]

        for old_message in old_messages:

            try:

                await bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_message["message_id"],
                )

            except Exception as e:

                print(
                    "Could not delete broadcast "
                    f"{old_message['message_id']}: {e}"
                )

            # Remove tracking record whether
            # Telegram deletion succeeded or not.
            delete_broadcast_message(
                old_message["id"]
            )

    return message
