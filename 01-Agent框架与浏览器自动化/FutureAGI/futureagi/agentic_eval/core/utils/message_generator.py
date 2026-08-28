from ...core.signatures.signatures import MySignature, Signature, get_signature_object
from ...core.utils.functions import download_image_to_base64


def message_generator(signature: Signature, prompt: str):
    data = get_signature_object(signature)
    # Extract fields from signature
    input_fields = data.get("input", [])
    image_fields = data.get("image", [])
    output_fields = data.get("output", [])
    doc = data.get("doc", "")
    # Append output fields to the prompt
    for field in output_fields:
        for key, value in field.items():
            if key != "desc":
                prompt += f"\n{field.get('desc')}: {value}"
    # Constructing the message structure
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{prompt}\n\n{doc}"},
                *[
                    {"type": "text", "text": f"{field.get('desc')}: {value}"}
                    for field in input_fields
                    for key, values in field.items()
                    if key != "desc"
                    for value in (values if isinstance(values, list) else [values])
                ],
                *[
                    {
                        "type": "image_url",
                        "image_url": {
                            # "url": f"data:image/jpeg;base64,{encode_image(img)}"
                            "url": img
                        },
                    }
                    for field in image_fields
                    for key, value in field.items()
                    if key != "desc"
                    for img in (value if isinstance(value, list) else [value])
                ],
            ],
        }
    ]

    return messages


def prompt_message_generator(prompt):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ],
        }
    ]


# Example usage
if __name__ == "__main__":
    # Example signature object

    # Example prompt
    prompt = "Please generate output based on input fields and images."
    sig = MySignature()
    # Generate messages
    generated_messages = message_generator(sig, prompt)
    print(generated_messages)
