from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter

from typing import Any
from functools import wraps

from source.autocomplete import get_autocomplete, style
from source.datamodels import (
    AddressBook,
    Record,
    NotesBook,
    Note,
)
from source.reader import BookReader


class BaseCliHelperException(Exception):
    """This is a generic Cli Helper exception."""


class CommandNotSupported(BaseCliHelperException):
    """This exception is to be raised when Cli Helper encounters a non-supported command."""


class CliHelperSigStop(BaseCliHelperException):
    """This exception is to be raised whenever we need to immediately stop the bot."""


class CommandOperationalError(BaseCliHelperException):
    """This exception is raised whenever we try to do an operation that is not allowed."""


def input_error(error_msg_base):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (
                CommandOperationalError,
                CommandNotSupported,
                ValueError,
                KeyError,
            ) as e:
                return f"{error_msg_base}: {e}"

        return wrapper

    return decorator


class CliHelperBot:
    _address_book: AddressBook = None
    _notes_book: NotesBook = None

    def __init__(self, address_book: AddressBook, notes_book: NotesBook):
        self.supported_commands = {
            "close": self.stop,
            "exit": self.stop,
            "hello": self.say_hello,
            "add": self.add_contact,
            "update-phone": self.change_contact,
            "phone": self.get_contact,
            "search": self.search_contact,
            "all": self.print_all_contacts,
            "add-birthday": self.add_birthday,
            "show-birthday": self.show_birthday,
            "birthdays": self.birthdays,
            "add-address": self.add_address,
            "add-email": self.add_email,
            "add-note": self.add_note,
            "delete-note": self.delete_note,
            "find-note": self.find_note,
            "all-notes": self.all_notes,
            "add-project-tasks": self.add_project_tasks,
            "add-hobby": self.add_hobby,
            "find-project-role": self.find_project_role,
            "find-hobby": self.find_hobby,
            "update-hobby": self.update_hobby,
            "delete-contact": self.delete_contact,
            "delete-email": self.delete_email,
            "delete-phone": self.delete_phone,
            "delete-address": self.delete_address,
            "delete-birthday": self.delete_birthday,
            "update-email": self.update_email,
            "update-address": self.update_address,
            "update-birthday": self.update_birthday,
            "help": self.help,
        }
        self._address_book = address_book
        self._notes_book = notes_book

    def help(self, *args: str) -> str:
        """Outputs a help message for user."""
        command_output = ""
        if len(args) > 1:
            command_output += (
                "Warning: Command optionally expect one argument - command name. "
                f"Received: {' '.join(args)}\n"
            )

        search_command = args[0] if args else None

        if search_command:
            if search_command not in self.supported_commands:
                return "Command not supported. Type 'help' to get list of supported commands."

            command_output += f"Command '{search_command}' help: "
            command_output += f"\n{self.supported_commands[search_command].__doc__.split('Returns:')[0].strip()}"
            return command_output

        command_output += "Supported commands: "
        for command in sorted(self.supported_commands):
            command_output += f"\n{command}"
        command_output += "\n\nType 'help <command>' to get help for specific command."

        return command_output

    def stop(self, message: str):
        """Stop the bot execution.

        Args:
            message: Explanation why bot needs to stop

        Returns:
            None

        Raises:
            CliHelperSigStop: with explanation message
        """
        raise CliHelperSigStop(message)

    @staticmethod
    def parse_input(user_input: str) -> (str, list[Any]):
        command, *args = user_input.split()
        command = command.casefold()

        if command in ["close", "exit"]:
            args = [f"Command '{command}' received. Good buy!"]

        return command, args

    @staticmethod
    def say_hello(*args: str) -> str:
        """Outputs a hello message for user."""
        command_output = ""
        if args:
            command_output += (
                "Warning: Command doesn't expect any arguments. "
                f"Received: {' '.join(args)}\n"
            )

        return command_output + "How can I help you?"

    @input_error(error_msg_base="Command 'add-birthday' failed")
    def add_birthday(self, *args: str) -> str:
        """Add birthday date to already existing record.

        Args:
            args: List with username and date to parse as YYYY.MM.DD.

        Returns:
            Command output

        Raises:
            CommandOperationalError if user does not exist.
            ValueError if date is invalid.
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: username and date, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        username, date_str = args
        try:
            record = self._address_book.find(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. "
                f"If you want to add number, please use 'add' command."
            ) from e

        record.add_birthday(date_str)
        return f"Contact {username} updated with date: {date_str}."

    @input_error(error_msg_base="Command 'add' failed")
    def add_contact(self, *args: str) -> str:
        """Add contact into Address Book.

        Args:
            args: List with username and phone of user to add.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user already exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: username and phone, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        username, phone = args
        record = self._address_book.add_record(Record(name_=username, phones=[phone]))

        if record is None:
            raise CommandOperationalError(
                f"user with username {username} already exist. "
                f"If you want to update number, please use 'change' command."
            )

        return f"Contact {username} created with phone: {phone}."

    @input_error(error_msg_base="Command 'update' failed")
    def change_contact(self, *args: str) -> str:
        """Change contact in Address Book.

        Args:
            args: List with username and phone of user to add.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: username and phone, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        username, phone = args
        try:
            record = self._address_book.find(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. "
                f"If you want to add number, please use 'add' command."
            ) from e

        record.edit_phone(record.phones[0].value, phone)
        return f"Contact {username} updated with phone: {phone}."

    @input_error(error_msg_base="Command 'show-birthday' failed")
    def show_birthday(self, *args: str) -> str:
        """Get user birthday by username.

        Args:
            args: List of one argument - username

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: username. "
                f"Received: {' '.join(args)}"
            )

        username = args[0]
        try:
            record = self._address_book.find(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. Try another username."
            ) from e

        return f"User's {username} birthday is: {record.birthday}"

    @input_error(error_msg_base="Command 'search' failed")
    def search_contact(self, *args: str) -> str:
        """Search user data by search query.

        Args:
            args: List of one argument - search query

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: search query. "
                f"Received: {' '.join(args)}"
            )

        query = args[0]
        records = self._address_book.search(query)

        if not records:
            return "No records found with provided query."

        command_output = "Found Records: "
        for record in records:
            command_output += f"\n{record}"

        return command_output

    @input_error(error_msg_base="Command 'phone' failed")
    def get_contact(self, *args: str) -> str:
        """Get user phone by username.

        Args:
            args: List of one argument - username

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: username. "
                f"Received: {' '.join(args)}"
            )

        username = args[0]
        try:
            record = self._address_book.find(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. Try another username."
            ) from e

        return f"Record found: \n{record}"

    @input_error(error_msg_base="Command 'birthdays' failed")
    def birthdays(self, *args: str) -> str:
        """Prepares all contacts to be outputted into console that have BD in a following number of days.

        Args:
            args: Number of days.

        Returns:
            Command output.
        """
        command_output = ""
        if len(args) != 1:
            raise CommandOperationalError(
                "Warning: Command expect one argument: number of days. "
                f"Received: {' '.join(args)}\n"
            )

        try:
            days = int(args[0])
        except ValueError:
            raise CommandOperationalError(
                "Command expects a valid integer - number of days, please recheck your input."
            )

        results = self._address_book.get_birthdays_per_days(days).items()
        if not results:
            return "No contacts found"

        command_output += "Contacts per day: "
        for date, records in results:
            records_str = "| " + "\n | ".join(str(r) for r in records)
            command_output += f"\nHave BD on {date}:\n {records_str}"

        return command_output

    def print_all_contacts(self, *args: str) -> str:
        """Prepares contacts to be outputted into console.

        Args:
            args: Command doesn't expect any args, list should be empty.

        Returns:
            Command output.
        """
        command_output = ""
        if args:
            command_output += (
                "Warning: Command doesn't expect any arguments. "
                f"Received: {' '.join(args)}\n"
            )

        command_output += "All Records: "
        for record in self._address_book.values():
            command_output += f"\n{record}"

        return command_output

    @input_error(error_msg_base="Command execution failed")
    def execute_command(self, command: str, args: list[str]) -> str:
        if command not in self.supported_commands:
            raise CommandNotSupported(f"command '{command}' is not supported!")

        command_handler = self.supported_commands[command]
        return command_handler(*args)

    @input_error(error_msg_base="Command 'add-address' failed")
    def add_address(self, *args: str) -> str:
        """Add address to already existing record.

        Args:
            args: List with username and address.

        Returns:
            Command output

        Raises:
            CommandOperationalError if user does not exist.
            ValueError if date is invalid.
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: username and address, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        username, address_str = args
        try:
            record = self._address_book.find(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. "
                f"If you want to add address, please use 'add-address' command."
            ) from e

        record.add_address(address_str)
        return f"Contact {username} updated with address: {address_str}."

    @input_error(error_msg_base="Command 'add-email' failed")
    def add_email(self, *args: str) -> str:
        """Add email to already existing record.

        Args:
            args: List with username and email.

        Returns:
            Command output

        Raises:
            CommandOperationalError if user does not exist.
            ValueError if date is invalid.
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: username and email, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        username, email_str = args
        try:
            record = self._address_book.find(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. "
                f"If you want to add email, please use 'add-email' command."
            ) from e

        record.add_email(email_str)
        return f"Contact {username} updated with email: {email_str}."

    @input_error(error_msg_base="Command 'add-note' failed")
    def add_note(self, *args: str) -> str:
        """Add note into Notes Book.

        Args:
            args: List note name and project role to add.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user already exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: name and project role, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        name, project_role = args
        note = self._notes_book.add_note(Note(name_=name, project_role=project_role))

        if note is None:
            raise CommandOperationalError(
                f"Note {name} already exist. "
                f"If you want to update project role, please use 'change-project-role' command."
            )

        return f"Created note {name} {project_role}."

    @input_error(error_msg_base="Command 'delete-note' failed")
    def delete_note(self, *args: str) -> str:
        """Delete note by name.

        Args:
            args: Name of note to remove.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or note doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: note name. "
                f"Received: {' '.join(args)}"
            )

        name = args[0]
        try:
            self._notes_book.delete(name)

        except KeyError as e:
            raise CommandOperationalError(
                f"Note with name {name} doesn't exist. "
            ) from e

        return f"Note {name} removed from Notes book."

    @input_error(error_msg_base="Command 'add-project-tasks' failed")
    def add_project_tasks(self, *args: str) -> str:
        """Add project tasks to existing note.

        Args:
            args: List with note name and project string.

        Returns:
            Command output

        Raises:
            CommandOperationalError if user does not exist.
            ValueError if date is invalid.
        """
        if len(args) <= 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: name and project tasks string, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        name, *project_tasks = args
        tasks_str = " ".join(t for t in project_tasks)

        try:
            note = self._notes_book.find(name)

        except KeyError as e:
            raise CommandOperationalError(
                f"note with name {name} doesn't exist. "
            ) from e

        note.add_project_tasks(tasks_str)
        return f"Note {name} updated"

    @input_error(error_msg_base="Command 'find-note' failed")
    def find_note(self, *args: str) -> str:
        """Find note by name.

        Args:
            args: Note name to find.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or no note found
        """

        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: name string."
                f"Received: {len(args)}"
            )

        name = args[0]
        note = self._notes_book.find(name_=name)

        return f"Found note: {note}"

    @input_error(error_msg_base="Command 'find-project-role' failed")
    def find_project_role(self, *args: str) -> str:
        """Find notes by project role.

        Args:
            args: Project role to find.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or no note found
        """

        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: project role string."
                f"Received: {len(args)}"
            )

        project_role = args[0]
        result = self._notes_book.find_project_role(project_role_=project_role)

        command_output = "Found Notes: "
        for record in result:
            command_output += f"\n{record}"

        return command_output

    @input_error(error_msg_base="Command 'add-hobby' failed")
    def add_hobby(self, *args: str) -> str:
        """Add hobby to already existing note by name.

        Args:
            args: List with name and hobby.

        Returns:
            Command output

        Raises:
            CommandOperationalError if note does not exist.
        """
        if len(args) <= 2:
            raise CommandOperationalError(
                "command expects an input of two arguments: name and hobby, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        name, *hobby = args
        hobby_str = " ".join(t for t in hobby)

        try:
            note = self._notes_book.find(name)

        except KeyError as e:
            raise CommandOperationalError(
                f"note with name {name} doesn't exist. "
            ) from e

        note.add_hobby(hobby_str)
        return f"Note {name} updated with hobby: {hobby_str}."

    @input_error(error_msg_base="Command 'find-hobby' failed")
    def find_hobby(self, *args: str) -> str:
        """Find notes by hobby.

        Args:
            args: Hobby to find.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or no note found
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: hobby string."
                f"Received: {len(args)}"
            )

        hobby = args[0]
        result = self._notes_book.find_hobby(hobby_=hobby)

        command_output = "Found Notes: "
        for record in result:
            command_output += f"\n{record}"

        return command_output

    @input_error(error_msg_base="Command 'update' failed")
    def update_hobby(self, *args: str) -> str:
        """Change specific hobbyin the note.

        Args:
            args: List with name, old hobby and new hobby of note to add.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or note doesn't exist
        """
        if len(args) != 3:
            raise CommandOperationalError(
                "command expects an input of three arguments: name, old hobby and new hobby, separated by a space. "
                f"Received: {' '.join(args)}"
            )

        name, old_hobby, new_hobby = args
        try:
            note = self._notes_book.find(name)

        except KeyError as e:
            raise CommandOperationalError(
                f"note with name {name} doesn't exist. "
            ) from e

        note.edit_hobby(hobby=old_hobby, new_hobby=new_hobby)
        return f"Note {name} updated with new hobby: {new_hobby}."

    def all_notes(self, *args: str) -> str:
        """Prepares notes to be outputted into console.

        Args:
            args: Command doesn't expect any args, list should be empty.

        Returns:
            Command output.
        """
        command_output = ""
        if args:
            command_output += (
                "Warning: Command doesn't expect any arguments. "
                f"Received: {' '.join(args)}\n"
            )

        command_output += "All Notes: "
        for note in self._notes_book.values():
            command_output += f"\n{note}"

        return command_output

    @input_error(error_msg_base="Command 'delete-contact' failed")
    def delete_contact(self, *args: str) -> str:
        """Delete contact in Address Book.

        Args:
            args: username of user to remove.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: username. "
                f"Received: {' '.join(args)}"
            )

        username = args[0]
        try:
            self._address_book.delete(username)

        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn't exist. "
            ) from e

        return f"Contact {username} removed from Address book."

    @input_error(error_msg_base="Command 'delete-phone' failed")
    def delete_phone(self, *args: str) -> str:
        """Delete phone by username.

        Args:
            args: List of two argument - username and phone.

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of one argument: username and phone. "
                f"Received: {' '.join(args)}"
            )

        username, phone = args
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.remove_phone(phone)
        return f"Phone of contact  {username} removed from Address book."

    @input_error(error_msg_base="Command 'delete-email' failed")
    def delete_email(self, *args: str) -> str:
        """Delete user email by username.

        Args:
            args: List of one argument - username

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: username. "
                f"Received: {' '.join(args)}"
            )

        username = args[0]
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.remove_email()
        return f"Email of contact  {username} removed from Address book."

    @input_error(error_msg_base="Command 'delete-address' failed")
    def delete_address(self, *args: str) -> str:
        """Delete user address by username.

        Args:
            args: List of one argument - username

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: username. "
                f"Received: {' '.join(args)}"
            )

        username = args[0]
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.remove_address()
        return f"Address of contact  {username} removed from Address book."

    @input_error(error_msg_base="Command 'delete-birthday' failed")
    def delete_birthday(self, *args: str) -> str:
        """Delete user birthday by username.

        Args:
            args: List of one argument - username

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 1:
            raise CommandOperationalError(
                "command expects an input of one argument: username. "
                f"Received: {' '.join(args)}"
            )

        username = args[0]
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.remove_birthday()
        return f"Birthday of contact {username} removed from Address book."

    @input_error(error_msg_base="Command 'update-email' failed")
    def update_email(self, *args: str) -> str:
        """Update user email by username.

        Args:
            args: List of two argument - username and email

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of 2 arguments: username and email "
                f"Received: {' '.join(args)}"
            )

        username, email = args
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.update_email(email)
        return f"Email of contact  {username} updated."

    @input_error(error_msg_base="Command 'update-address' failed")
    def update_address(self, *args: str) -> str:
        """Update user address by username.

        Args:
            args: List of two argument - username and address

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of 2 arguments: username and address "
                f"Received: {' '.join(args)}"
            )

        username, address = args
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.update_address(address)
        return f"Address of contact  {username} updated."

    @input_error(error_msg_base="Command 'update-birthday' failed")
    def update_birthday(self, *args: str) -> str:
        """Update user birthday by username.

        Args:
            args: List of two argument - username and birthday

        Returns:
            Command output.

        Raises:
            CommandOperationalError: if wrong arguments or user doesn't exist
        """
        if len(args) != 2:
            raise CommandOperationalError(
                "command expects an input of 2 arguments: username and birthday "
                f"Received: {' '.join(args)}"
            )

        username, birthday = args
        try:
            record = self._address_book.find(username)
        except KeyError as e:
            raise CommandOperationalError(
                f"user with username {username} doesn`t exist. Try another username"
            ) from e

        record.update_birthday(birthday)
        return f"Birthday of contact  {username} updated."

    def main(self) -> None:

        while True:
            try:
                autocomplete_list = get_autocomplete(
                    self._address_book.get_all_names(),
                    list(self.supported_commands.keys()),
                )
                text = NestedCompleter.from_nested_dict(autocomplete_list)
                session = PromptSession(completer=text, style=style)

                user_input = session.prompt(
                    "Enter a command with arguments separated with a ' ' character: "
                )

                command, args = self.parse_input(user_input)
                command_output = self.execute_command(command, args)
                print(
                    f"Command was'{command}' executed, might have been successfully. Result is:"
                    f"\n{command_output}"
                )

            except CliHelperSigStop as e:
                print(e)
                break

            except Exception as e:
                print(
                    f"Unknown exception was encountered during execution: {e}"
                    "The bot will stop ..."
                )
                raise


def main():
    with BookReader() as book:
        cli_helper = CliHelperBot(book.address_book, book.notes_book)
        cli_helper.main()


if __name__ == "__main__":
    main()
