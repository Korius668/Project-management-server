
class DomainError(Exception):
    """Bazowy wyjątek domenowy"""
    pass


class DatabaseError(DomainError):
    """Ogólny błąd warstwy bazy danych"""
    pass


class UserAlreadyExistsError(DomainError):
    """Wyjątek gdy użytkownik już istnieje"""
    pass

class UserNotFoundError(DomainError):
    """Wyjątek gdy użytkownik nie został znaleziony"""
    pass

class UserDeletionForbiddenError(DomainError):
    """Wyjątek gdy nie można usunąć użytkownika (zależności w bazie)"""
    pass


class ProjectNotFoundError(DomainError):
    """Wyjątek gdy projekt nie został znaleziony"""
    pass

class ProjectAlreadyExistsError(DomainError):
    pass


class DocumentAlreadyExistsError(DomainError):
    pass

class DocumentNotFoundError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass
