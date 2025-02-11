from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import ProductDetails, CartItems, UserDetails, OrderDetails, Payment
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q

# Home Page View
def index(request):
    # Get user session data
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        user = UserDetails.objects.get(id=user_id)
    
    return render(request, 'index.html', {'user': user})

# Register Page View
def register(request):
    if request.method == 'POST':
        if 'signup' in request.POST:
            # Handle Sign Up
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            phone = request.POST['phone']

            try:
                # Check if username or email already exists
                if UserDetails.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists')
                    return render(request, 'register.html')
                
                if UserDetails.objects.filter(email=email).exists():
                    messages.error(request, 'Email already exists')
                    return render(request, 'register.html')

                # Create new user
                user = UserDetails(
                    username=username,
                    email=email,
                    password=make_password(password),
                    phone=phone
                )
                user.save()
                
                # Add user to session after successful registration
                request.session['user_id'] = user.id
                messages.success(request, 'Registration successful')
                return redirect('index')
            
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                return render(request, 'register.html')

        elif 'login' in request.POST:
            # Handle Login
            email = request.POST['email']
            password = request.POST['password']

            try:
                user = UserDetails.objects.get(email=email)
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    messages.success(request, 'Login successful')
                    return redirect('index')
                else:
                    messages.error(request, 'Invalid password')
            except UserDetails.DoesNotExist:
                messages.error(request, 'Email not found')
            
            return render(request, 'register.html')

    return render(request, 'register.html')

def product(request):
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        user = UserDetails.objects.get(id=user_id)
        cart_count = CartItems.objects.filter(user=user).count()
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Filter products based on search query
    if search_query:
        products = ProductDetails.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    else:
        products = ProductDetails.objects.all()
    
    context = {
        'products': products,
        'user': user,
        'cart_count': cart_count if user else 0,
        'search_query': search_query
    }
    
    return render(request, 'product.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(ProductDetails, id=product_id)
    return render(request, 'product_detail.html', {'product': product}) 

def cart(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to view your cart')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        cart_items = CartItems.objects.filter(user=user).select_related('product')
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        cart_count = cart_items.count()
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'cart_count': cart_count,
            'user': user
        }
        return render(request, 'cart.html', context)
    except UserDetails.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('register')

def add_to_cart(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please login to add items to cart')
            return redirect('register')
        
        product_id = request.POST.get('product_id')
        size = request.POST.get('size', 'M')  # Default size M if not specified
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            user = UserDetails.objects.get(id=user_id)
            product = ProductDetails.objects.get(id=product_id)
            
            # Check if item already in cart
            cart_item, created = CartItems.objects.get_or_create(
                user=user,
                product=product,
                size=size,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            messages.success(request, 'Item added to cart successfully')
            return redirect('cart')
            
        except Exception as e:
            messages.error(request, f'Error adding item to cart: {str(e)}')
            return redirect('product')
    
    return redirect('product')

def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        try:
            cart_item = CartItems.objects.get(id=item_id)
            if action == 'increase':
                cart_item.quantity += 1
            elif action == 'decrease' and cart_item.quantity > 1:
                cart_item.quantity -= 1
            cart_item.save()
        except CartItems.DoesNotExist:
            pass
    
    return redirect('cart')

def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        try:
            cart_item = CartItems.objects.get(id=item_id)
            cart_item.delete()
            messages.success(request, 'Item removed from cart')
        except CartItems.DoesNotExist:
            messages.error(request, 'Item not found in cart')
    
    return redirect('cart')

def signout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        messages.success(request, 'Logged out successfully')
    return redirect('index')

def search(request):
    query = request.GET.get('query', '')
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        user = UserDetails.objects.get(id=user_id)
        cart_count = CartItems.objects.filter(user=user).count()

    if query:
        # Try to find exact match first
        try:
            product = ProductDetails.objects.get(name__iexact=query)
            return redirect('product_detail', product_id=product.id)
        except ProductDetails.DoesNotExist:
            # If no exact match, look for similar products
            products = ProductDetails.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__icontains=query)
            )
            
            if products.count() == 1:
                # If only one product found, go directly to its details
                return redirect('product_detail', product_id=products.first().id)
            
            context = {
                'products': products,
                'query': query,
                'user': user,
                'cart_count': cart_count if user else 0,
                'no_results': products.count() == 0
            }
            return render(request, 'search_results.html', context)
    
    return redirect('product')

def checkout(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to checkout')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        cart_items = CartItems.objects.filter(user=user).select_related('product')
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
        
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        
        # Create order
        order = OrderDetails.objects.create(
            user=user,
            total_amount=total_price,
            status='Pending'
        )
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'order': order,
            'user': user,
            'cart_count': cart_items.count()
        }
        return render(request, 'checkout.html', context)
        
    except UserDetails.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('register')

def process_payment(request):
    if request.method != 'POST':
        return redirect('cart')
    
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to complete payment')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        order_id = request.POST.get('order_id')
        payment_method = request.POST.get('payment_method')
        
        order = OrderDetails.objects.get(id=order_id, user=user)
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            status='Completed' if payment_method == 'Cash On Delivery' else 'Pending'
        )
        
        # Clear the cart after successful order
        CartItems.objects.filter(user=user).delete()
        
        messages.success(request, 'Order placed successfully!')
        return redirect('product')  # Redirect to products page after successful payment
        
    except (UserDetails.DoesNotExist, OrderDetails.DoesNotExist):
        messages.error(request, 'Error processing payment')
        return redirect('cart') 

def my_orders(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to view your orders')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        orders = OrderDetails.objects.filter(user=user).order_by('-created_at')
        cart_count = CartItems.objects.filter(user=user).count()
        
        # Get payment details for each order
        orders_with_payments = []
        for order in orders:
            try:
                payment = Payment.objects.get(order=order)
                orders_with_payments.append({
                    'order': order,
                    'payment': payment
                })
            except Payment.DoesNotExist:
                orders_with_payments.append({
                    'order': order,
                    'payment': None
                })
        
        context = {
            'orders_with_payments': orders_with_payments,
            'user': user,
            'cart_count': cart_count
        }
        return render(request, 'my_orders.html', context)
        
    except UserDetails.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('register') 

def cancel_order(request, order_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to cancel order')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        order = OrderDetails.objects.get(id=order_id, user=user)
        
        if order.status != 'Pending':
            messages.error(request, 'Only pending orders can be cancelled')
            return redirect('my_orders')
        
        # Update order status
        order.status = 'Cancelled'
        order.save()
        
        # Update payment status if exists
        try:
            payment = Payment.objects.get(order=order)
            payment.status = 'Failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
        
        messages.success(request, 'Order cancelled successfully')
        return redirect('my_orders')
        
    except (UserDetails.DoesNotExist, OrderDetails.DoesNotExist):
        messages.error(request, 'Order not found')
        return redirect('my_orders') 

def delete_order(request, order_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to delete order')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        order = OrderDetails.objects.get(id=order_id, user=user)
        
        if order.status != 'Cancelled':
            messages.error(request, 'Only cancelled orders can be deleted')
            return redirect('my_orders')
        
        # Delete the order and its related payment
        order.delete()  # This will also delete related payment due to CASCADE
        
        messages.success(request, 'Order deleted successfully')
        return redirect('my_orders')
        
    except (UserDetails.DoesNotExist, OrderDetails.DoesNotExist):
        messages.error(request, 'Order not found')
        return redirect('my_orders') 

def about(request):
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        user = UserDetails.objects.get(id=user_id)
    
    return render(request, 'about.html', {'user': user}) 

def contact(request):
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        user = UserDetails.objects.get(id=user_id)
    
    return render(request, 'contact.html', {'user': user}) 

def profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to view profile')
        return redirect('register')
    
    try:
        user = UserDetails.objects.get(id=user_id)
        orders = OrderDetails.objects.filter(user=user).order_by('-created_at')[:5]  # Get last 5 orders
        return render(request, 'profile.html', {
            'user': user,
            'recent_orders': orders
        })
    except UserDetails.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('register') 