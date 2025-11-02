from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from .models import Item,InventoryItem
from .serializers import ItemSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connection
from inventory.forms import InventoryItemForm
from django.contrib.auth import authenticate, login
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta,datetime
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from datetime import timedelta
from decimal import Decimal
from rest_framework.parsers import FormParser, MultiPartParser







class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]



from django.shortcuts import redirect
from rest_framework import generics
from django.contrib.auth import login

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 201:  # ✅ Check if user was created successfully
            username = request.data.get('username')
            user = User.objects.get(username=username)

            # 🔒 Store user session (automatic login)
            request.session['user_id'] = user.id
            request.session['username'] = user.username  # Optional: Store username

            return redirect('inventory_list')  # 🔄 Redirect to home page

        return response


# API View for Login
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate

class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # Handle form data
        if request.content_type == 'application/x-www-form-urlencoded':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user:
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                return redirect('inventory_list')
            else:
                # Handle invalid login
                return redirect('login_template')  # Or render with error

        # Handle JSON data
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:  # If login is successful
            username = request.data.get('username')
            user = authenticate(username=username, password=request.data.get('password'))
            
            if user:
                request.session['user_id'] = user.id  # Store user ID in session
                request.session['username'] = user.username  # Optional: Store username
                
            return redirect('inventory_list')  # Redirect to home page
        
        return response


# Template View for Registration Form
class RegisterTemplateView(TemplateView):
    template_name = 'inventory/register.html'

# Template View for Login Form
class LoginTemplateView(TemplateView):
    template_name = 'inventory/login.html'

from django.shortcuts import redirect

def logout_view(request):
    request.session.flush()  # ❌ Clear session (logs the user out)
    return redirect('login_template')  # 🔄 Redirect to login page


from django.shortcuts import render, redirect
from django.db import connection
import json
from datetime import datetime, timedelta

def home(request):
    """Dashboard home view displaying sales data, expiry data, and category-wise sales."""
    
    # 🔒 Check if user is authenticated using session
    if not request.session.get('user_id'):  
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)

    # 1️⃣ Fetch Total Sales for the Current Month
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT SUM(total_price) FROM customer_bill 
            WHERE TO_CHAR(current_date, 'YYYY-MM') = TO_CHAR(NOW(), 'YYYY-MM')
        """)
        total_sales = cursor.fetchone()[0] or 0  # If no sales, default to 0

    # 2️⃣ Fetch Inventory Expiry Data
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM inventory_items WHERE expiration_date < %s", [today])
        expired_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventory_items WHERE expiration_date BETWEEN %s AND %s", [today, next_month])
        expiring_items_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM inventory_items WHERE expiration_date > %s", [next_month])
        after_one_month_count = cursor.fetchone()[0]

    expiry_data = {
        "Expired": expired_count,
        "Expiring Soon": expiring_items_count,
        "Safe Stock": after_one_month_count
    }

    # 3️⃣ Fetch Monthly Sales Data for Charts
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT TO_CHAR(current_date, 'YYYY-MM') AS month, SUM(total_price) 
            FROM customer_bill 
            GROUP BY month 
            ORDER BY month
        """)
        monthly_sales = cursor.fetchall()
    sales_data = {row[0]: float(row[1]) for row in monthly_sales}

    # 4️⃣ Fetch Category-wise Sales Data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT i.category, SUM(b.total_price) 
            FROM customer_bill b
            JOIN inventory_items i ON b.item_id = i.item_id
            GROUP BY i.category 
            ORDER BY SUM(b.total_price) DESC
        """)
        category_sales = cursor.fetchall()
    category_sales_data = {row[0]: float(row[1]) for row in category_sales}

    # 5️⃣ Fetch All Categories for Dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT category FROM inventory_items")
        categories = [row[0] for row in cursor.fetchall()]

    return render(request, 'inventory/home.html', {
        'total_sales': total_sales,
        'expiring_items_count': expiring_items_count,
        'sales_data': json.dumps(sales_data),  # JSON format for charts
        'expiry_data': json.dumps(expiry_data),
        'category_sales_data': json.dumps(category_sales_data),
        'all_categories': categories  # Dropdown categories
    })

def get_top_products(request):
    category = request.GET.get('category', None)
    if not category:
        return JsonResponse({}, safe=False)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT i.item_name, SUM(b.total_price) 
            FROM customer_bill b
            JOIN inventory_items i ON b.item_id = i.item_id
            WHERE i.category = %s 
            GROUP BY i.item_name ORDER BY SUM(b.total_price) DESC LIMIT 5
        """, [category])
        product_sales = cursor.fetchall()

    product_sales_data = {row[0]: float(row[1]) for row in product_sales}
    return JsonResponse(product_sales_data, safe=False)

def monthly_sales_details(request, month):
    """Fetch and return total sales for a given month."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT SUM(total_price) FROM customer_bill 
            WHERE TO_CHAR(current_date, 'YYYY-MM') = %s
        """, [month])
        total_sales = cursor.fetchone()[0] or 0

    return JsonResponse({"month": month, "total_sales": total_sales})

def add_inventory_item(request):
    if not request.session.get('user_id'):  
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO inventory_items (item_name, category, quantity, unit, price, expiration_date, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, [
                    data['item_name'],
                    data['category'],
                    data['quantity'],
                    data['unit'],
                    data['price'],
                    data['expiration_date']
                ])
            return redirect('inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'inventory/add_inventory_item.html', {'form': form})




def inventory_list(request):
    if not request.session.get('user_id'):  
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)
    # Define Bootstrap color classes
    color_classes = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']

    # Fetch distinct categories
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT category FROM inventory_items")
        categories = [row[0] for row in cursor.fetchall()]

    categories_with_colors = [
        (category, color_classes[i % len(color_classes)]) for i, category in enumerate(categories)
    ]

    # Get filters from request
    selected_category = request.GET.get('category', '')
    show_expired = request.GET.get('expired', '')
    show_near_expiry = request.GET.get('near_expiry', '')
    show_after_one_month = request.GET.get('after_one_month', '')

    # Date calculations
    today = now().date()
    next_month = today + timedelta(days=30)

    # SQL query adjustment based on filters
    if show_expired:
        query = """
            SELECT item_id, item_name, category, quantity, unit, price, expiration_date 
            FROM inventory_items 
            WHERE expiration_date < %s
        """
        params = [today]  # Expired items

    elif show_near_expiry:
        query = """
            SELECT item_id, item_name, category, quantity, unit, price, expiration_date 
            FROM inventory_items 
            WHERE expiration_date BETWEEN %s AND %s
        """
        params = [today, next_month]  # Items expiring in the next month

    elif show_after_one_month:
        query = """
            SELECT item_id, item_name, category, quantity, unit, price, expiration_date 
            FROM inventory_items 
            WHERE expiration_date > %s
        """
        params = [next_month]  # Items expiring after one month

    elif selected_category:
        query = """
            SELECT item_id, item_name, category, quantity, unit, price, expiration_date 
            FROM inventory_items 
            WHERE category = %s
        """
        params = [selected_category]

    else:
        query = """
            SELECT item_id, item_name, category, quantity, unit, price, expiration_date 
            FROM inventory_items
        """
        params = []  # No filters applied

    # Fetch items using raw SQL SELECT statement
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        items = cursor.fetchall()

    # Structure items for rendering in the template
    items = [
        {
            'id': row[0],
            'item_name': row[1],
            'category': row[2],
            'quantity': row[3],
            'unit': row[4],
            'price': row[5],
            'expiration_date': row[6],
        }
        for row in items
    ]

    return render(request, 'inventory/inventory_list.html', {
        'categories_with_colors': categories_with_colors,
        'selected_category': selected_category,
        'items': items,
        'show_expired': show_expired,  
        'show_near_expiry': show_near_expiry,  
        'show_after_one_month': show_after_one_month,
    })



def update_inventory_item(request, item_id):
    if not request.session.get('user_id'):  
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)    
    # Fetch the specific item using the provided `item_id`
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM inventory_items WHERE item_id = %s", [item_id])
        row = cursor.fetchone()

    if not row:
        return HttpResponse("Item not found", status=404)

    # Convert the row data to a dictionary for the form
    item_data = {
        'item_name': row[1],
        'category': row[2],
        'quantity': row[3],
        'unit': row[4],
        'price': row[5],
        'expiration_date': row[6],
    }

    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Update the item in the database
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE inventory_items 
                    SET item_name = %s, category = %s, quantity = %s, unit = %s, price = %s, expiration_date = %s, updated_at = NOW()
                    WHERE item_id = %s
                """, [
                    data['item_name'],
                    data['category'],
                    data['quantity'],
                    data['unit'],
                    data['price'],
                    data['expiration_date'],
                    item_id
                ])
            return redirect('inventory_list')
    else:
        form = InventoryItemForm(initial=item_data)

    return render(request, 'inventory/update_inventory_item.html', {'form': form})

def delete_inventory_item(request, item_id):
    # Delete the inventory item with the given item_id
    with connection.cursor() as cursor:
        # Delete the specific record
        cursor.execute("DELETE FROM inventory_items WHERE item_id = %s", [item_id])
        
        # Reorder IDs to maintain sequential order
        cursor.execute("""
            WITH reordered AS (
                SELECT item_id, ROW_NUMBER() OVER (ORDER BY item_id) AS new_id
                FROM inventory_items
            )
            UPDATE inventory_items
            SET item_id = reordered.new_id
            FROM reordered
            WHERE inventory_items.item_id = reordered.item_id;
        """)

        # Reset the AUTO_INCREMENT/SEQUENCE value
        cursor.execute("SELECT setval(pg_get_serial_sequence('inventory_items', 'item_id'), MAX(item_id)) FROM inventory_items")
        
    return redirect('inventory_list')



def bill_form(request):
    if not request.session.get('user_id'):  
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)    
    return render(request, 'inventory/bill_form.html')


@csrf_exempt
def save_bill(request):
    if not request.session.get('user_id'):  
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)    
    """Save bill details, check for expired items, deduct stock, and return bill_number."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name = data.get('customer_name')
            phno = data.get('phno')
            current_date = datetime.now().strftime('%Y-%m-%d')

            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(bill_number), 0) + 1 FROM customer_bill")
                new_bill_number = cursor.fetchone()[0]

                for item in data.get('items', []):
                    item_id = int(item.get('itemid', 0))
                    quantity = int(item.get('quantity', 0))

                    # Check if item is expired
                    cursor.execute("SELECT expiration_date FROM inventory_items WHERE item_id = %s", [item_id])
                    expiration_date = cursor.fetchone()[0]

                    if expiration_date and expiration_date < datetime.today().date():
                        return JsonResponse({'error': f'Item ID {item_id} is expired and cannot be sold!'}, status=400)

                    # Insert bill record
                    cursor.execute("""
                        INSERT INTO customer_bill (customer_name, phno, item_id, quantity, price, total_price, "current_date", bill_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        customer_name,
                        phno,
                        item_id,
                        quantity,
                        float(item.get('price', 0)),
                        float(item.get('totalprice', 0)),
                        current_date,
                        new_bill_number  
                    ])

                    # Deduct the quantity from inventory
                    cursor.execute("""
                        UPDATE inventory_items 
                        SET quantity = quantity - %s 
                        WHERE item_id = %s AND quantity >= %s
                    """, [quantity, item_id, quantity])

                    # Check if stock went negative
                    cursor.execute("SELECT quantity FROM inventory_items WHERE item_id = %s", [item_id])
                    new_quantity = cursor.fetchone()[0]
                    if new_quantity < 0:
                        return JsonResponse({'error': f'Not enough stock for item ID {item_id}!'}, status=400)

            return JsonResponse({'message': 'Bill saved successfully!', 'bill_number': new_bill_number}, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error inserting bill: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)




def get_item_details(request, item_id):

    """Fetch item details including available quantity and expiration date from inventory_items."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT item_name, category, price, quantity, expiration_date 
            FROM inventory_items 
            WHERE item_id = %s
        """, [item_id])
        item = cursor.fetchone()

        if item:
            return JsonResponse({
                'item_name': item[0],
                'category': item[1],
                'price': item[2],
                'quantity': item[3],  # Available stock
                'expiration_date': item[4].strftime('%Y-%m-%d')  # Convert date to string format
            })
        else:
            return JsonResponse({'error': 'Item not found'}, status=404)



from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.db import connection
from django.core.mail import send_mail
from django.conf import settings

def bill_page(request, bill_number=None):
    if not request.session.get('user_id'):
        return redirect('login_template')  # Redirect to login if session does not exist

    today = datetime.today().date()
    next_month = today + timedelta(days=30)

    # Get bill_number from query parameters if available
    bill_number = request.GET.get("bill_number", bill_number)

    if not bill_number:  # No bill number provided
        return render(request, "inventory/bill_page.html", {"bill": None})

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cb.customer_name, cb.phno, cb.item_id, ii.item_name, ii.category,
                   cb.quantity, cb.price, cb.total_price, cb.current_date
            FROM customer_bill cb
            JOIN inventory_items ii ON cb.item_id = ii.item_id
            WHERE cb.bill_number = %s
        """, [bill_number])
        bill_details = cursor.fetchall()

    if not bill_details:
        return render(request, "inventory/bill_page.html", {"error": "Bill not found.", "bill": None})

    total_quantity = sum(row[5] for row in bill_details)
    total_amount = sum(row[7] for row in bill_details)

    bill_data = {
        "bill_number": bill_number,
        "customer_name": bill_details[0][0],
        "phno": bill_details[0][1],
        "items": [
            {"item_id": row[2], "item_name": row[3], "category": row[4], "quantity": row[5], "price": row[6], "total_price": row[7]}
            for row in bill_details
        ],
        "date": bill_details[0][8],
        "total_quantity": total_quantity,
        "total_amount": total_amount
    }

    # Send bill via email if requested
    if request.method == 'POST' and 'send_email' in request.POST:
        customer_email = request.POST.get('customer_email')
        if customer_email:
            subject = f"Bill #{bill_number} - {bill_data['customer_name']}"
            message = f"""
            Dear {bill_data['customer_name']},

            Here is your bill details:

            Bill Number: {bill_number}
            Date: {bill_data['date']}
            Phone: {bill_data['phno']}

            Items:
            """
            for item in bill_data['items']:
                message += f"- {item['item_name']} ({item['category']}): {item['quantity']} x {item['price']} = {item['total_price']}\n"

            message += f"""
            Total Quantity: {total_quantity}
            Total Amount: {total_amount}

            Thank you for your business!
            """

            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [customer_email],
                    fail_silently=False,
                )
                bill_data['email_sent'] = True
            except Exception as e:
                bill_data['email_error'] = str(e)

    return render(request, "inventory/bill_page.html", {"bill": bill_data})

