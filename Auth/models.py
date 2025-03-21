from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class School(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']



class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + " at " + self.school.name

class Book(models.Model):
    id = models.AutoField(primary_key=True)
    isbn = models.CharField(max_length=100, null=False, default= '')
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100)
    quantity = models.IntegerField()
    cost = models.DecimalField(max_digits=5, decimal_places=2)
    image = models.URLField()
    subjects = models.ManyToManyField(Subject)

class Stationary(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    image = models.URLField()
    quantity = models.IntegerField()
    cost = models.DecimalField(max_digits=5, decimal_places=2)

class Order(models.Model):
    paid_for = models.BooleanField(default=False)
    date_time_placed = models.DateTimeField()
    date_time_paid = models.DateTimeField(null=True)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    qr_code = models.URLField()
    books = models.ManyToManyField("Book", through="OrderBook")
    stationary = models.ManyToManyField("Stationary", through="OrderStationary")

class OrderBook(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("order", "book")

class OrderStationary(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    stationary = models.ForeignKey("Stationary", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("order", "stationary")

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)





