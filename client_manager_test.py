import psycopg
from pytest import raises

from client_manager import ClientManager
from client_manager.errors import ClientNotExistsError

def test_client_manager():
    with open('db.txt', encoding='UTF-8') as f:
        with psycopg.connect(f.readline()) as conn:
            cm = ClientManager(conn)

            # Prepare client tables.
            cm.setup()

            # Add a client.
            client = cm.add_client({
                'first_name': 'Michael',
                'last_name': 'Keaton',
                'email': 'm.keaton@hollywood.com',
                'phone_numbers': [
                    '+12222222222',
                ],
            })
            assert str(client) == '(1) Michael Keaton <m.keaton@hollywood.com> [+12222222222]'

            # Add a phone number to the client.
            client = cm.add_phone_number(client.id, '+13333333333')
            assert str(client) == '(1) Michael Keaton <m.keaton@hollywood.com> [+12222222222, +13333333333]'

            # Delete the original phone number.
            client = cm.delete_phone_number(client.id, '+12222222222')
            assert str(client) == '(1) Michael Keaton <m.keaton@hollywood.com> [+13333333333]'

            # Add another client.
            client = cm.add_client({
                'first_name': 'Bruce',
                'last_name': 'Dickinson',
                'email': 'b.dickinson@ironmaiden.com',
                'phone_numbers': [
                    '+441111111111',
                    '+442222222222',
                ],
            })
            assert str(client) == '(2) Bruce Dickinson <b.dickinson@ironmaiden.com> [+441111111111, +442222222222]'

            # Add one more client.
            client = cm.add_client({
                'first_name': 'Some',
                'last_name': 'Guy',
                'email': 's.guy@guys.ru',
                'phone_numbers': [
                    '+71111111111',
                    '+72222222222',
                ],
            })
            assert str(client) == '(3) Some Guy <s.guy@guys.ru> [+71111111111, +72222222222]'

            # Now delete it...
            cm.delete_client(client.id)

            # ...and try to load it.
            assert cm.load_client(client.id) is None

            # Internal test: after client deletion there shouldn't be
            # any phone numbers related to deleted client left in the
            # database.
            assert cm._load_phone_numbers(client.id) == []

            # Add a client with just first and last names.
            client = cm.add_client({
                'first_name': 'Rafael',
                'last_name': 'Nadal',
            })
            assert str(client) == '(4) Rafael Nadal'

            # Now change its last name and add an email.
            client.last_name = 'Nadal Parera'
            client.email = 'r.nadal@rafaelnadal.com'
            cm.update_client(client)
            assert str(client) == '(4) Rafael Nadal Parera <r.nadal@rafaelnadal.com>'

            # Now explicitly set the client's phone numbers.
            client.phone_numbers.append('+341111111111')
            client.phone_numbers.append('+342222222222')
            cm.update_client(client)
            assert str(client) == '(4) Rafael Nadal Parera <r.nadal@rafaelnadal.com> [+341111111111, +342222222222]'

            # Try to update client that doesn't exist.
            with raises(ClientNotExistsError) as e:
                client.id = 999
                cm.update_client(client)
                assert e.value == 'Client with ID=999 does not exist'

            # Search clients by name.
            clients = cm.search_clients({
                'first_name': 'michael'
            })
            assert [str(c) for c in clients.values()] == [
                '(1) Michael Keaton <m.keaton@hollywood.com> [+13333333333]'
            ]

            # Search clients by last name suffix.
            clients = cm.search_clients({
                'last_name': '%on'
            })
            assert [str(c) for c in clients.values()] == [
                '(1) Michael Keaton <m.keaton@hollywood.com> [+13333333333]',
                '(2) Bruce Dickinson <b.dickinson@ironmaiden.com> [+441111111111, +442222222222]'
            ]

            # Search clients with letter "a" in their first name and
            # letter "r" in their email :)
            clients = cm.search_clients({
                'first_name': '%a%',
                'email': '%r%'
            })
            assert [str(c) for c in clients.values()] == [
                '(4) Rafael Nadal Parera <r.nadal@rafaelnadal.com> [+341111111111, +342222222222]'
            ]

            # Search clients by local phone numbers.
            clients = cm.search_clients({
                'phone_number': '%1111111111',
            })
            assert [str(c) for c in clients.values()] == [
                '(2) Bruce Dickinson <b.dickinson@ironmaiden.com> [+441111111111, +442222222222]',
                '(4) Rafael Nadal Parera <r.nadal@rafaelnadal.com> [+341111111111, +342222222222]'
            ]

            # Search by a full phone number.
            clients = cm.search_clients({
                'phone_number': '+13333333333',
            })
            assert [str(c) for c in clients.values()] == [
                '(1) Michael Keaton <m.keaton@hollywood.com> [+13333333333]'
            ]

            # Search that shouldn't find anything.
            clients = cm.search_clients({
                'first_name': 'Michael',
                'last_name': 'Dickinson',
            })
            assert clients is None

