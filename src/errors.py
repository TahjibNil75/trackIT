from fastapi import HTTPException, status



class BadRequestError(HTTPException):
    def __init__(self, message: str = "Bad request."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class UserAlreadyExistsError(HTTPException):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{email}' already exists."
        )


class InvalidCredentialsError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )


class PasswordMismatchError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )


class NotFoundError(HTTPException):
    def __init__(self, resource_name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found."
        )


class UnauthorizedError(HTTPException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )


# ==================== Ticket-specific Errors ====================
class TicketNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Ticket")

class AttachmentNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Attachment")


class UserNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("User")


class InvalidTicketUpdateError(HTTPException):
    def __init__(self, message: str = "Invalid update request for this ticket."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class TicketPermissionError(UnauthorizedError):
    def __init__(self, message: str = "You do not have permission to update this ticket."):
        super().__init__(detail=message)


class TicketPriorityUpdateError(UnauthorizedError):
    def __init__(self, message: str = "Only admin, manager, or IT support can update ticket priority."):
        super().__init__(message)



class TicketStatusUpdateError(UnauthorizedError):
    def __init__(self, message: str = "Only admin, manager, or IT support can update ticket status."):
        super().__init__(detail=message)


class TicketAssignmentError(UnauthorizedError):
    def __init__(self, message: str = "You do not have permission to assign this ticket."):
        super().__init__(detail=message)


# ==================== Ticket-specific Errors ====================
class CommentNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Comment")