

class ClientError(Exception):
    """Custom exception for client errors."""
    pass


class ClientNotExistsError(ClientError):
    """Raised when client to be updated doesn't exist"""
    pass
