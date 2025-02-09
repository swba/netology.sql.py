from .types import ClientValues


class Client:
    """Client model"""

    def __init__(self, props: ClientValues):
        self.id = props.get('client_id')
        self.first_name = props.get('first_name')
        self.last_name = props.get('last_name')
        self.email = props.get('email')
        self.phone_numbers = props.get('phone_numbers', [])

    def __str__(self):
        parts = [f'({self.id})', self.first_name, self.last_name]
        if self.email:
            parts.append(f'<{self.email}>')
        if len(self.phone_numbers):
            parts.append('[' + ', '.join(self.phone_numbers) + ']')
        return ' '.join(parts)
