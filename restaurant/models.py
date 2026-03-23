from django.contrib.auth.models import User
from django.db import models


class Dish(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='dishes/', blank=True, null=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    amount = models.IntegerField()
    check_request_id = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)


class Reservation(models.Model):
    TABLE_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('private', 'Private Room'),
        ('any', 'No Preference'),
    ]

    OCCASION_CHOICES = [
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('business', 'Business Dinner'),
        ('date', 'Date Night'),
        ('family', 'Family Gathering'),
        ('other', 'Other'),
        ('', 'None'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user             = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name        = models.CharField(max_length=255)
    phone            = models.CharField(max_length=20)
    email            = models.EmailField(blank=True, null=True)
    date             = models.DateField()
    time             = models.TimeField()
    guests           = models.PositiveIntegerField(default=1)
    table_preference = models.CharField(max_length=20, choices=TABLE_CHOICES, default='any')
    occasion         = models.CharField(max_length=20, choices=OCCASION_CHOICES, blank=True)
    notes            = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at       = models.DateTimeField(auto_now_add=True)
    table_number     = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.full_name} – {self.date} at {self.time} ({self.guests} guests)"


#Cart

class Cart(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart – {self.user.username}"


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    dish     = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.dish.price * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.dish.name}"

#Orders

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready',     'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total      = models.DecimalField(max_digits=10, decimal_places=2)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} – {self.user.username} ({self.status})"


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish       = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.dish.name} (Order #{self.order.id})"