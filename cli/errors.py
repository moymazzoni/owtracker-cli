class Errors:
    """
    All errors are here in order to not make custom messages everytime I
    want to cover a potential error because I might genuinely kill myself plus
    that is very error-prone.
    """

    # Account errors
    ACCOUNT_CREATION_FAILED = 'Account "{player_id}" could not be saved in the database: {error}'
    ACCOUNT_DELETION_FAILED = 'Account "{player_id}" could not be deleted: {error}'
    ACCOUNT_MODIFICATION_FAILED = 'Account "{player_id}" was unable to be changed in the database: {error}'

    ACCOUNT_ALREADY_EXISTS = 'Account "{player_id}" already exists in the database.'
    ACCOUNT_DOESNT_EXIST = 'Account "{player_id}" doesn\'t exist in the database.'
    ACCOUNT_NO_ATTRIBUTES = 'Account "{player_id}" has no attributes.'
    ACCOUNT_ATTRIBUTE_MISSING = 'Account "{player_id}" does not contain the attribute: "{attribute}".'
    ACCOUNT_MODIFICATION_REPTETITIVE_VALUE = 'Account "{player_id}" was not updated as the "{attribute}" attribute already has the same value that you entered ("{replacement}"). '
    ACCOUNT_MODIFICATION_ILLEGAL_ATTRIBUTE = 'Attribute "{attribute}" is in the database, but it should not be altered. No permission to modify it.'
    ACCOUNT_ATTRIBUTE_VALUE_INVALID = 'Attribute "{attribute}" for account "{player_id}" has no value or an unuseable value.'

    # General / reusable errors
    EMPTY_OPTIONS = 'Somehow the options menu is completely empty. Terminating application.'
    OUT_OF_RANGE = 'Out of range: "{value}"'
    VALUE_NOT_ALLOWED = 'Value "{value}" is not allowed. Must be one of: "{allowed}"'
    MISSING_KEY = 'Missing required key: {key}'
    INVALID_TYPE = 'Incorrect type, expected: {expected}'
    INCORRECT_GIVEN = 'Incorrect given value used: "{value}"'


class AppError(Exception):
    """Base exception for the whole app. Formats a template with kwargs."""

    template = 'An application error occurred: {error}'  # fallback

    def __init__(self, template=None, **kwargs):
        # Allows raising with no template override: raise SomeError(player_id=x)
        template = template or self.template
        super().__init__(template.format(**kwargs))


class AccountError(AppError):
    """Base exception for account operations."""


class AccountAlreadyExistsError(AccountError):
    """Raised when attempting to add an account that already exists."""
    template = Errors.ACCOUNT_ALREADY_EXISTS


class AccountCreationError(AccountError):
    """
    Raised when an account could not be created due to an unexpected error.
    """
    template = Errors.ACCOUNT_CREATION_FAILED


class AccountDoesntExist(AccountError):
    """Raised when an account could not be found in the database."""
    template = Errors.ACCOUNT_DOESNT_EXIST


class AccountDeletionError(AccountError):
    """
    Raised when an account could not be removed due to an unexpected error.
    """
    template = Errors.ACCOUNT_DELETION_FAILED


class AccountModificationError(AccountError):
    """
    Raised when an account could not be modified due to an unexpected error.
    """
    template = Errors.ACCOUNT_MODIFICATION_FAILED


class AccountAttributeError(AccountError):
    """Raised when an account does not contain an attribute being requested."""
    template = Errors.ACCOUNT_ATTRIBUTE_MISSING


class AccountAttributeInvalidValueError(AccountError):
    """
    Raised when an account does have the attribute being requested, but it is
    unuseable or empty.
    """
    template = Errors.ACCOUNT_ATTRIBUTE_VALUE_INVALID


class AccountNoAttributesError(AccountError):
    """Raised when an account has no attributes at all."""
    template = Errors.ACCOUNT_NO_ATTRIBUTES


class AccountInaccessibleAttribute(AccountError):
    """
    Raised when an account should not interact with an attribute excluded
    from the editable fields
    """
    template = Errors.ACCOUNT_MODIFICATION_ILLEGAL_ATTRIBUTE


class AccountModificationRepetitiveValueError(AccountError):
    """
    Raised when an account attribute's value is being changed to the same
    value that was given (changing username from "Froggo" to "Froggo").
    """
    template = Errors.ACCOUNT_MODIFICATION_REPTETITIVE_VALUE


# ----------------------------------------------------------------------------#

class OutOfRangeError(AppError):
    """Raised when value is out of bounds."""
    template = Errors.OUT_OF_RANGE


class IncorrectValue(AppError):
    """Raised when given value is not correct."""
    template = Errors.INCORRECT_GIVEN


class NoOptionsInMenuError(AppError):
    """Raised when main menu has no options (somehow)."""
    template = Errors.EMPTY_OPTIONS

class RankDivisionError(AppError):
    """Raised when an account's division in the database"""

