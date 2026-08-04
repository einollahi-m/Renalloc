from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate active users with either username or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("identifier")
        if not identifier or password is None:
            return None

        UserModel = get_user_model()
        identifier = identifier.strip()
        user = UserModel._default_manager.filter(email__iexact=identifier).first()
        if user is None:
            user = UserModel._default_manager.filter(
                username__iexact=identifier
            ).first()

        if user is None:
            # Keep password hashing work similar when the account does not exist.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
