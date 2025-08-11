from django.contrib.auth.models import BaseUserManager
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        if not extra_fields.get("is_active", True):
            user.activation_key = str(
                uuid.uuid4()
            )  # Generate activation key for inactive users
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)  # Superuser is always active

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def update_password(self, user, new_password):
        """
        Updates the user's password with the correct hash.

          Args:
          user: The user object whose password to update
          new_password: The new password in plain text

          Returns:
          The updated user object
        """
        if not new_password:
            raise ValueError("Password cannot be empty")

        user.set_password(new_password)
        user.save(using=self._db)
        return user
