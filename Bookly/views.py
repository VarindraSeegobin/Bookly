from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from .forms import AccountForm
from Auth.models import User, Cart, CartItem, Book

def account_view(request):
    user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        form = AccountForm(request.POST, instance=user) if user else AccountForm(request.POST)

        if form.is_valid():
            account_data = form.cleaned_data

            if user:
                # Update logged-in user details
                form.save()
                messages.success(request, 'Your details have been updated successfully.')
            else:
                # Check if user exists, if not, create new user
                existing_user = User.objects.filter(email=account_data['email']).first()

                if existing_user:
                    login(request, existing_user)
                    messages.success(request, 'Welcome back! You have been logged in.')
                else:
                    new_user = User.objects.create(
                        username=account_data['email'],
                        email=account_data['email'],
                        first_name=account_data['first_name'],
                        last_name=account_data['last_name']
                    )
                    new_user.set_unusable_password()  # Since there's no password yet
                    new_user.save()
                    login(request, new_user)
                    messages.success(request, 'Details saved. Account created and logged in successfully.')

            return redirect('account')

    else:
        form = AccountForm(instance=user) if user else AccountForm()

    return render(request, 'Auth/account.html', {"form": form, "user": user})


def cart_view(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to access your cart.")
        return redirect("account")  # Change "account" to the actual URL name of your login page

    user = request.user
    cart, created = Cart.objects.get_or_create(user=user)
    cart_items = CartItem.objects.filter(cart=cart)

    # Group cart items by subject
    subjects = {}
    for item in cart_items:
        print(f"Item: {item}, Content Type: {item.content_type}, Object: {item.content_object}")
        if isinstance(item.content_object, Book):
            for subject in item.content_object.subjects.all():
                if subject not in subjects:
                    subjects[subject] = []
                subjects[subject].append(item)

    # Handle item removal
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        return redirect("cart")  # Redirect to refresh cart

    return render(request, "Auth/cart.html", {"subjects": subjects, "cart_items": cart_items})


def add_to_cart(request, content_type_id, object_id):
    if request.method == "POST":
        try:
            # Ensure content type exists
            content_type = get_object_or_404(ContentType, id=content_type_id)

            # Ensure the item exists
            model_class = content_type.model_class()
            item = get_object_or_404(model_class, id=object_id)

            # Retrieve or create the user's cart
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Ensure `cart` is associated properly
            if created:
                print(f"New cart created for user {request.user.id}")

            # Retrieve or create the cart item for this product
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                content_type=content_type,
                object_id=object_id,
                defaults={"quantity": 1}
            )

            if not item_created:
                # If the item exists, increase quantity atomically
                CartItem.objects.filter(id=cart_item.id).update(quantity=cart_item.quantity + 1)
                cart_item.refresh_from_db()  # Refresh to get updated quantity

            return JsonResponse({
                "success": True,
                "message": "Item added to cart!",
                "cart_id": cart.id,  # Ensure correct cart association
                "cart_item_id": cart_item.id,
                "quantity": cart_item.quantity
            })

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)



