# cli_tool.py
import argparse
from auth import register_user, load_users
import config


def create_user(username, password, is_admin=False):
    success = register_user(username, password)
    if success:
        print(f"User '{username}' created successfully.")
        if is_admin:
            config.ADMINS.append(username)
            print(f"User '{username}' granted admin rights.")
    else:
        print(f"User '{username}' already exists.")


def list_users():
    users = load_users()
    print("Registered users:")
    for user in users:
        role = "Admin" if user in config.ADMINS else "User"
        print(f"- {user} ({role})")


def main():
    parser = argparse.ArgumentParser(description="MediChain Admin CLI")
    subparsers = parser.add_subparsers(dest='command')

    add_user = subparsers.add_parser('add-user')
    add_user.add_argument('username')
    add_user.add_argument('password')
    add_user.add_argument('--admin', action='store_true')

    list_users_cmd = subparsers.add_parser('list-users')

    args = parser.parse_args()

    if args.command == 'add-user':
        create_user(args.username, args.password, args.admin)
    elif args.command == 'list-users':
        list_users()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
# cli_tool.py
import argparse
from auth import register_user, load_users
import config


def create_user(username, password, is_admin=False):
    success = register_user(username, password)
    if success:
        print(f"User '{username}' created successfully.")
        if is_admin:
            config.ADMINS.append(username)
            print(f"User '{username}' granted admin rights.")
    else:
        print(f"User '{username}' already exists.")


def list_users():
    users = load_users()
    print("Registered users:")
    for user in users:
        role = "Admin" if user in config.ADMINS else "User"
        print(f"- {user} ({role})")


def main():
    parser = argparse.ArgumentParser(description="MediChain Admin CLI")
    subparsers = parser.add_subparsers(dest='command')

    add_user = subparsers.add_parser('add-user')
    add_user.add_argument('username')
    add_user.add_argument('password')
    add_user.add_argument('--admin', action='store_true')

    list_users_cmd = subparsers.add_parser('list-users')

    args = parser.parse_args()

    if args.command == 'add-user':
        create_user(args.username, args.password, args.admin)
    elif args.command == 'list-users':
        list_users()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
