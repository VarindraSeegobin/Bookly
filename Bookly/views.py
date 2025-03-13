from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from .forms import AccountForm
from Auth.models import User, Cart, CartItem, Book, Stationary


def account_view(request):
    user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        form = AccountForm(request.POST, instance=user) if user else AccountForm(request.POST)

        if form.is_valid():
            account_data = form.cleaned_data
            existing_user = User.objects.filter(email=account_data['email']).first()

            if existing_user:
                if not user:
                    authenticated_user = authenticate(request, username=existing_user.username, password=None)
                    if authenticated_user:
                        login(request, authenticated_user)
                        messages.success(request, 'Welcome back! You have been logged in.')
                        merge_session_cart(request, authenticated_user)  # Merge session cart

                # Update existing user details
                existing_user.first_name = account_data['first_name']
                existing_user.last_name = account_data['last_name']
                existing_user.save()

            else:
                # Create a new user and log them in
                new_user = User.objects.create(
                    username=account_data['email'],
                    email=account_data['email'],
                    first_name=account_data['first_name'],
                    last_name=account_data['last_name']
                )
                new_user.set_unusable_password()
                new_user.save()
                login(request, new_user)
                messages.success(request, 'Account created successfully. You are now logged in.')
                merge_session_cart(request, new_user)  # Merge session cart

            return redirect('account')

    else:
        form = AccountForm(instance=user) if user else AccountForm()

    return render(request, 'Auth/account.html', {"form": form, "user": user})


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

        if isinstance(content_obj, Book):
            for subject in content_obj.subjects.all():
                if subject not in books_by_subject:
                    books_by_subject[subject] = []
                books_by_subject[subject].append(item)
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
