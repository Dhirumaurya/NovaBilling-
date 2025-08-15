import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
from num2words import num2words
import os
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont, ImageTk
import sys, os
import re




# Global user
current_user = ""
main_frame = None
selected_customers = set()
# Global shared data
metrics = {}
transactions = []
revenue_by_month = []

# Colors
colors = {
    'sidebar': '#2c3e50',
    'main_bg': '#f8f9fa',
    'card_green': '#10B981',
    'card_blue': '#3B82F6',
    'card_yellow': '#F59E0B',
    'card_red': '#EF4444',
    'white': '#ffffff',
    'text_dark': '#1f2937',
    'text_light': '#6b7280',
}

# Color schemec
PRIMARY_COLOR = "#1E3A8A"  # Deep blue
SECONDARY_COLOR = "#FFFFFF"  # White
ACCENT_COLOR = "#3B82F6"  # Bright blue
TEXT_COLOR = "#1F2937"  # Dark gray
BACKGROUND_COLOR = "#F3F4F6"
CARD_SHADOW = "#e5e7eb"# Light gray

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller .exe """
    try:
        base_path = sys._MEIPASS  # Temporary folder used by PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------------------- Database Setup ----------------------
import sqlite3

def create_company_db():
    try:
        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()

        # --- Customers Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                state_code TEXT,
                gstin TEXT
            )
        ''')

        # --- Items Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                stock INTEGER,
                price REAL
            )
        ''')


        # --- Revenue Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                date TEXT NOT NULL
            )
        ''')

        # --- Invoices Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                status TEXT CHECK(status IN ('pending', 'paid')) DEFAULT 'pending',
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')

        # --- Invoice Products Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (invoice_id) REFERENCES invoices_table(id),
                FOREIGN KEY (product_id) REFERENCES items(item_id)
            )
        ''')

        # --- Payments Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                amount REAL,
                method TEXT,
                date TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices_table(id)
            )
        ''')

        # --- Users/Admins Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        ''')

        # --- Settings Table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                gstin TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                logo_path TEXT
            )
        ''')

        conn.commit()
        conn.close()

       

    except sqlite3.Error as e:
        print(f"❌ Error creating tables in company.db: {e}")

# Call the function
create_company_db()

import sqlite3

def ensure_eway_bills_table():
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    # Create eway_bills table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eway_bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eway_bill TEXT,
            vehicle_no TEXT,
            p_marka TEXT,
            reverse_charges TEXT,
            invoice_no TEXT,
            transport_by TEXT,
            station TEXT
        )
    ''')

    conn.commit()
    conn.close()
 

ensure_eway_bills_table()


import sqlite3
from datetime import datetime

# ✅ Insert revenue amount with date
def insert_revenue(amount):
    date_str = datetime.now().strftime("%Y-%m-%d")  # Today's date in YYYY-MM-DD
    try:
        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()

        # Ensure table exists before insert (optional)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revenue_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                date TEXT NOT NULL
            )
        """)

        cursor.execute(
            "INSERT INTO revenue_table (amount, date) VALUES (?, ?)",
            (amount, date_str)
        )
        conn.commit()
        conn.close()
        print(f"✅ Revenue data inserted: ₹{amount:.2f} on {date_str}")
    except Exception as e:
        print("❌ Failed to insert revenue:", e)

# ✅ Fetch total revenue
def fetch_total_revenue():
    try:
        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(amount) FROM revenue_table")
        result = cursor.fetchone()
        total_revenue = result[0] if result and result[0] else 0

        conn.close()
        return total_revenue
    except Exception as e:
        print("❌ Error loading total revenue:", e)
        return 0

# ✅ Example usage
if _name_ == "_main_":
    # Test insert (uncomment this to add test value)
    # insert_revenue(5000)

    metrics = {}
    metrics["revenue"] = fetch_total_revenue()
    
import sqlite3

conn = sqlite3.connect("company.db")
cursor = conn.cursor()

# Check if 'address' exists and 'customer_address' does not
cursor.execute("PRAGMA table_info(customers)")
columns = [row[1] for row in cursor.fetchall()]

if "address" in columns and "customer_address" not in columns:
    cursor.execute("ALTER TABLE customers RENAME COLUMN address TO customer_address")
    print("✅ Renamed 'address' to 'customer_address'")
else:
    print("ℹ Rename skipped. Current columns:", columns)

conn.commit()
conn.close()


# ---------------------- Login Function ----------------------
def on_signin():
    global current_user
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    if not email or not password:
        messagebox.showwarning("Missing Info", "Please enter both email and password.")
    elif email == "123" and password == "123":
        current_user = "Novanectar Services Pvt.Ltd."
        root.destroy()           # Close login window
        build_dashboard()        # Open actual dashboard
    else:
        messagebox.showerror("Login Failed", "Incorrect email or password")

def handle_logout(current_window):
    confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
    if confirm:
        current_window.destroy()
        show_login_screen() 
        
# ---------------------- inventorydef show_inventory_view():
def init_inventory_db():
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            stock INTEGER,
            price REAL
        )
    """)
    conn.commit()
    conn.close()
    # Show success message
    messagebox.showinfo("Database Initialized", "Table 'items' has been created.")
    # Open the form
    add_item_form()

def add_item_form():
    top = tk.Toplevel()
    top.title("Add Item")
    top.geometry("460x540")  # Increased window height
    top.configure(bg="#e0e0e0")

    # Card-like frame
    card = tk.Frame(top, bg="white", bd=2, relief="groove")
    card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=500)  # Increased card height

    # Title
    title_label = tk.Label(card, text="Add New Item", bg="white",
                           font=("Segoe UI", 16, "bold"), fg="#333")
    title_label.pack(pady=(20, 10))

    # Helper for input fields
    def create_labeled_input(parent, label_text, widget):
        label = tk.Label(parent, text=label_text, bg="white", font=("Segoe UI", 11), anchor="w")
        label.pack(fill="x", padx=30, pady=(10, 2))
        widget.pack(padx=30, pady=(0, 5), fill="x")

    # Entry fields
    entry_item_id = ttk.Entry(card, font=("Segoe UI", 11))
    create_labeled_input(card, "Item ID", entry_item_id)

    entry_name = ttk.Entry(card, font=("Segoe UI", 11))
    create_labeled_input(card, "Name", entry_name)

    category_options = ["Fruits", "Vegetables", "Clothes", "Electronics", "Books", "Toys"]
    entry_category = ttk.Combobox(card, values=category_options, state="readonly", font=("Segoe UI", 11))
    entry_category.set("Select Category")
    create_labeled_input(card, "Category", entry_category)

    entry_stock = ttk.Entry(card, font=("Segoe UI", 11))
    create_labeled_input(card, "Stock", entry_stock)

    entry_price = ttk.Entry(card, font=("Segoe UI", 11))
    create_labeled_input(card, "Price", entry_price)

    # Hover button effect
    def on_enter(e): save_btn["bg"] = "#0056b3"
    def on_leave(e): save_btn["bg"] = "#007bff"

    # Save function
    def on_save():
        if not all([entry_item_id.get(), entry_name.get(), entry_category.get(),
                    entry_stock.get(), entry_price.get()]):
            messagebox.showwarning("Missing Fields", "Please fill all fields.")
            return

        try:
            int(entry_stock.get())
            float(entry_price.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Stock must be an integer and Price must be numeric.")
            return

        messagebox.showinfo("Success", "Item saved successfully!")
        print("Saved:", {
            "Item ID": entry_item_id.get(),
            "Name": entry_name.get(),
            "Category": entry_category.get(),
            "Stock": entry_stock.get(),
            "Price": entry_price.get()
        })
        top.destroy()

    # Save button
    save_btn = tk.Button(card, text="Save", font=("Segoe UI", 11, "bold"),
                         bg="#007bff", fg="white", activebackground="#0056b3",
                         relief="flat", command=on_save)
    save_btn.pack(pady=20, ipadx=15, ipady=6)

    save_btn.bind("<Enter>", on_enter)
    save_btn.bind("<Leave>", on_leave)

def load_inventory_data():
    inventory_tree.delete(*inventory_tree.get_children())
    
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    # Fetch all items and sort by stock ascending (low to high)
    cursor.execute("SELECT * FROM items ORDER BY stock ASC")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        item_id, name, category, stock, price = row[:5]  # Adjust index if more columns exist

        if stock == 0:
            tag = "Out of Stock"
        elif stock < 5:
            tag = "Low Stock"
        else:
            tag = "In Stock"

        # Add edit/delete icons
        inventory_tree.insert("", "end", values=(item_id, name, category, stock, price, "✏  🗑"), tags=(tag,))

    conn.close()

    # Only bind once, not repeatedly
    inventory_tree.unbind("<Button-1>")
    inventory_tree.bind("<Button-1>", handle_treeview_click)


def handle_treeview_click(event):
    region = inventory_tree.identify("region", event.x, event.y)
    if region != "cell":
        return

    row_id = inventory_tree.identify_row(event.y)
    col_id = inventory_tree.identify_column(event.x)

    if not row_id or col_id != "#6":  # Action column
        return

    values = inventory_tree.item(row_id, "values")
    if not values:
        return

    item_id = values[0]

    # Detect which icon was clicked
    bbox = inventory_tree.bbox(row_id, col_id)
    if not bbox:
        return
    x_offset = bbox[0]
    width = bbox[2]
    relative_x = event.x - x_offset

    # Assume ✏ takes left half, 🗑 takes right half
    if relative_x < width / 2:
        edit_inventory_item(item_id)
    else:
        delete_inventory_item(item_id)


def edit_inventory_item(item_id):
    # Fetch item data
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE item_id=?", (item_id,))
    item = cursor.fetchone()
    conn.close()

    if not item:
        messagebox.showerror("Error", "Item not found.")
        return

    # item = (item_id, name, category, stock, price)
    popup = tk.Toplevel()
    popup.title("Edit Item")
    popup.geometry("400x350")
    popup.resizable(False, False)
    popup.configure(bg="white")

    tk.Label(popup, text="Edit Item", font=("Helvetica", 16, "bold"), bg="white").pack(pady=10)

    # Fields
    tk.Label(popup, text="Name:", font=("Helvetica", 12), bg="white").pack()
    name_entry = tk.Entry(popup, font=("Helvetica", 12))
    name_entry.insert(0, item[1])
    name_entry.pack(pady=5)

    tk.Label(popup, text="Category:", font=("Helvetica", 12), bg="white").pack()
    category_entry = tk.Entry(popup, font=("Helvetica", 12))
    category_entry.insert(0, item[2])
    category_entry.pack(pady=5)

    tk.Label(popup, text="Stock:", font=("Helvetica", 12), bg="white").pack()
    stock_entry = tk.Entry(popup, font=("Helvetica", 12))
    stock_entry.insert(0, str(item[3]))
    stock_entry.pack(pady=5)

    tk.Label(popup, text="Price:", font=("Helvetica", 12), bg="white").pack()
    price_entry = tk.Entry(popup, font=("Helvetica", 12))
    price_entry.insert(0, str(item[4]))
    price_entry.pack(pady=5)

    def save_changes():
        new_name = name_entry.get()
        new_category = category_entry.get()
        try:
            new_stock = int(stock_entry.get())
            new_price = float(price_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Stock must be an integer and Price must be a number.")
            return

        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE items
            SET name=?, category=?, stock=?, price=?
            WHERE item_id=?
        """, (new_name, new_category, new_stock, new_price, item_id))
        conn.commit()
        conn.close()
        popup.destroy()
        load_inventory_data()
        messagebox.showinfo("Success", "Item updated successfully.")

    tk.Button(popup, text="Save Changes", bg="#2563eb", fg="white", font=("Helvetica", 12, "bold"),
              command=save_changes).pack(pady=15)



def delete_inventory_item(item_id):
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete item ID {item_id}?")
    if not confirm:
        return

    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE item_id=?", (item_id,))
    conn.commit()
    conn.close()
    load_inventory_data()

    

def show_inventory_view():
    for widget in main_frame.winfo_children():
        widget.destroy()
    main_frame.configure(bg="#f1f5f9")

    box_frame = tk.Frame(main_frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Header with label and button
    header_row = tk.Frame(box_frame, bg="white")
    header_row.pack(fill="x", padx=20, pady=(20, 10))
    tk.Label(header_row, text="📦 Inventory", font=("Helvetica", 20, "bold"), bg="white").pack(side="left")
    tk.Button(header_row, text="➕ Add Item", bg="#2563eb", fg="white",
              font=("Helvetica", 10, "bold"), padx=15, pady=5, command=add_item_form).pack(side="right")

    # Search Entry
    search_entry = tk.Entry(box_frame, font=("Helvetica", 12), width=60, fg="#64748b", bg="#f8fafc", bd=1, relief="solid")
    placeholder = "🔍 Search item by name and category"
    search_entry.insert(0, placeholder)
    search_entry.pack(padx=20, pady=(0, 20), ipady=6)

    def on_entry_click(event):
        if search_entry.get() == placeholder:
            search_entry.delete(0, "end")
            search_entry.config(fg="black")

    def on_focus_out(event):
        if search_entry.get() == "":
            search_entry.insert(0, placeholder)
            search_entry.config(fg="#64748b")

    search_entry.bind("<FocusIn>", on_entry_click)
    search_entry.bind("<FocusOut>", on_focus_out)

    # Inventory Table
    table_container = tk.Frame(box_frame, bg="#e2e8f0", bd=1, relief="solid")
    table_container.pack(fill="both", expand=True, padx=8, pady=(0, 30))

    inner_box_frame = tk.Frame(table_container, bg="white", bd=2, relief="ridge")
    inner_box_frame.pack(fill="both", expand=True, padx=30, pady=30)

    scrollbar = tk.Scrollbar(inner_box_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    columns = ("Item ID", "Name", "Category", "Stock", "Price", "Action")
    global inventory_tree
    inventory_tree = ttk.Treeview(inner_box_frame, columns=columns, show="headings", height=12, yscrollcommand=scrollbar.set)
    inventory_tree.pack(side="left", fill="both", expand=True)

    scrollbar.config(command=inventory_tree.yview)

    style = ttk.Style()
    style.configure("Treeview", rowheight=40, font=("Helvetica", 12))
    style.configure("Treeview.Heading", font=("Helvetica", 13, "bold"))

    for col in columns:
        inventory_tree.heading(col, text=col)
        inventory_tree.column(col, anchor="center", width=100)

    inventory_tree.tag_configure("In Stock", foreground="#334155")
    inventory_tree.tag_configure("Low Stock", foreground="#f97316")
    inventory_tree.tag_configure("Out of Stock", foreground="#dc2626")

    load_inventory_data()
    
    def filter_inventory(event):
        query = search_entry.get().strip().lower()
        if query == placeholder.lower():
            query = ""

        inventory_tree.delete(*inventory_tree.get_children())

        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        rows = cursor.fetchall()
        conn.close()

        filtered_rows = [
            row for row in rows
            if query in row[1].lower() or query in row[2].lower() or query == ""
        ]
        filtered_rows.sort(key=lambda x: x[3])  # sort by stock ascending

        for row in filtered_rows:
            item_id, name, category, stock, price = row[:5]
            if stock == 0:
                tag = "Out of Stock"
            elif stock < 5:
                tag = "Low Stock"
            else:
                tag = "In Stock"

            inventory_tree.insert("", "end", values=(item_id, name, category, stock, price, "✏  🗑"), tags=(tag,))

    # Bind the event here inside the function where search_entry exists
    search_entry.bind("<KeyRelease>", filter_inventory)

    # Initial load
    filter_inventory(None)


def initialize_database():
    """Initialize the SQLite database and create or update the settings table."""
    try:
        conn = sqlite3.connect("comapny.db")
        cursor = conn.cursor()
        
        # Check if the settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        table_exists = cursor.fetchone()
        
        # If the table doesn't exist, create it with all columns
        if not table_exists:
            cursor.execute('''CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                business_type TEXT,
                phone TEXT,
                email TEXT,
                password TEXT NOT NULL,
                billing_address TEXT,
                state TEXT,
                pincode TEXT,
                city TEXT,
                gst_registered TEXT CHECK(gst_registered IN ('Yes', 'No')),
                gstin TEXT,
                pan TEXT,
                einvoice_enabled INTEGER CHECK(einvoice_enabled IN (0, 1)),
                signature_path TEXT,
                business_reg_type TEXT,
                terms TEXT
            )''')
        else:
            # Get existing columns in the settings table
            cursor.execute("PRAGMA table_info(settings)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # Define the expected columns and their definitions
            expected_columns = {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'company_name': 'TEXT NOT NULL',
                'business_type': 'TEXT',
                'phone': 'TEXT',
                'email': 'TEXT',
                'password': 'TEXT NOT NULL',
                'billing_address': 'TEXT',
                'state': 'TEXT',
                'pincode': 'TEXT',
                'city': 'TEXT',
                'gst_registered': 'TEXT CHECK(gst_registered IN (\'Yes\', \'No\'))',
                'gstin': 'TEXT',
                'pan': 'TEXT',
                'einvoice_enabled': 'INTEGER CHECK(einvoice_enabled IN (0, 1))',
                'signature_path': 'TEXT',
                'business_reg_type': 'TEXT',
                'terms': 'TEXT'
            }
            
            # Add missing columns
            for column, column_type in expected_columns.items():
                if column not in existing_columns:
                    cursor.execute(f"ALTER TABLE settings ADD COLUMN {column} {column_type}")
                    print(f"Added missing column: {column} to settings table")
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number (10 digits)."""
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None

def validate_gstin(gstin):
    """Validate GSTIN format (simplified check)."""
    pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[A-Z0-9]{1}$'
    return re.match(pattern, gstin) is not None if gstin else True

def validate_pan(pan):
    """Validate PAN format."""
    pattern = r'^[A-Z]{5}\d{4}[A-Z]{1}$'
    return re.match(pattern, pan) is not None if pan else True

def load_settings():
    """Load the most recent settings from the database."""
    try:
        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to load settings: {e}")
        return None

def show_settings_view():
    """Display the settings form in the provided main frame with an attractive design."""
    terms_widget = [None]

    def save_settings():
        """Save or update settings in the database after validation."""
        try:
            if not company_name.get().strip():
                messagebox.showwarning("Input Error", "Company Name is required.")
                return
            if not password.get().strip():
                messagebox.showwarning("Input Error", "Password is required.")
                return
            if phone.get() and not validate_phone(phone.get()):
                messagebox.showwarning("Input Error", "Phone number must be 10 digits.")
                return
            if email.get() and not validate_email(email.get()):
                messagebox.showwarning("Input Error", "Invalid email format.")
                return
            if gst_var.get() == "Yes" and gstin.get() and not validate_gstin(gstin.get()):
                messagebox.showwarning("Input Error", "Invalid GSTIN format.")
                return
            if pan.get() and not validate_pan(pan.get()):
                messagebox.showwarning("Input Error", "Invalid PAN format.")
                return

            conn = sqlite3.connect("company.db")
            cursor = conn.cursor()
            data = (
                company_name.get().strip(),
                business_type.get().strip(),
                phone.get().strip(),
                email.get().strip(),
                password.get().strip(),
                address.get().strip(),
                state.get().strip(),
                pincode.get().strip(),
                city.get().strip(),
                gst_var.get(),
                gstin.get().strip(),
                pan.get().strip(),
                1 if einvoice_var.get() else 0,
                signature_path.get().strip(),
                business_reg_type.get().strip(),
                terms_widget[0].get("1.0", tk.END).strip() if terms_widget[0] else ""
            )
            cursor.execute("SELECT id FROM settings LIMIT 1")
            if cursor.fetchone():
                cursor.execute('''UPDATE settings SET
                    company_name=?, business_type=?, phone=?, email=?, password=?,
                    billing_address=?, state=?, pincode=?, city=?, gst_registered=?,
                    gstin=?, pan=?, einvoice_enabled=?, signature_path=?,
                    business_reg_type=?, terms=? WHERE id=1''', data)
            else:
                cursor.execute('''INSERT INTO settings (
                    company_name, business_type, phone, email, password,
                    billing_address, state, pincode, city, gst_registered,
                    gstin, pan, einvoice_enabled, signature_path,
                    business_reg_type, terms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Settings saved successfully.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save settings: {e}")

    def upload_signature():
        """Upload a signature image and update the label."""
        path = filedialog.askopenfilename(filetypes=[("Image files", ".png;.jpg;*.jpeg")])
        if path:
            signature_path.set(path)
            sig_label.config(text=os.path.basename(path))
        else:
            sig_label.config(text="No file selected")

    def reset_form():
        """Reset the form to loaded or default values."""
        row = load_settings()
        company_name.set(row[1] if row else "")
        business_type.set(row[2] if row else "")
        phone.set(row[3] if row else "")
        email.set(row[4] if row else "")
        password.set(row[5] if row else "")
        address.set(row[6] if row else "")
        state.set(row[7] if row else "")
        pincode.set(row[8] if row else "")
        city.set(row[9] if row else "")
        gst_var.set(row[10] if row else "No")
        gstin.set(row[11] if row else "")
        pan.set(row[12] if row else "")
        einvoice_var.set(bool(row[13]) if row and row[13] is not None else False)
        signature_path.set(row[14] if row else "")
        business_reg_type.set(row[15] if row else "")
        if terms_widget[0]:
            terms_widget[0].delete("1.0", tk.END)
            terms_text_value = row[16] if row and row[16] is not None else ""
            if isinstance(terms_text_value, str):
                terms_widget[0].insert("1.0", terms_text_value)
            else:
                terms_widget[0].insert("1.0", "")
        sig_label.config(text=os.path.basename(signature_path.get()) if signature_path.get() else "No file selected")

    def clear_form():
        """Clear all form fields to allow the user to fill information again."""
        company_name.set("")
        business_type.set("")
        phone.set("")
        email.set("")
        password.set("")
        address.set("")
        state.set("")
        pincode.set("")
        city.set("")
        gst_var.set("No")
        gstin.set("")
        pan.set("")
        einvoice_var.set(False)
        signature_path.set("")
        business_reg_type.set("")
        if terms_widget[0]:
            terms_widget[0].delete("1.0", tk.END)
        sig_label.config(text="No file selected")

    # Clear previous content
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Style configuration for attractive design
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.TLabel", font=('Helvetica', 12), padding=8, background='#f0f4f8')
    style.configure("Custom.TEntry", padding=8, font=('Helvetica', 11))
    style.configure("Custom.TButton", padding=10, font=('Helvetica', 11, 'bold'), background='#4a90e2', foreground='white')
    style.map("Custom.TButton", background=[('active', '#357abd')])
    style.configure("Custom.TCheckbutton", font=('Helvetica', 11), background='#f0f4f8')
    style.configure("Custom.TRadiobutton", font=('Helvetica', 11), background='#f0f4f8')

    # Main container with background
    canvas = tk.Canvas(main_frame, highlightthickness=0, bg='#f0f4f8')
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scroll_frame.bind("<Configure>", update_scroll_region)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Header
    header = ttk.Label(scroll_frame, text="Business Settings", font=('Helvetica', 16, 'bold'), foreground='#2c3e50', style="Custom.TLabel")
    header.grid(row=0, column=0, columnspan=2, pady=15)

    # Load existing settings
    row = load_settings()

    # Tkinter variables
    company_name = tk.StringVar(value=row[1] if row else "")
    business_type = tk.StringVar(value=row[2] if row else "")
    phone = tk.StringVar(value=row[3] if row else "")
    email = tk.StringVar(value=row[4] if row else "")
    password = tk.StringVar(value=row[5] if row else "")
    address = tk.StringVar(value=row[6] if row else "")
    state = tk.StringVar(value=row[7] if row else "")
    pincode = tk.StringVar(value=row[8] if row else "")
    city = tk.StringVar(value=row[9] if row else "")
    gst_var = tk.StringVar(value=row[10] if row else "No")
    gstin = tk.StringVar(value=row[11] if row else "")
    pan = tk.StringVar(value=row[12] if row else "")
    einvoice_var = tk.BooleanVar(value=bool(row[13]) if row and row[13] is not None else False)
    signature_path = tk.StringVar(value=row[14] if row else "")
    business_reg_type = tk.StringVar(value=row[15] if row else "")
    terms_text = row[16] if row and row[16] is not None else ""

    def add_entry(label, variable, row_num, show=None, tooltip=None):
        """Add a labeled entry field with optional tooltip."""
        lbl = ttk.Label(scroll_frame, text=label, style="Custom.TLabel")
        lbl.grid(row=row_num, column=0, sticky="e", padx=10, pady=8)
        entry = ttk.Entry(scroll_frame, textvariable=variable, width=35, show=show, style="Custom.TEntry")
        entry.grid(row=row_num, column=1, padx=10, pady=8, sticky="w")
        if tooltip:
            create_tooltip(lbl, tooltip)
        return entry

    def create_tooltip(widget, text):
        """Create a tooltip for a widget."""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry("+1000+1000")
        label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, padding=5)
        label.pack()

        def show(event):
            x, y = widget.winfo_rootx() + 20, widget.winfo_rooty() + 20
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)
        tooltip.withdraw()

    # Form fields with sections
    row_num = 1
    ttk.Separator(scroll_frame).grid(row=row_num, column=0, columnspan=2, sticky="ew", pady=10)
    row_num += 1
    ttk.Label(scroll_frame, text="Company Details", font=('Helvetica', 13, 'bold'), foreground='#2c3e50', style="Custom.TLabel").grid(row=row_num, column=0, columnspan=2, pady=5)
    row_num += 1
    add_entry("Company Name", company_name, row_num, tooltip="Enter your company name (required)"); row_num += 1
    add_entry("Business Type", business_type, row_num, tooltip="e.g., Retail, Manufacturing"); row_num += 1
    add_entry("Phone", phone, row_num, tooltip="10-digit phone number"); row_num += 1
    add_entry("Email", email, row_num, tooltip="e.g., example@domain.com"); row_num += 1
    add_entry("Password", password, row_num, show="*", tooltip="Enter a secure password (required)"); row_num += 1

    ttk.Separator(scroll_frame).grid(row=row_num, column=0, columnspan=2, sticky="ew", pady=10)
    row_num += 1
    ttk.Label(scroll_frame, text="Address Details", font=('Helvetica', 13, 'bold'), foreground='#2c3e50', style="Custom.TLabel").grid(row=row_num, column=0, columnspan=2, pady=5)
    row_num += 1
    add_entry("Billing Address", address, row_num, tooltip="Full billing address"); row_num += 1
    add_entry("State", state, row_num, tooltip="e.g., California"); row_num += 1
    add_entry("Pincode", pincode, row_num, tooltip="Postal code"); row_num += 1
    add_entry("City", city, row_num, tooltip="e.g., San Francisco"); row_num += 1

    ttk.Separator(scroll_frame).grid(row=row_num, column=0, columnspan=2, sticky="ew", pady=10)
    row_num += 1
    ttk.Label(scroll_frame, text="Tax & Compliance", font=('Helvetica', 13, 'bold'), foreground='#2c3e50', style="Custom.TLabel").grid(row=row_num, column=0, columnspan=2, pady=5)
    row_num += 1
    ttk.Label(scroll_frame, text="GST Registered", style="Custom.TLabel").grid(row=row_num, column=0, sticky="e", padx=10, pady=8)
    gst_frame = ttk.Frame(scroll_frame)
    ttk.Radiobutton(gst_frame, text="Yes", variable=gst_var, value="Yes", style="Custom.TRadiobutton").pack(side="left", padx=5)
    ttk.Radiobutton(gst_frame, text="No", variable=gst_var, value="No", style="Custom.TRadiobutton").pack(side="left", padx=5)
    gst_frame.grid(row=row_num, column=1, sticky="w", padx=10, pady=8)
    row_num += 1
    add_entry("GSTIN", gstin, row_num, tooltip="e.g., 22AAAAA0000A1Z5"); row_num += 1
    add_entry("PAN", pan, row_num, tooltip="e.g., ABCDE1234F"); row_num += 1
    ttk.Checkbutton(scroll_frame, text="Enable E-Invoice", variable=einvoice_var, style="Custom.TCheckbutton").grid(row=row_num, column=1, sticky="w", padx=10, pady=8)
    row_num += 1

    ttk.Separator(scroll_frame).grid(row=row_num, column=0, columnspan=2, sticky="ew", pady=10)
    row_num += 1
    ttk.Label(scroll_frame, text="Additional Settings", font=('Helvetica', 13, 'bold'), foreground='#2c3e50', style="Custom.TLabel").grid(row=row_num, column=0, columnspan=2, pady=5)
    row_num += 1
    ttk.Label(scroll_frame, text="Signature Image", style="Custom.TLabel").grid(row=row_num, column=0, sticky="e", padx=10, pady=8)
    sig_button = ttk.Button(scroll_frame, text="Upload Signature", command=upload_signature, style="Custom.TButton")
    sig_button.grid(row=row_num, column=1, sticky="w", padx=10, pady=8)
    sig_label = ttk.Label(scroll_frame, text=os.path.basename(signature_path.get()) if signature_path.get() else "No file selected", style="Custom.TLabel")
    sig_label.grid(row=row_num + 1, column=1, sticky="w", padx=10, pady=8)
    row_num += 2
    add_entry("Business Reg. Type", business_reg_type, row_num, tooltip="e.g., LLC, Corporation"); row_num += 1
    ttk.Label(scroll_frame, text="Terms & Conditions", style="Custom.TLabel").grid(row=row_num, column=0, sticky="ne", padx=10, pady=8)
    terms_widget[0] = tk.Text(scroll_frame, width=35, height=6, font=('Helvetica', 11), relief="flat", bg="#ffffff", borderwidth=1)
    terms_widget[0].grid(row=row_num, column=1, padx=10, pady=8, sticky="w")
    # Safely insert terms_text, ensuring it's a string
    try:
        terms_text_value = str(terms_text) if terms_text is not None else ""
        terms_widget[0].insert("1.0", terms_text_value)
    except Exception as e:
        messagebox.showwarning("Text Insert Error", f"Failed to insert Terms & Conditions: {e}")
        terms_widget[0].insert("1.0", "")
    row_num += 1

    # Buttons
    button_frame = ttk.Frame(scroll_frame)
    button_frame.grid(row=row_num, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
    save_button = ttk.Button(button_frame, text="Save Settings", command=save_settings, style="Custom.TButton")
    save_button.pack(side="left", padx=10)
    cancel_button = ttk.Button(button_frame, text="Cancel", command=reset_form, style="Custom.TButton")
    cancel_button.pack(side="left", padx=10)
    reset_button = ttk.Button(button_frame, text="Reset", command=clear_form, style="Custom.TButton")
    reset_button.pack(side="left", padx=10)

    # Force update of the scroll region
    scroll_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))


# ---------------------- Dashboard ----------------------


def build_dashboard():
    global main_frame

    dashboard = tk.Tk()
    dashboard.title("Dashboard")
    dashboard.state('zoomed')  # Auto full screen
    dashboard.configure(bg=BACKGROUND_COLOR)

    # Sidebar
    sidebar = tk.Frame(dashboard, width=200, bg=PRIMARY_COLOR)
    sidebar.pack(side="left", fill="y")

    tk.Label(sidebar, text=f"👤  {current_user}", bg=PRIMARY_COLOR, fg=SECONDARY_COLOR, font=("Helvetica", 12, "bold")).pack(pady=(30, 10))

    def create_sidebar_button(name, command=None):
        btn = tk.Button(sidebar, text=name, font=("Helvetica", 12), fg=SECONDARY_COLOR, bg=PRIMARY_COLOR, bd=0, anchor="w", padx=10, pady=5)
        btn.pack(fill="x", pady=2)
        btn.bind("<Enter>", lambda e: btn.config(bg="#2B4FAA"))
        btn.bind("<Leave>", lambda e: btn.config(bg=PRIMARY_COLOR))
        if command:
            btn.config(command=command)

    create_sidebar_button("Dashboard", show_dashboard_view)
    create_sidebar_button("Customer", show_customer_details)
    create_sidebar_button("Inventory",show_inventory_view)
    create_sidebar_button("Settings",show_settings_view)

    logout_btn = tk.Button(
    sidebar,
    text="⬅ LOGOUT",
    font=("Helvetica", 10, "bold"),
    fg=SECONDARY_COLOR,
    bg=PRIMARY_COLOR,
    bd=0,
    anchor="w",
    padx=10,
    pady=5,
    command=lambda: handle_logout(dashboard)  # Use the handler
)
    logout_btn.pack(side="bottom", pady=20)

    logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg="#2B4FAA"))
    logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=PRIMARY_COLOR))

    # Top Frame
    top_frame = tk.Frame(dashboard, bg=SECONDARY_COLOR, height=60, relief="raised", bd=1)
    top_frame.pack(fill="x")

    today = datetime.now().strftime("%d %B %Y")
    tk.Label(top_frame, text=f"✨ Welcome back  |  {today}  |  {datetime.now().strftime('%A')}", font=("Helvetica", 10), bg=SECONDARY_COLOR, fg=PRIMARY_COLOR).pack(side="right", padx=20, pady=10)

    main_frame = tk.Frame(dashboard, bg=BACKGROUND_COLOR, padx=20, pady=10)
    main_frame.pack(fill="both", expand=True)

    show_dashboard_view()

    dashboard.mainloop()


def calculate_grand_total(products):
    # Logic for calculating the grand total
    total = sum([product['price'] * product['quantity'] for product in products])
    return total
from datetime import datetime
import os

# --- TAX INVOICE NUMBER ---
def get_next_invoice_number():
    counter_file = resource_path("invoice_counter_tax.txt") # Use resource_path
    
    number = read_and_increment_counter(counter_file)

    # Get financial year string
    now = datetime.now()
    year = now.year
    month = now.month
    if month >= 4:
        fy_start = year
        fy_end = year + 1
    else:
        fy_start = year - 1
        fy_end = year
    fy_label = f"{str(fy_start)[-2:]}-{str(fy_end)[-2:]}"  # e.g., "25-26"

    return f"NN/{fy_label}/{str(number).zfill(3)}"


import os

def read_and_increment_counter(counter_file):
    # Ensure the file exists
    if not os.path.exists(counter_file):
        with open(counter_file, 'w') as f:
            f.write('1')
        return 1

    # Read, increment, write back
    with open(counter_file, 'r+') as f:
        try:
            number = int(f.read().strip())
        except ValueError:
            number = 1  # fallback if file is empty or corrupt

        f.seek(0)
        f.write(str(number + 1))
        f.truncate()

    return number
def get_simple_invoice_number():
    counter_file = resource_path("invoice_counter_cash.txt") # Use resource_path
    number = read_and_increment_counter(counter_file)
    print(f"[DEBUG] Generated Invoice Number: NN-{str(number).zfill(3)}")  # 👈 Add this
    return f"NN-{str(number).zfill(3)}"


def draw_full_table_blank_rows(draw, font, bold_font, products, start_x=10, start_y=710, bottom_y=1260):
    headers = ["S.No", "Description of Goods/Services", "HSN", "Qty", "Rate", "Amount"]
    col_widths = [80, 460, 170, 170, 170, 170]
    header_height = 50
    row_height = 70
    header_bg_color = "#D0E4F7"
    row_alt_color = "#e7f4fc"
    border_color = "#A9C7ED"

    def safe_float(val):
        try:
            return float(str(val).strip().replace("₹", "").replace("%", ""))
        except:
            return 0.0

    # --- Draw Header ---
    x = start_x
    y = start_y
    total_width = sum(col_widths)
    draw.rectangle([(x, y), (x + total_width, y + header_height)], fill=header_bg_color, outline=border_color)

    x = start_x
    for header, width in zip(headers, col_widths):
        draw.text((x + 10, y + 20), header, fill="black", font=bold_font)
        x += width

    draw.line([(start_x, y + header_height), (start_x + total_width, y + header_height)], fill="black", width=1)

    # --- Draw Table Border ---
    table_top = y + header_height
    table_bottom = bottom_y
    draw.rectangle([(start_x, table_top), (start_x + total_width, table_bottom)], outline=border_color, width=1)

    # --- Product Rows ---
    y = table_top
    grand_total = 0.0
    for idx, product in enumerate(products):
        if y + row_height > bottom_y:
            break

        bg_color = row_alt_color if idx % 2 == 0 else "white"
        draw.rectangle([start_x, y, start_x + total_width, y + row_height], fill=bg_color)

        try:
            name = str(product[0]).strip()
            hsn = str(product[1]).strip()
            rate = safe_float(product[2])
            qty = int(str(product[3]).strip())
            amount = rate * qty
        except Exception as e:
            print(f"⚠ Error parsing row {idx + 1}: {e} — {product}")
            continue

        grand_total += amount

        row_data = [str(idx + 1), name, hsn, str(qty), f"{rate:.2f}", f"{amount:.2f}"]
        x = start_x
        for value, width in zip(row_data, col_widths):
            draw.text((x + 20, y + 10), value, fill="black", font=font)
            x += width

        y += row_height

    # ✅ Draw "Total Amount" Box on LEFT SIDE
    total_box_width = 400
    total_box_height = 60
    image_width = 1270

# Set right margin
    right_margin = 40

# Right-align box: from right edge minus width and margin
    total_box_x = image_width - total_box_width - right_margin
    total_box_y = 1325  # fixed Y, below product table area

    draw.rectangle(
        [total_box_x, total_box_y, total_box_x + total_box_width, total_box_y + total_box_height],
        outline="black", fill="#f4f4f4"
    )

    draw.text(
        (total_box_x + 20, total_box_y + 15),
        "Total Amount",
        font=bold_font, fill="black"
    )

    total_text = f"₹{grand_total:,.2f}"
    text_width = draw.textlength(total_text, font=bold_font)
    draw.text(
        (total_box_x + total_box_width - text_width - 20, total_box_y + 15),
        total_text,
        font=bold_font, fill="black"
    )

    return grand_total


'''def draw_product_rows(draw, font, start_x, start_y, products):
    column_widths = [70, 330, 220, 160, 180, 230]
    row_height = 40

    for idx, product in enumerate(products):
        row_y = start_y + idx * row_height
        bg_color = "#e7f4fc" if idx % 2 == 0 else "white"
        draw.rectangle([start_x, row_y, start_x + sum(column_widths), row_y + row_height], fill=bg_color)

        try:
            description = str(product[0]).strip()                           # Product Name
            sac_code = str(product[1]).strip()                             # SAC Code
            rate = float(str(product[2]).replace("₹", "").strip())        # Rate
            quantity = int(str(product[3]).strip())                        # Quantity
            total = rate * quantity                                        # Total = Qty × Rate
        except Exception as e:
            print(f"⚠ Error parsing row {idx + 1}: {e} — {product}")
            continue

        row_data = [
            str(idx + 1),              # S.No
            description,
            sac_code,
            str(quantity),
            f"₹{rate:.2f}",
            f"₹{total:.2f}"
        ]

        x = start_x
        for text, width in zip(row_data, column_widths):
            draw.text((x + 40, row_y + 12), text, font=font, fill="black")
            x += width'''


def draw_summary_table1(draw, font, start_x, start_y, cell_width=300, cell_height=40):
    # Step 1: Connect and fetch latest E-Way Bill data
    conn = sqlite3.connect('company.db')
    cursor = conn.cursor()
    cursor.execute("SELECT eway_bill, vehicle_no, p_marka, reverse_charges FROM eway_bills ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    # Step 2: Provide default values if no record found
    if result:
        eway_bill, vehicle_no, p_marka, reverse_charges = result
    else:
        eway_bill, vehicle_no, p_marka, reverse_charges = ("", "", "", "")

    # Step 3: Table content with default blank values if empty
    texts = [
        ("E-way Bill No.", eway_bill if eway_bill else " "),  # Default to blank if empty
        ("Vehicle No.", vehicle_no if vehicle_no else " "),  # Default to blank if empty
        ("P-Marka", p_marka if p_marka else " "),  # Default to blank if empty
        ("Reverse Charge", reverse_charges if reverse_charges else " ")  # Default to blank if empty
    ]

    # Adjust horizontal position
    start_x += 565

    # Step 4: Draw table cells and text
    for row, (label, value) in enumerate(texts):
        for col, text in enumerate([label, value]):
            x1 = start_x + col * cell_width
            y1 = start_y + row * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height

            # Draw cell border
            draw.rectangle([x1, y1, x2, y2], outline="black", width=1)

            # Draw text inside cell
            lines = text.split('\n')
            for i, line in enumerate(lines):
                w, h = draw.textbbox((0, 0), line, font=font)[2:4]
                text_x = x1 + 10
                text_y = y1 + 10 + i * (h + 5)
                draw.text((text_x, text_y), line, fill="black", font=font)


import os
from tkinter import messagebox
from PIL import Image


def sanitize_filename(name, replace_with="_"):
    return "".join(c if c.isalnum() or c in "._-" else replace_with for c in name)


import os

def sanitize_filename(name, replace_with="-"):
    """
    Replaces unsafe characters in a string to make a safe filename.
    """
    return "".join(c if c.isalnum() or c in "._-" else replace_with for c in name)

def download_invoice(img, invoice_number):
    """
    Save the invoice image as a PDF in the 'tax_invoices' folder and open it.
    """
    folder_path = resource_path("tax_invoices") # Use resource_path
    os.makedirs(folder_path, exist_ok=True)

    filename_safe = sanitize_filename(invoice_number, replace_with="-")
    pdf_path = os.path.join(folder_path, f"{filename_safe}.pdf")

    try:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(pdf_path, "PDF", resolution=100.0)
        messagebox.showinfo("Download Complete", f"Invoice PDF saved:\n{pdf_path}")

        # ✅ Automatically open the PDF file (Windows only)
        os.startfile(pdf_path)

    except Exception as e:
        messagebox.showerror("Download Failed", f"Error saving invoice PDF:\n{e}")

def download_invoice2(img, invoice_number):
    """
    Save the receipt image as a PDF in the 'cash_receipts' folder and open it.
    """
    folder_path = resource_path("cash_receipts") # Use resource_path
    os.makedirs(folder_path, exist_ok=True)

    filename_safe = sanitize_filename(invoice_number, replace_with="-")
    pdf_path = os.path.join(folder_path, f"{filename_safe}.pdf")

    try:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(pdf_path, "PDF", resolution=100.0)
        messagebox.showinfo("Download Complete", f"Cash Receipt saved:\n{pdf_path}")

        # ✅ Automatically open the PDF file (Windows only)
        os.startfile(pdf_path)

    except Exception as e:
        messagebox.showerror("Save Error", f"❌ Error saving receipt:\n{e}")


from textwrap import wrap
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from num2words import num2words
import os
from tkinter import messagebox

def open_invoice_image(
    customer_name,
    customer_email,
    customer_phone,
    customer_address,      # 🧾 Billing address     # 🧾 Shipping address (replaces previous shipping_address)
    gstin,
    state_code,
    invoice_number,
    products=None,
    grand_total=0.0,
    domain="127.0.0.1"  # Replace with production domain when deploying
):
    products = products or []

    def calculate_gst_summary(products):
        subtotal = 0.0
        for idx, product in enumerate(products):
            try:
                rate = float(str(product[2]).replace("₹", "").strip())
                qty = int(str(product[3]).strip())
                subtotal += rate * qty
            except Exception as e:
                print(f"⚠ Error in GST calculation for row {idx+1}: {e} — {product}")
                continue
        sgst = subtotal * 0.09
        cgst = subtotal * 0.09
        gross_total = subtotal + sgst + cgst
        rounded_total = round(gross_total)
        round_off = rounded_total - gross_total
        return subtotal, sgst, cgst, round_off, rounded_total


    try:
        img = Image.open(resource_path("invoice.jpg")).convert("RGB") # Use resource_path
    except FileNotFoundError:
        print("⚠ invoice.jpg not found.")
        return

    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    # Load logo
    try:
        logo = Image.open(resource_path("logo2.jpg")).convert("RGBA") # Use resource_path
        logo = logo.resize((256, 75))
        logo_x = (img_width - logo.width) // 2
        img.paste(logo, (logo_x, 20), logo)
    except Exception as e:
        print(f"⚠ Could not load logo: {e}")

    # Fonts
    try:
        font = ImageFont.truetype("arial.ttf", 22)
        bold_font = ImageFont.truetype("arialbd.ttf", 25)
        title_font = ImageFont.truetype("arialbd.ttf", 30)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        bold_font = font
        title_font = font
        small_font = font

    # Header
    header_y = 90
    title = "Tax Invoice"
    w, _ = draw.textbbox((0, 0), title, font=title_font)[2:]
    draw.text(((img_width - w) // 2, header_y), title, fill="black", font=title_font)

    # Company Info
    company_x = 10
    company_y = header_y + 50
    company_lines = [
        "Novanectar Services Private Limited",
        "Khasra No. 1336/3/1 Haripuram, Kanwali GMS Road,",
        "Dehradun, Uttarakand-248001",
        "Mob:- +91 8979891703",
        "State:- Uttrakhand ",
        "GSTIN:- 05AAJCN5266D1Z1",
        "E-Mail:- account@novanectar.co.in"
    ]
    for idx, line in enumerate(company_lines):
        draw.text((company_x, company_y), line, fill="black", font=bold_font if idx == 0 else font)
        company_y += 30

    # Invoice Info
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    info_x = img_width - 320
    info_y = header_y + 60
    draw.text((info_x, info_y), "Invoice No.", font=bold_font, fill="black")
    draw.text((info_x + 150, info_y), str(invoice_number), font=font, fill="blue")
    draw.text((info_x, info_y + 35), "Invoice Date", font=bold_font, fill="black")
    draw.text((info_x + 150, info_y + 35), date_str, font=font, fill="blue")

    # Buyer (Billing Address)
    section_y = company_y + 10
    draw.text((company_x, section_y), "Buyer (Bill To)", fill=(35, 102, 171), font=bold_font)
    section_y += 35
    draw.text((company_x, section_y), customer_name, font=bold_font, fill="black")
    section_y += 30
    for line in wrap(customer_address or "", width=40)[:2]:
        draw.text((company_x, section_y), line, font=font, fill="black")
        section_y += 25
    if gstin:  # Only draw GSTIN if it's not empty or None
     draw.text((company_x, section_y), f"GSTIN: {gstin}", font=font, fill="black")
     section_y += 25

    draw.text((company_x, section_y), f"State Code: {state_code}", font=font, fill="black")
    section_y += 45

    # Consignee (Shipping Address)
    draw.text((company_x, section_y), "Consignee (Ship To)", fill=(35, 102, 171), font=bold_font)
    section_y += 35
    draw.text((company_x, section_y), customer_name, font=bold_font, fill="black")
    section_y += 30
    for line in wrap(customer_address or "", width=40)[:2]:
        draw.text((company_x, section_y), line, font=font, fill="black")
        section_y += 25
    if gstin:  # Only draw GSTIN if it's not empty or None
     draw.text((company_x, section_y), f"GSTIN: {gstin}", font=font, fill="black")
     section_y += 25

    section_y += 10
    draw.text((company_x, section_y), f"State: {state_code}", font=font, fill="black")

    # Product Table
    draw_full_table_blank_rows(draw, font, bold_font, products, start_x=10, start_y=680, bottom_y=1300)

    # GST Summary
    subtotal, sgst, cgst, round_off, rounded_total = calculate_gst_summary(products)

    # Account Details
    bottom_y = 1330
    box_left = 10
    draw.text((box_left, bottom_y), "Account Details", font=bold_font, fill=(35, 102, 171))
    y = bottom_y + 50
    account_info = [
        "Bank Name: HDFC Bank",
        "Account Number: 50200095658621",
        "IFSC Code: HDFC0007959",
        "CIN: U47410UT2024PTC017142",
        "GSTIN: 06AHWPP8969N1ZV"
    ]
    for line in account_info:
        draw.text((box_left, y), line, font=font, fill="black")
        y += 28

    # GST Summary Box
    box_x = img_width - 410
    box_y = bottom_y
    box_width = 400
    row_height = 40
    labels = ["Subtotal", "SGST (9%)", "CGST (9%)", "ROUND OFF", "Total Amount"]
    values = [
        f"₹{subtotal:,.2f}",
        f"₹{sgst:,.2f}",
        f"₹{cgst:,.2f}",
        f"{round_off:+.2f}",
        f"₹{rounded_total:,.2f}"
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        fill_color = "#E6F2FA" if i < 4 else "#0B5C8D"
        text_color = "black" if i < 4 else "white"
        draw.rectangle([box_x, box_y + i * row_height, box_x + box_width, box_y + (i + 1) * row_height], fill=fill_color)
        draw.text((box_x + 10, box_y + i * row_height + 10), label, font=font, fill=text_color)
        w = draw.textbbox((0, 0), value, font=bold_font)[2]
        draw.text((box_x + box_width - w - 10, box_y + i * row_height + 10), value, font=bold_font, fill=text_color)

    # Total in Words
    words_y = box_y + len(labels) * row_height + 20
    amount_in_words = num2words(rounded_total, to='cardinal', lang='en_IN').replace(",", "").title() + " Only"
    draw.text((box_left, words_y), f"Total Amount (In Words): {amount_in_words}", font=bold_font, fill="black")

    # Declaration
    draw.text((box_left, words_y + 60), "Description", font=small_font, fill="black")
    desc_text = (
        "We declare that this invoice shows the actual price of the goods/Services described\n"
        "and that all particulars are true and correct."
    )
    desc_y = words_y + 90
    for line in desc_text.split("\n"):
        draw.text((box_left, desc_y), line, font=small_font, fill="black")
        desc_y += 22

    # Signature
    sig_x = img_width - 410
    sig_y = desc_y - 60
    draw.text((sig_x, sig_y), "For Novanectar Services Pvt. Ltd", font=bold_font, fill="black")
    draw.line([(sig_x, sig_y + 60), (sig_x + 390, sig_y + 60)], fill="black", width=1)
    draw.text((sig_x + 80, sig_y + 60), "Authorized Signature", font=font, fill="black")

    # Footer
    footer_y = img_height - 30
    draw.line([(0, footer_y - 10), (img_width, footer_y - 10)], fill="black", width=1)

    credit_text = "This Is A Computer-Generated Invoice"
    cr_w = draw.textbbox((0, 0), credit_text, font=font)[2]
    draw.text(((img_width - cr_w) // 2, footer_y), credit_text, font=font, fill="black")


    safe_invoice_number = invoice_number.replace("/", "_")
    os.makedirs(resource_path("invoices"), exist_ok=True) # Use resource_path
    img.save(resource_path(f"invoices/{safe_invoice_number}.pdf"), "PDF", resolution=100.0) # Use resource_path

    

    # Show preview in Tkinter
    img_resized = img.resize((500, 600), Image.LANCZOS)
    preview_window = tk.Toplevel()
    preview_window.title("Invoice Preview")
    preview_window.geometry("595x850")
    tk_image = ImageTk.PhotoImage(img_resized)
    label = tk.Label(preview_window, image=tk_image)
    label.image = tk_image
    label.pack(padx=10, pady=10)
    tk.Button(preview_window, text="Close", command=preview_window.destroy).pack(pady=5)
    tk.Button(preview_window, text="Download Invoice", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", command=lambda img=img, inv=invoice_number: download_invoice(img, inv)).pack(pady=10)
    insert_revenue(rounded_total)


from textwrap import wrap
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from num2words import num2words
import os
from tkinter import messagebox

import os
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
from datetime import datetime
from textwrap import wrap
from num2words import num2words

def open_invoice_image1(
    customer_name,
    customer_email,
    customer_phone,
    customer_address,
    gstin,
    state_code,
    invoice_number,
    products=None,
    grand_total=0.0,
    domain="127.0.0.1"
):
    products = products or []

    def calculate_gst_summary(products):
        subtotal = 0.0
        for idx, product in enumerate(products):
            try:
                rate = float(str(product[2]).replace("₹", "").strip())
                qty = int(str(product[3]).strip())
                subtotal += rate * qty
            except Exception as e:
                print(f"⚠ Error in GST calculation for row {idx+1}: {e} — {product}")
                continue
        sgst = subtotal * 0.09
        cgst = subtotal * 0.09
        gross_total = subtotal + sgst + cgst
        rounded_total = round(gross_total)
        round_off = rounded_total - gross_total
        return subtotal, sgst, cgst, round_off, rounded_total

    try:
        img = Image.open(resource_path("invoice1.jpg")).convert("RGB") # Use resource_path
    except FileNotFoundError:
        print("⚠ invoice1.jpg not found.")
        return

    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    # Load logo
    try:
        logo = Image.open(resource_path("logo2.jpg")).convert("RGBA") # Use resource_path
        logo = logo.resize((256, 75))
        logo_x = (img_width - logo.width) // 2
        img.paste(logo, (logo_x, 20), logo)
    except Exception as e:
        print(f"⚠ Could not load logo: {e}")

    # Fonts
    try:
        font = ImageFont.truetype("arial.ttf", 22)
        bold_font = ImageFont.truetype("arialbd.ttf", 25)
        title_font = ImageFont.truetype("arialbd.ttf", 30)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        bold_font = font
        title_font = font
        small_font = font

    # Header
    header_y = 90
    title = "Tax Invoice"
    w, _ = draw.textbbox((0, 0), title, font=title_font)[2:]
    draw.text(((img_width - w) // 2, header_y), title, fill="black", font=title_font)

    # Company Info
    company_x = 10
    company_y = header_y + 50
    company_lines = [
        "Novanectar Services Private Limited",
        "Khasra No. 1336/3/1 Haripuram, Kanwali GMS Road,",
        "Dehradun, Uttarakand-248001",
        "Mob:- +91 8979891703",
        "State:- Uttrakhand ",
        "GSTIN:- 05AAJCN5266D1Z1",
        "E-Mail:- account@novanectar.co.in"
    ]
    for idx, line in enumerate(company_lines):
        draw.text((company_x, company_y), line, fill="black", font=bold_font if idx == 0 else font)
        company_y += 30

    # Invoice Info
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    info_x = img_width - 320
    info_y = header_y + 60
    draw.text((info_x, info_y), "Invoice No.", font=bold_font, fill="black")
    draw.text((info_x + 150, info_y), str(invoice_number), font=font, fill="blue")
    draw.text((info_x, info_y + 35), "Invoice Date", font=bold_font, fill="black")
    draw.text((info_x + 150, info_y + 35), date_str, font=font, fill="blue")

    # Buyer (Billing Address)
    section_y = company_y + 10
    draw.text((company_x, section_y), "Buyer (Bill To)", fill=(35, 102, 171), font=bold_font)
    section_y += 35
    draw.text((company_x, section_y), customer_name, font=bold_font, fill="black")
    section_y += 30
    for line in wrap(customer_address or "", width=40)[:2]:
        draw.text((company_x, section_y), line, font=font, fill="black")
        section_y += 25
    if gstin:
        draw.text((company_x, section_y), f"GSTIN: {gstin}", font=font, fill="black")
        section_y += 25
    draw.text((company_x, section_y), f"State: {state_code}", font=font, fill="black")
    section_y += 45

    # Consignee (Shipping Address)
    draw.text((company_x, section_y), "Consignee (Ship To)", fill=(35, 102, 171), font=bold_font)
    section_y += 35
    draw.text((company_x, section_y), customer_name, font=bold_font, fill="black")
    section_y += 30
    for line in wrap(customer_address or "", width=40)[:2]:
        draw.text((company_x, section_y), line, font=font, fill="black")
        section_y += 25
    if gstin:
        draw.text((company_x, section_y), f"GSTIN: {gstin}", font=font, fill="black")
        section_y += 30
    draw.text((company_x, section_y ), f"State: {state_code}", font=font, fill="black")

    # Product Table Placeholder
    draw_full_table_blank_rows(draw, font, bold_font, products, start_x=10, start_y=680, bottom_y=1300)

    # GST Summary
    subtotal, sgst, cgst, round_off, rounded_total = calculate_gst_summary(products)

    # Account Details
    bottom_y = 1330
    box_left = 10
    draw.text((box_left, bottom_y), "Account Details", font=bold_font, fill=(35, 102, 171))
    y = bottom_y + 50
    account_info = [
        "Bank Name: HDFC Bank",
        "Account Number: 50200095658621",
        "IFSC Code: HDFC0007959",
        "CIN: U47410UT2024PTC017142",
        "GSTIN: 06AHWPP8969N1ZV"
    ]
    for line in account_info:
        draw.text((box_left, y), line, font=font, fill="black")
        y += 28

    # GST Summary Box
    box_x = img_width - 410
    box_y = bottom_y
    box_width = 400
    row_height = 40
    labels = ["Subtotal", "SGST (9%)", "CGST (9%)", "ROUND OFF", "Total Amount"]
    values = [
        f"₹{subtotal:,.2f}",
        f"₹{sgst:,.2f}",
        f"₹{cgst:,.2f}",
        f"{round_off:+.2f}",
        f"₹{rounded_total:,.2f}"
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        fill_color = "#E6F2FA" if i < 4
