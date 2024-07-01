import uuid


def uuid_generator() -> str:
    """
    Generate a UUID string
    :return: UUID string
    """

    return str(uuid.uuid4())
