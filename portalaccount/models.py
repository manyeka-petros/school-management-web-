from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

# ============================
# Custom User Manager
# ============================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# ============================
# Custom User Model
# ============================
class User(AbstractUser):
    class UserType(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        PARENT = 'parent', 'Parent'
        STAFF = 'staff', 'Staff'
        HEADTEACHER = 'headteacher', 'Head Teacher'

    username = None  # Remove username field
    first_name = models.CharField(max_length=100, blank=True, null=True)  # Made optional
    last_name = models.CharField(max_length=100, blank=True, null=True)   # Made optional
    email = models.EmailField(unique=True)
    user_type = models.CharField(
        max_length=30,
        choices=UserType.choices,
        default=UserType.STUDENT
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Removed required first_name, last_name

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.user_type})"

    @property
    def full_name(self):
        # Return empty string if names missing to avoid errors
        fn = self.first_name or ''
        ln = self.last_name or ''
        return f"{fn} {ln}".strip()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


# ============================
# Student Profile
# ============================
class StudentProfile(models.Model):
    user = models.OneToOneField('portalaccount.User', on_delete=models.CASCADE, related_name='student_profile')
    profile_picture = models.ImageField(upload_to='student_profile_pics/', blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)

    classroom = models.ForeignKey(
        'academic.Classroom',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    admitted_on = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(default='active', max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Student Profile - {self.user.full_name}"


# ============================
# Teacher Profile
# ============================
class TeacherProfile(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    user = models.OneToOneField('portalaccount.User', on_delete=models.CASCADE, related_name='teacher_profile')
    profile_picture = models.ImageField(upload_to='teacher_profile_pics/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    qualification = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Teacher Profile - {self.user.full_name}"


# ============================
# Head Teacher Profile
# ============================
class HeadTeacherProfile(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    user = models.OneToOneField('portalaccount.User', on_delete=models.CASCADE, related_name='headteacher_profile')
    profile_picture = models.ImageField(upload_to='headteacher_profile_pics/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, default='Head Teacher', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    joined_on = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Head Teacher - {self.user.full_name}"


# ============================
# Parent Profile
# ============================
class ParentProfile(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    user = models.OneToOneField('portalaccount.User', on_delete=models.CASCADE, related_name='parent_profile')
    profile_picture = models.ImageField(upload_to='parent_profile_pics/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    relation_to_student = models.CharField(max_length=100, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parent Profile - {self.user.full_name}"


# ============================
# Staff Profile
# ============================
class StaffProfile(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    user = models.OneToOneField('portalaccount.User', on_delete=models.CASCADE, related_name='staff_profile')
    profile_picture = models.ImageField(upload_to='staff_profile_pics/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)  # Made optional
    joined_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Staff Profile - {self.user.full_name}"
