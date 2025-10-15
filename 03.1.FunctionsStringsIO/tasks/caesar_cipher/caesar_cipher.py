def caesar_encrypt_char(c: str, n: int) -> str:
    if not c.isalpha():
        return c
    start = ord('a' if c.islower() else 'A')
    return  chr(start + (ord(c) - start + n) % 26)


def caesar_encrypt(message: str, n: int) -> str:
    """Encrypt message using caesar cipher

    :param message: message to encrypt
    :param n: shift
    :return: encrypted message
    """
    return ''.join(map(lambda c: caesar_encrypt_char(c, n=n), message))
