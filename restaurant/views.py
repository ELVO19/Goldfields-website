from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
import json
from django.http import JsonResponse
from django.utils import timezone
from django_daraja.mpesa.core import MpesaClient
from .models import Dish, Payment, Reservation,Cart, CartItem, Order, OrderItem


@login_required
def index(request):
    dishes = Dish.objects.all()
    return render(request, "index.html")


@login_required
def admin_page(request):
    if not request.user.is_superuser:
        return HttpResponse("You are not authorized to view this page.")
    dishes = Dish.objects.all()
    return render(request, "admin_page.html", {"dishes": dishes})


def contact(request):
    return render(request, "contact.html")


def menu(request):
    dishes = Dish.objects.all()
    return render(request, "menu.html", {"dishes": dishes})


def add_dish(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        Dish.objects.create(
            name=name,
            description=description,
            price=price,
            image=image
        )
        return redirect("admin_page")

    return render(request, "add_dish.html")


def update_dish(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)

    if request.method == "POST":
        dish.name = request.POST.get("name")
        dish.description = request.POST.get("description")
        dish.price = request.POST.get("price")

        if request.FILES.get("image"):
            dish.image = request.FILES.get("image")

        dish.save()
        return redirect("admin_page")

    return render(request, "update_dish.html", {"dish": dish})


def delete_dish(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)

    if request.method == "POST":
        dish.delete()

    return redirect("admin_page")


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        login(request, user)
        return redirect("index")

    return render(request, "signup.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect("admin_page")
            else:
                return redirect("index")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect("login")


def payment(request, id):
    dish = get_object_or_404(Dish, id=id)

    if request.method == 'POST':
        phone = request.POST.get('phone')

        if not phone:
            messages.error(request, 'Please enter your phone number in format 2547XXXXXXXX.')
            return render(request, 'payment.html', {'dish': dish})

        amount = int(dish.price)

        try:
            client = MpesaClient()
            callback_url = 'https://mydomain.com/mpesa/callback/'

            response = client.stk_push(
                phone_number=phone,
                amount=amount,
                account_reference=f"Order{dish.id}",
                transaction_desc=f"Payment for {dish.name}",
                callback_url=callback_url
            )

            check_request_id = None
            if isinstance(response, dict):
                check_request_id = response.get('CheckoutRequestID')
            elif hasattr(response, 'CheckoutRequestID'):
                check_request_id = response.CheckoutRequestID

            Payment.objects.create(
                user=request.user,
                phone=phone,
                amount=amount,
                check_request_id=check_request_id,
                status='Pending'
            )
            messages.success(request, 'STK push sent! Check your phone to complete payment.')

        except Exception as e:
            messages.error(request, f'Payment failed: {str(e)}')

    return render(request, 'payment.html', {'dish': dish})


def reservation(request):
    if request.method == 'POST':
        full_name        = request.POST.get('full_name', '').strip()
        phone            = request.POST.get('phone', '').strip()
        email            = request.POST.get('email', '').strip()
        date             = request.POST.get('date')
        time             = request.POST.get('time')
        guests           = request.POST.get('guests', 1)
        table_preference = request.POST.get('table_preference', 'any')
        table_number     = request.POST.get('table_number', 1)
        occasion         = request.POST.get('occasion', '')
        notes            = request.POST.get('notes', '').strip()

        if not full_name or not phone or not date or not time:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'reservation.html')

        Reservation.objects.create(
            user             = request.user if request.user.is_authenticated else None,
            full_name        = full_name,
            phone            = phone,
            email            = email,
            date             = date,
            time             = time,
            guests           = int(guests),
            table_preference = table_preference,
            table_number     = int(table_number),
            occasion         = occasion,
            notes            = notes,
            status           = 'pending',
        )

        messages.success(request, 'Reservation confirmed! We look forward to hosting you.')
        return redirect('reservation_success')

    # GET — build table availability for today
    today = timezone.now().date()
    today_reservations = Reservation.objects.filter(
        date=today
    ).exclude(status='cancelled')
    table_map = {r.table_number: r for r in today_reservations}

    tables = []
    for n in range(1, 11):  # T1–T10
        res = table_map.get(n)
        state = 'available' if not res else ('reserved' if res.status == 'confirmed' else 'pending')
        tables.append({'number': n, 'state': state})

    return render(request, 'reservation.html', {'tables': tables})


def reservation_success(request):
    return render(request, 'reservation_success.html')


TOTAL_TABLES = 30


def admin_reservations(request):
    if not request.user.is_superuser:
        return HttpResponse("You are not authorized to view this page.")

    status_filter    = request.GET.get('status', 'all')
    all_reservations = Reservation.objects.all().order_by('-created_at')

    total_count     = all_reservations.count()
    pending_count   = all_reservations.filter(status='pending').count()
    confirmed_count = all_reservations.filter(status='confirmed').count()
    cancelled_count = all_reservations.filter(status='cancelled').count()

    if status_filter in ['pending', 'confirmed', 'cancelled']:
        reservations = all_reservations.filter(status=status_filter)
    else:
        reservations = all_reservations

    today = timezone.now().date()
    today_reservations = Reservation.objects.filter(
        date=today
    ).exclude(status='cancelled')
    table_map = {r.table_number: r for r in today_reservations}

    tables = []
    for n in range(1, TOTAL_TABLES + 1):
        res = table_map.get(n)
        if res:
            tables.append({
                'number': n,
                'state':  'reserved' if res.status == 'confirmed' else 'pending',
                'guest':  res.full_name,
                'time':   res.time,
            })
        else:
            tables.append({'number': n, 'state': 'available', 'guest': None, 'time': None})

    return render(request, 'admin_reservations.html', {
        'tables':          tables,
        'reservations':    reservations,
        'status_filter':   status_filter,
        'total_count':     total_count,
        'pending_count':   pending_count,
        'confirmed_count': confirmed_count,
        'cancelled_count': cancelled_count,
    })


def update_reservation_status(request, reservation_id):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized")

    if request.method == 'POST':
        res = get_object_or_404(Reservation, id=reservation_id)
        new_status = request.POST.get('status')
        if new_status in ['pending', 'confirmed', 'cancelled']:
            res.status = new_status
            res.save()

    return redirect('admin_reservations')


def reports(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized")
    return render(request, 'reports.html')

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})


@login_required
def add_to_cart(request, dish_id):
    if request.method != 'POST':
        return redirect('menu')

    dish     = get_object_or_404(Dish, id=dish_id)
    cart, _  = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    item, created = CartItem.objects.get_or_create(cart=cart, dish=dish)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success':    True,
            'item_count': cart.item_count,
            'message':    f'{dish.name} added to cart',
        })

    messages.success(request, f'{dish.name} added to cart!')
    return redirect('menu')


@login_required
def update_cart(request, item_id):
    item     = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = item.cart if quantity > 0 else Cart.objects.get(user=request.user)
        return JsonResponse({
            'success':    True,
            'item_count': cart.item_count,
            'cart_total': str(cart.total),
        })

    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({
            'success':    True,
            'item_count': cart.item_count,
            'cart_total': str(cart.total),
        })

    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        phone = request.POST.get('phone', '').strip()

        # Create the Order
        order = Order.objects.create(
            user=request.user,
            total=cart.total,
            notes=notes,
            status='pending',
        )

        # Copy cart items into OrderItems
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                dish=cart_item.dish,
                quantity=cart_item.quantity,
                unit_price=cart_item.dish.price,
            )

        # Trigger M-Pesa STK push if phone provided
        if phone:
            try:
                client = MpesaClient()
                callback_url = 'https://mydomain.com/mpesa/callback/'
                amount = int(order.total)
                response = client.stk_push(
                    phone_number=phone,
                    amount=amount,
                    account_reference=f"Order{order.id}",
                    transaction_desc=f"Nexxa Hotels Order #{order.id}",
                    callback_url=callback_url,
                )

                check_request_id = None
                if isinstance(response, dict):
                    check_request_id = response.get('CheckoutRequestID')
                elif hasattr(response, 'CheckoutRequestID'):
                    check_request_id = response.CheckoutRequestID

                Payment.objects.create(
                    user=request.user,
                    phone=phone,
                    amount=amount,
                    check_request_id=check_request_id,
                    status='Pending',
                )
                messages.success(request, 'STK push sent! Check your phone to complete payment.')
            except Exception as e:
                messages.error(request, f'Payment initiation failed: {str(e)}')

        # Clear the cart
        cart.items.all().delete()

        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'checkout.html', {'cart': cart})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})


@login_required
def cart_item_count(request):
    """AJAX endpoint – returns live badge count."""
    try:
        count = request.user.cart.item_count
    except Cart.DoesNotExist:
        count = 0
    return JsonResponse({'count': count})

from django.db.models import Sum
from .models import Payment, Order, Reservation

def report(request):
    payments = Payment.objects.select_related('user').all().order_by('-created_at')
    return render(request, 'report.html', {
        'payments': payments,
        'payments_total': payments.filter(status='Confirmed').aggregate(t=Sum('amount'))['t'] or 0,
        'pending_payments': payments.filter(status='Pending').count(),
        'orders': Order.objects.select_related('user').prefetch_related('items__dish').order_by('-created_at'),
        'reservations': Reservation.objects.all().order_by('-created_at'),
    })