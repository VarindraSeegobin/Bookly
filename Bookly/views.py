import decimal
import json
import boto3
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.core.mail import EmailMessage
from .forms import AccountForm
from Auth.models import User, Cart, CartItem, Book, Stationary, Order, OrderBook, OrderStationary, Subject
import datetime
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
import qrcode
import os
from django.contrib.auth.decorators import login_required



def account_view(request):
    user = request.user if request.user.is_authenticated else None
    orders = Order.objects.filter(user=user).order_by('-date_time_placed') if user else []

    # Process order costs if the user is authenticated and there are orders
    if orders:
        for order in orders:
            order.order_books = OrderBook.objects.filter(order=order)
            order.order_stationary = OrderStationary.objects.filter(order=order)

            total_books_cost = order.order_books.aggregate(
                total_cost=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('book__cost'),
                        output_field=DecimalField()
                    )
                )
            )['total_cost'] or 0

            total_stationary_cost = order.order_stationary.aggregate(
                total_cost=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('stationary__cost'),
                        output_field=DecimalField()
                    )
                )
            )['total_cost'] or 0

            order.total_cost = total_books_cost + total_stationary_cost

    if request.method == 'POST':
        form = AccountForm(request.POST)

        if form.is_valid():
            account_data = form.cleaned_data
            existing_user = User.objects.filter(email=account_data['email']).first()

            if existing_user:
                # Log the existing user in if they exist (even without a password)
                login(request, existing_user)
                messages.success(request, 'Welcome back! You have been logged in.')
                merge_session_cart(request, existing_user)
            else:
                # Create a new user and log them in
                new_user = User.objects.create(
                    username=account_data['email'],
                    email=account_data['email'],
                    first_name=account_data['first_name'],
                    last_name=account_data['last_name'],
                    school=account_data['school']
                )
                new_user.set_unusable_password()  # No password used
                new_user.save()
                login(request, new_user)
                messages.success(request, 'Account created successfully. You are now logged in.')
                merge_session_cart(request, new_user)

            return redirect('account')  # Redirect to the account page after processing the form

    else:
        # Prepopulate the form with the current user's details if authenticated
        if user:
            form = AccountForm(initial={
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'school': user.school if user.school else None  # Handle case if no school is set
            })
        else:
            form = AccountForm()  # Don't pass an instance here as we want to handle new user creation
    cart_is_full = Cart.objects.filter(user=user).exists()
    return render(request, 'Auth/account.html', {"form": form, "user": user, "orders": orders, "cart_is_full": cart_is_full})


def merge_session_cart(request, user):
    """
    Merges the session cart with the authenticated user's cart upon login.
    """
    session_cart = request.session.get('cart', {})

    if session_cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        for key, quantity in session_cart.items():
            content_type_id, object_id = map(int, key.split('-'))
            content_type = get_object_or_404(ContentType, id=content_type_id)
            model_class = content_type.model_class()
            item = get_object_or_404(model_class, id=object_id)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, content_type=content_type, object_id=object_id,
                defaults={"quantity": quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

        # Clear session cart after merging
        del request.session['cart']
        request.session.modified = True





def cart_view(request):
    """
    Displays the cart for both authenticated and anonymous users.
    """
    user = request.user if request.user.is_authenticated else None
    cart_items = []
    total_cost = 0  # Initialize total cart cost

    if user:
        # Fetch items from the user's cart
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
    else:
        # Fetch items from the session
        session_cart = request.session.get('cart', {})
        for key, quantity in session_cart.items():
            content_type_id, object_id = map(int, key.split('-'))
            content_type = ContentType.objects.get(id=content_type_id)
            model_class = content_type.model_class()
            item = model_class.objects.get(id=object_id)
            if item not in cart_items:
                cart_items.append({
                    "id": key,  # Unique identifier for session item
                    "item": item,
                    "quantity": quantity,
                    "content_type": content_type
                })

    books_by_subject = {}
    stationary_items = []

    # Process cart items
    for item in cart_items:
        content_obj = item["item"] if isinstance(item, dict) else item.content_object
        quantity = item["quantity"] if isinstance(item, dict) else item.quantity
        added_books = set()
        if isinstance(content_obj, Book):
            if content_obj not in added_books:
                for subject in content_obj.subjects.all():
                    if subject not in books_by_subject:
                        books_by_subject[subject] = []
                    books_by_subject[subject].append(item)
                    added_books.add(content_obj)
        elif isinstance(content_obj, Stationary):
            stationary_items.append(item)

        # Calculate total cost
        total_cost += content_obj.cost * quantity

    if request.method == "POST":
        item_id = request.POST.get("item_id")
        if user:
            cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
            cart_item.delete()
        else:
            request.session['cart'].pop(item_id, None)
            request.session.modified = True

        return redirect("cart")
    return render(request, "Auth/cart.html", {
        "books_by_subject": books_by_subject,
        "stationary_items": stationary_items,
        "total_cost": total_cost
    })


@csrf_protect
def add_many_subjects(request):
    """
    Adds all books and stationaries related to given subjects to the cart.
    """
    subject_ids = request.GET.getlist("subject_ids")  # Extract subject IDs from query params
    subjects = Subject.objects.filter(id__in=subject_ids)  # Get valid subjects
    valid_subject_ids = subjects.values_list("id", flat=True)  # List of found subject IDs
    invalid_ids = set(subject_ids) - set(map(str, valid_subject_ids))  # Find invalid IDs

    # Get related books and stationaries
    books = Book.objects.filter(subjects__in=subjects).distinct()
    stationaries = Stationary.objects.filter(subjects__in=subjects).distinct()

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Add books to cart
        for book in books:
            content_type = ContentType.objects.get_for_model(Book)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, content_type=content_type, object_id=book.id, defaults={"quantity": 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()

        # Add stationaries to cart
        for stationary in stationaries:
            content_type = ContentType.objects.get_for_model(Stationary)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, content_type=content_type, object_id=stationary.id, defaults={"quantity": 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()

        messages.success(request, "Items added to cart!")
        return redirect("account")  # Redirect authenticated users to account page

    else:
        # Store in session
        session_cart = request.session.get('cart', {})

        # Add books to session cart
        for book in books:
            key = f"{ContentType.objects.get_for_model(Book).id}-{book.id}"
            session_cart[key] = session_cart.get(key, 0) + 1

        # Add stationaries to session cart
        for stationary in stationaries:
            key = f"{ContentType.objects.get_for_model(Stationary).id}-{stationary.id}"
            session_cart[key] = session_cart.get(key, 0) + 1

        request.session['cart'] = session_cart
        request.session.modified = True

        messages.info(request, "Items added to cart! Add your details above and then go to the shopping cart to checkout.")
        return redirect("account")

@csrf_protect
def add_to_cart(request, content_type_id, object_id):
    """
    Allows adding items to the cart for both authenticated and anonymous users.
    """
    if request.method == "POST":
        content_type = get_object_or_404(ContentType, id=content_type_id)
        model_class = content_type.model_class()
        item = get_object_or_404(model_class, id=object_id)

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, content_type=content_type, object_id=object_id, defaults={"quantity": 1}
            )

            if not created:
                cart_item.quantity += 1
                cart_item.save()
        else:
            # Store in session
            session_cart = request.session.get('cart', {})
            key = f"{content_type_id}-{object_id}"

            if key in session_cart:
                session_cart[key] += 1
            else:
                session_cart[key] = 1

            request.session['cart'] = session_cart
            request.session.modified = True

        return JsonResponse({"success": True, "message": "Item added to cart!"})

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

def update_cart_ajax(request):
    """
    Handles AJAX requests to update cart items dynamically.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")
        action = data.get("action")
        is_authenticated = data.get("is_authenticated") == "true"

        quantity = 0  # Default quantity in case the item is removed

        if is_authenticated:
            # Logged-in user: Fetch from database
            user = request.user
            cart = Cart.objects.get(user=user)
            cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

            if action == "increase":
                cart_item.quantity += 1
            elif action == "decrease":
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                else:
                    cart_item.delete()
                    return JsonResponse({"status": "success", "quantity": 0})
            elif action == "remove":
                cart_item.delete()
                return JsonResponse({"status": "success", "quantity": 0})

            cart_item.save()
            quantity = cart_item.quantity

        else:
            # Guest user: Update session storage
            session_cart = request.session.get("cart", {})

            if item_id in session_cart:
                if action == "increase":
                    session_cart[item_id] += 1
                elif action == "decrease":
                    if session_cart[item_id] > 1:
                        session_cart[item_id] -= 1
                    else:
                        del session_cart[item_id]
                        request.session["cart"] = session_cart
                        request.session.modified = True
                        return JsonResponse({"status": "success", "quantity": 0})
                elif action == "remove":
                    del session_cart[item_id]
                    request.session["cart"] = session_cart
                    request.session.modified = True
                    return JsonResponse({"status": "success", "quantity": 0})

                request.session["cart"] = session_cart
                request.session.modified = True
                quantity = session_cart[item_id]

        return JsonResponse({"status": "success", "quantity": quantity})

    return JsonResponse({"status": "error"}, status=400)

def generate_qr_code(order: int):
    base_url = os.environ.get("QR_CODE_BASE_URL")
    base_url += str(order)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10,border=4)
    qr.add_data(base_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def upload_to_r2(file, filename):

    s3 = boto3.client(
        service_name='s3',
        region_name=os.environ.get('CLOUDFLARE_REGION'),
        endpoint_url=os.environ.get('CLOUDFLARE_ENDPOINT'),
        aws_access_key_id=os.environ.get('CLOUDFLARE_ACCESS_KEY'),
        aws_secret_access_key=os.environ.get('CLOUDFLARE_SECRET_KEY')
    )

    img_byes = io.BytesIO()
    file.save(img_byes, format='PNG')
    img_byes.seek(0)

    s3.upload_fileobj(img_byes, 'bookly', filename)

    return f"{os.environ.get('CLOUDFLARE_FIND_ENDPOINT')}/{filename}"




def send_order_email(user_email, order, order_items, total_cost):
    """
    Sends an order confirmation email with an embedded QR code.
    """
    subject = f"Order Confirmation - Order #{order.id}"

    order_details = f"""
    <p>Hello {order.user.first_name},</p>

    <p>Your order has been successfully placed.</p>

    <p><strong>Order ID:</strong> {order.id}<br>
    <strong>Date Placed:</strong> {order.date_time_placed.strftime('%Y-%m-%d %H:%M:%S')}<br>
    <strong>Total Cost:</strong> ${total_cost:.2f}</p>

    <p><strong>Items Ordered:</strong></p>
    <ul>
    """

    for item in order_items:
        order_details += f"<li>{item['name']} (Quantity: {item['quantity']}) - ${item['cost'] * item['quantity']:.2f}</li>"

    order_details += f"""
    </ul>
    <p>You can track your order or confirm your order using the QR code below:</p>
    <img src="{order.qr_code}" alt="QR Code" style="width:200px; height:200px;"/>

    <p>You can expect your order to arrive within the first week of school. Your order can either be picked up by your child or yourself. Thank you for shopping with us!</p>

    <p>Regards,</p>
    <p>The Bookly Team.</p>
    """

    # Create email and set content type to HTML
    email = EmailMessage(subject, order_details, to=[user_email])
    email.content_subtype = "html"  # Ensure HTML rendering

    # Send email
    email.send()



def checkout(request):
    if not request.user.is_authenticated:
        messages.info(request,
                      "You must provide these details before checking out. When finished, click Save Details and go back to your Cart.")
        return redirect("account")

    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart_page")

    subtotal = sum(item.content_object.cost * item.quantity for item in cart_items)
    tax = float(subtotal) * 0.1  # 10% tax
    subtotal = subtotal * decimal.Decimal(0.9)
    total = float(subtotal) + tax

    if request.method == "POST":
        # Create an order
        order = Order.objects.create(
            user=request.user,
            date_time_placed=datetime.datetime.now(),
            date_time_paid=None,
            paid_for=False,
            total=total
        )

        qr_code = generate_qr_code(order.id)
        filename = f"{request.user.email}_order_id_{order.id}.png"
        url = upload_to_r2(qr_code, filename)
        order.qr_code = url
        order.save()

        order_items_list = []  # List to store order details for the email

        # Add items to order
        for item in cart_items:
            if isinstance(item.content_object, Book):
                OrderBook.objects.create(order=order, book=item.content_object, quantity=item.quantity)
            elif isinstance(item.content_object, Stationary):
                OrderStationary.objects.create(order=order, stationary=item.content_object, quantity=item.quantity)

            order_items_list.append({
                "name": item.content_object.title,
                "quantity": item.quantity,
                "cost": item.content_object.cost
            })

        # Clear the cart
        cart_items.delete()

        # Send order confirmation email
        send_order_email(request.user.email, order, order_items_list, total)

        messages.success(request, "Your order has been placed successfully.")
        return redirect("account")

    return render(request, "Auth/checkout.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    })

def confirm_email(order):
    """Sends an order confirmation email to the user."""
    subject = f"Order Confirmation - Order #{order.id}"
    user_email = order.user.email
    order_details = f"""
        <html>
        <body>
            <p>Dear {order.user.first_name},</p>
            <p>Your order <strong>#{order.id}</strong> has been successfully confirmed and paid for.</p>
            <p>You will receive further updates when your order is shipped.</p>
            <br>
            <p>Thank you for supporting the Bookly mission!</p>
        </body>
        </html>
    """

    # Send email
    email = EmailMessage(subject, order_details, to=[user_email])
    email.content_subtype = "html"  # Ensure HTML rendering
    email.send()

@login_required
def view_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Ensure only the order owner or a superuser can access the order
    if request.user != order.user and not request.user.is_superuser:
        return redirect("account")  # Redirect unauthorized users

    # If superuser confirms payment
    if request.user.is_superuser and request.method == "POST":
        confirmation = request.POST.get("confirmation")
        if confirmation == "confirm":
            order.paid_for = True
            order.date_time_paid = datetime.datetime.now()


            for order_book in OrderBook.objects.filter(order=order):
                book = order_book.book
                book.quantity += order_book.quantity
                book.save()

            for order_stationary in OrderStationary.objects.filter(order=order):
                stationary = order_stationary.stationary
                stationary.quantity += order_stationary.quantity
                stationary.save()

            order.save()

            # Send confirmation email
            confirm_email(order)

            return redirect("view_order", order_id=order.id)  # Refresh page
        else:
            messages.error(request, "Please confirm payment before submitting.")

    context = {
        "order": order,
        "books": order.books.all(),
        "stationary": order.stationary.all(),
        "is_superuser": request.user.is_superuser,
    }
    return render(request, "Admin/view_order.html", context)