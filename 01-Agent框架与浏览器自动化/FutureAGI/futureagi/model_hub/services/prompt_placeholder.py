def _handle_text_message(message_content: str) -> dict:
    """Handle text message type."""
    if not message_content:
        raise ValueError("Message content is required for text type")

    content = [{"text": message_content, "type": "text"}]

    return {"role": "user", "content": content}


def _handle_audio_url_message(
    file_url: str, file_name: str, message_content: str | None = None
) -> dict:
    """Handle audio_url message type."""
    if not file_url or not file_name:
        raise ValueError("File url and file name are required for audio_url type")

    content = [
        {"audio_url": {"url": file_url, "audio_name": file_name}, "type": "audio_url"}
    ]

    if message_content and len(message_content) > 0:
        content.append({"text": message_content, "type": "text"})

    return {"role": "user", "content": content}


def _handle_pdf_url_message(
    file_url: str, file_name: str, message_content: str | None = None
) -> dict:
    """Handle pdf_url message type."""
    if not file_url or not file_name:
        raise ValueError("File url and file name are required for pdf_url type")

    content = [
        {
            "pdf_url": {"url": file_url, "pdf_name": file_name, "file_name": file_name},
            "type": "pdf_url",
        }
    ]

    if message_content and len(message_content) > 0:
        content.append({"text": message_content, "type": "text"})

    return {"role": "user", "content": content}


def _handle_image_url_message(
    file_url: str, file_name: str, message_content: str | None = None
) -> dict:
    """Handle image_url message type."""
    if not file_url or not file_name:
        raise ValueError("File url and file name are required for image_url type")

    content = [
        {"image_url": {"url": file_url, "image_name": file_name}, "type": "image_url"}
    ]

    if message_content and len(message_content) > 0:
        content.append({"text": message_content, "type": "text"})

    return {"role": "user", "content": content}


def validate_and_parse_placeholder(messages):

    parsed_messages = []
    # sample object
    #     {
    #   "type": "text/audio_url/pdf_url/image_url",
    #   "message": "",
    #   "file_name": ""
    # }

    for message in messages:
        message_type = message.get("type")
        message_content = message.get("message", None)
        file_name = message.get("file_name", None)
        file_url = message.get("file_url", None)
        parsed_message = None

        if message_type not in ["text", "audio_url", "pdf_url", "image_url"]:
            raise ValueError("Invalid message type")

        if message_type == "text":
            parsed_message = _handle_text_message(message_content)
        elif message_type == "audio_url":
            parsed_message = _handle_audio_url_message(
                file_url, file_name, message_content
            )
        elif message_type == "pdf_url":
            parsed_message = _handle_pdf_url_message(
                file_url, file_name, message_content
            )
        elif message_type == "image_url":
            parsed_message = _handle_image_url_message(
                file_url, file_name, message_content
            )
        else:
            raise ValueError("Invalid message type")

        if parsed_message:
            parsed_messages.append(parsed_message)

    return parsed_messages
