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
# Global selected customer (✅ ye add karna hai)
selected_customer_id = None
selected_customer_name = None

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
# (आपके मौजूदा डेटाबेस सेटअप कोड को यहाँ रखें)
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
if __name__ == "__main__":
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
    print("ℹ️ Rename skipped. Current columns:", columns)

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
        inventory_tree.insert("", "end", values=(item_id, name, category, stock, price, "✏️  🗑️"), tags=(tag,))

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

    # Assume ✏️ takes left half, 🗑️ takes right half
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

            inventory_tree.insert("", "end", values=(item_id, name, category, stock, price, "✏️  🗑️"), tags=(tag,))

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
            existing_columns = [row[1] for row in cursor.fetchall()]
            
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
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
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
    reset_button = tk.Button(button_frame, text="Reset", command=clear_form, style="Custom.TButton")
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
            print(f"⚠️ Error parsing row {idx + 1}: {e} — {product}")
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

# Right-align box: from right edge minus width and width and margin
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
            print(f"⚠️ Error parsing row {idx + 1}: {e} — {product}")
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
        # 🧠 Fetch and show last invoice products for this customer
    customer_id = get_customer_id_by_name_and_phone(customer_name, customer_phone)

    if customer_id:
        last_invoice_id = get_last_invoice_id(customer_id)
        if last_invoice_id:
            last_products = get_products_by_invoice(last_invoice_id)
            print("🧾 Last purchased products:")
            for item in last_products:
                print(item)
        else:
            print("ℹ️ No previous invoices found for this customer.")
    else:
        print("❌ Customer not found.")


    def calculate_gst_summary(products):
        subtotal = 0.0
        for idx, product in enumerate(products):
            try:
                rate = float(str(product[2]).replace("₹", "").strip())
                qty = int(str(product[3]).strip())
                subtotal += rate * qty
            except Exception as e:
                print(f"⚠️ Error in GST calculation for row {idx+1}: {e} — {product}")
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
        print("⚠️ invoice.jpg not found.")
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
        print(f"⚠️ Could not load logo: {e}")

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
                print(f"⚠️ Error in GST calculation for row {idx+1}: {e} — {product}")
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
        print("⚠️ invoice1.jpg not found.")
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
        print(f"⚠️ Could not load logo: {e}")

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

   # Footer Message (No Signature)
    credit_text = "This is a computer-generated invoice. No physical signature is required."
    cr_w = draw.textbbox((0, 0), credit_text, font=font)[2]

# Y-position of the footer text
    footer_y = desc_y + 40

# ✅ Draw full-width horizontal line above the text
    draw.line([(0, footer_y - 10), (img_width, footer_y - 10)], fill="black", width=2)

# Draw the centered footer text
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


def open_invoice_image2(
    customer_name,
    customer_email,
    customer_phone,
    customer_address,
    gstin,
    state_code,
    invoice_number,  # ✅ Already passed, do NOT generate inside
    products=None,
    grand_total=0.0,
    domain="127.0.0.1"
):
    from textwrap import wrap
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    from datetime import datetime
    from num2words import num2words
    import os
    import tkinter as tk
    from tkinter import messagebox

    def calculate_gst_summary(products):
        subtotal = 0.0
        for idx, product in enumerate(products):
            try:
                rate = float(str(product[2]).replace("₹", "").strip())
                qty = int(str(product[3]).strip())
                subtotal += rate * qty
            except Exception as e:
                print(f"⚠️ Error in GST calculation for row {idx+1}: {e} — {product}")
                continue
        sgst = subtotal * 0.09
        cgst = subtotal * 0.09
        gross_total = subtotal + sgst + cgst
        rounded_total = round(gross_total)
        round_off = rounded_total - gross_total
        return subtotal, sgst, cgst, round_off, rounded_total

    products = products or []

    try:
        img = Image.open(resource_path("invoice2.jpg")).convert("RGB") # Use resource_path
    except FileNotFoundError:
        print("⚠️ invoice2.jpg not found.")
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
        print(f"⚠️ Could not load logo: {e}")

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
    title = "Cash Receipt"
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
        "State:- Uttrakhand",
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
    draw.text((info_x, info_y), "Invoice No.:", font=bold_font, fill="black")
    draw.text((info_x + 150, info_y), str(invoice_number), font=font, fill="blue")
    draw.text((info_x, info_y + 35), "Invoice Date", font=bold_font, fill="black")
    draw.text((info_x + 150, info_y + 35), date_str, font=font, fill="blue")

    # Buyer
    section_y = company_y + 10
    draw.text((company_x, section_y), "Buyer (Bill To)", fill=(35, 102, 171), font=bold_font)
    section_y += 22
    draw.text((company_x, section_y), customer_name, font=bold_font, fill="black")
    section_y += 25
    for line in wrap(customer_address or "", width=40)[:2]:
        draw.text((company_x, section_y), line, font=font, fill="black")
        section_y += 25
    draw.text((company_x, section_y), f"State: {state_code}", font=font, fill="black")
    section_y += 30

    # Shipping Address
    draw.text((company_x, section_y), "Consignee (Ship To)", fill=(35, 102, 171), font=bold_font)
    section_y += 35
    draw.text((company_x, section_y), customer_name, font=bold_font, fill="black")
    section_y += 30
    for line in wrap(customer_address or "", width=40)[:2]:
        draw.text((company_x, section_y), line, font=font, fill="black")
        section_y += 25
    draw.text((company_x, section_y), f"State: {state_code}", font=font, fill="black")
    section_y += 45

    # Product Table
    try:
        draw_full_table_blank_rows(draw, font, bold_font, products, start_x=10, start_y=650, bottom_y=1300)
    except Exception as e:
        print("⚠️ Missing draw_full_table_blank_rows function")

    # Amount in Words
    words_y = 1600
    amount_in_words = num2words(grand_total, to='cardinal', lang='en_IN').replace(",", "").title() + " Only"
    draw.text((10, words_y), f"Total Amount (In Words): {amount_in_words}", font=bold_font, fill="black")

    # Description & Declaration
    draw.text((10, words_y + 30), "Description", font=small_font, fill="black")
    desc_text = (
        "We declare that this invoice shows the actual price of the goods/Services described\n"
        "and that all particulars are true and correct."
    )
    desc_y = words_y + 50
    for line in desc_text.split("\n"):
        draw.text((10, desc_y), line, font=small_font, fill="black")
        desc_y += 22

    # Footer line
    line_y = desc_y + 20
    draw.line([(0, line_y), (img_width, line_y)], fill="black", width=2)

    # Footer text
    credit_text = "This is a computer-generated Cash Receipt. No physical signature is required."
    cr_w = draw.textbbox((0, 0), credit_text, font=font)[2]
    text_x = (img_width - cr_w) // 2
    draw.text((text_x, line_y + 5), credit_text, font=font, fill="black")

    # Save PDF
    safe_invoice_number = invoice_number.replace("/", "_")
    os.makedirs(resource_path("invoices"), exist_ok=True) # Use resource_path
    img.save(resource_path(f"invoices/{safe_invoice_number}.pdf"), "PDF", resolution=100.0) # Use resource_path

    # Revenue entry
    subtotal, sgst, cgst, round_off, rounded_total = calculate_gst_summary(products)
    insert_revenue(subtotal)

    # Preview in Tkinter
    img_resized = img.resize((500, 600), Image.LANCZOS)
    preview_window = tk.Toplevel()
    preview_window.title("Invoice Preview")
    preview_window.geometry("595x850")
    tk_image = ImageTk.PhotoImage(img_resized)
    label = tk.Label(preview_window, image=tk_image)
    label.image = tk_image
    label.pack(padx=10, pady=10)
    tk.Button(
        preview_window,
        text="Download Invoice",
        font=("Arial", 11, "bold"),
        bg="#4CAF50",
        fg="white",
        command=lambda: download_invoice2(img, invoice_number)
    ).pack(pady=10)

  

# ---------------------- Number to Words Utility ----------------------
def number_to_words(number):
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Million", "Billion"]

    if number == 0:
        return "Zero"

    def convert_below_thousand(num):
        if num == 0:
            return ""
        elif num < 10:
            return units[num]
        elif num < 20:
            return teens[num - 10] if num != 10 else "Ten"
        elif num < 100:
            return tens[num // 10] + (" " + units[num % 10] if num % 10 else "")
        else:
            return units[int(num) // 100] + " Hundred" + (" and " + convert_below_thousand(int(num) % 100) if int(num) % 100 else "")


    words = []
    chunk_count = 0

    while number > 0:
        chunk = number % 1000
        if chunk:
            chunk_words = convert_below_thousand(chunk)
            if thousands[chunk_count]:
                chunk_words += " " + thousands[chunk_count]
            words.insert(0, chunk_words)
        number //= 1000
        chunk_count += 1

    return " ".join(words).strip()


# ✅ Step 3: Save function
def save_eway_bill():
    eway_bill = entry_eway_bill.get()
    vehicle_no = entry_vehicle_no.get()
    p_marka = entry_p_marka.get()
    reverse_charges = var_reverse_charges.get()

    # Validate the inputs
    if not eway_bill or not vehicle_no or not p_marka:
        messagebox.showerror("Input Error", "Please fill all fields!")
        return

    # Connect to the correct table in the correct database
    conn = sqlite3.connect('company.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO eway_bills (eway_bill, vehicle_no, p_marka, reverse_charges)
        VALUES (?, ?, ?, ?)
    ''', (eway_bill, vehicle_no, p_marka, reverse_charges))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "E-Way Bill details saved successfully!")
    popup_window.destroy()


# Function to open the E-Way Bill popup
def open_eway_bill_popup():
    global popup_window, entry_eway_bill, entry_vehicle_no, entry_p_marka, var_reverse_charges

    popup_window = tk.Toplevel()  # Create a new window (popup)
    popup_window.title("E-Way Bill Entry")

    # Create the form labels and entry fields
    tk.Label(popup_window, text="E-Way Bill No:").grid(row=0, column=0, padx=10, pady=5)
    entry_eway_bill = tk.Entry(popup_window)
    entry_eway_bill.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(popup_window, text="Vehicle No:").grid(row=1, column=0, padx=10, pady=5)
    entry_vehicle_no = tk.Entry(popup_window)
    entry_vehicle_no.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(popup_window, text="P. Marka:").grid(row=2, column=0, padx=10, pady=5)
    entry_p_marka = tk.Entry(popup_window)
    entry_p_marka.grid(row=2, column=1, padx=10, pady=5)

    # Reverse Charges - Yes/No option
    tk.Label(popup_window, text="Reverse Charges:").grid(row=3, column=0, padx=10, pady=5)
    var_reverse_charges = tk.StringVar()
    var_reverse_charges.set("No")  # Default value
    tk.Radiobutton(popup_window, text="Yes", variable=var_reverse_charges, value="Yes").grid(row=3, column=1, padx=10, pady=5)
    tk.Radiobutton(popup_window, text="No", variable=var_reverse_charges, value="No").grid(row=3, column=2, padx=10, pady=5)

    # Save Button
    tk.Button(popup_window, text="Save", command=save_eway_bill).grid(row=4, column=0, columnspan=3, pady=10)

# ---------------------- Billing --------------------------
def show_product_purchase_view(selected_customer_name=None):
    clear_main_frame()

    # Fetch customers from database
    conn = sqlite3.connect("company.db")
    c = conn.cursor()
    c.execute("SELECT id, name, email, phone, customer_address, state_code, gstin FROM customers ORDER BY id DESC")
    customer_list = c.fetchall()
    conn.close()

    # Fetch all items for product selection
    conn = sqlite3.connect("company.db")
    c = conn.cursor()
    c.execute("SELECT item_id, name, category, price, stock FROM items")
    all_items = c.fetchall()
    conn.close()
    item_names = [item[1] for item in all_items] # For combobox

    # --- Customer Selection ---
    customer_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
    customer_frame.pack(anchor="w", pady=(10, 0), padx=20)

    tk.Label(
        customer_frame, 
        text="Select Customer:", 
        font=("Helvetica", 12, "bold"), 
        bg=BACKGROUND_COLOR, 
        fg=TEXT_COLOR
    ).pack(side="left")

    customer_names_dropdown = ["Select a customer"] + [customer[1] for customer in customer_list]
    customer_var = tk.StringVar(value=selected_customer_name if selected_customer_name in customer_names_dropdown else customer_names_dropdown[0])

    customer_dropdown = ttk.Combobox(
        customer_frame, 
        textvariable=customer_var, 
        values=customer_names_dropdown, 
        state="readonly", 
        font=("Helvetica", 10)
    )
    customer_dropdown.pack(side="left", padx=10)

    # --- Customer Info Display ---
    customer_info_label = tk.Label(
        main_frame, 
        text="", 
        bg=BACKGROUND_COLOR, 
        fg=TEXT_COLOR, 
        justify="left", 
        font=("Helvetica", 10)
    )
    customer_info_label.pack(anchor="w", padx=20, pady=(5, 10))

    # --- Old Invoices Display ---
    old_invoices_frame = tk.LabelFrame(main_frame, text="Customer's Old Invoices", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10, "bold"), padx=10, pady=10, bd=2, relief="groove")
    old_invoices_frame.pack(pady=10, fill="x", padx=20)

    old_invoices_tree = ttk.Treeview(old_invoices_frame, columns=("Invoice ID", "Amount", "Date"), show="headings", height=3)
    old_invoices_tree.heading("Invoice ID", text="Invoice ID")
    old_invoices_tree.heading("Amount", text="Amount")
    old_invoices_tree.heading("Date", text="Date")
    old_invoices_tree.column("Invoice ID", width=100, anchor="center")
    old_invoices_tree.column("Amount", width=100, anchor="center")
    old_invoices_tree.column("Date", width=150, anchor="center")
    old_invoices_tree.pack(fill="both", expand=True)

    

    # Product Frame with Scrollbar
    product_frame = tk.LabelFrame(main_frame, text="Add Purchased Products", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10, "bold"), padx=10, pady=10, bd=2, relief="groove")
    product_frame.pack(pady=10, fill="both", expand=True, padx=20)

    tree_frame = tk.Frame(product_frame, bg=BACKGROUND_COLOR)
    tree_frame.pack(fill="both", expand=True)

    columns = ("Item ID", "Name", "SAC", "Price", "Qty", "Discount", "Total", "Actions")

    tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll.pack(side="right", fill="y")

    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=tree_scroll.set, height=5)
    tree_scroll.config(command=tree.yview)

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
    style.configure("Treeview", font=("Helvetica", 10), rowheight=25)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=100) # Adjusted width for better fit
    tree.pack(fill="both", expand=True)

    subtotal_label = tk.Label(product_frame, text="Subtotal: ₹0", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10), anchor="e")
    subtotal_label.pack(anchor="e", pady=2)
   
    total_label = tk.Label(product_frame, text="Grand Total: ₹0", font=("Helvetica", 10, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor="e")
    total_label.pack(anchor="e", pady=(2, 10))

    def update_totals():
        subtotal = 0
        for row_id in tree.get_children():
            val = tree.item(row_id)['values']
            if len(val) >= 7: # Ensure 'Total' column exists
                try:
                    # Total is in the 6th index (0-based)
                    amount_str = str(val[6]).replace("₹", "").strip()
                    amount = float(amount_str)
                    subtotal += amount
                except ValueError:
                    print(f"Warning: Could not parse amount '{val[6]}'")
                    pass
      
        grand = subtotal 
        subtotal_label.config(text=f"Subtotal: ₹{subtotal:,.2f}")
        total_label.config(text=f"Grand Total: ₹{grand:,.2f}")

    # Auto-update customer info and old invoices when selection changes
    def update_customer_info_and_invoices(*args):
        selected_name = customer_var.get()
        customer_id = None
        customer_address = ""
        customer_state_code = ""
        customer_gstin = ""
        
        # Clear current products in treeview
        for item in tree.get_children():
            tree.delete(item)

        if selected_name == "Select a customer":
            customer_info_label.config(text="")
            # Clear old invoices tree
            for item in old_invoices_tree.get_children():
                old_invoices_tree.delete(item)
            old_invoices_tree.insert("", "end", values=("", "Select a customer", ""))
            update_totals() # Reset totals
            return

        for customer in customer_list:
            if customer[1] == selected_name:
                customer_id = customer[0]
                info = f"Email: {customer[2]}\nPhone: {customer[3]}\nAddress: {customer[4]}"
                customer_info_label.config(text=info)
                customer_address = customer[4]
                customer_state_code = customer[5]
                customer_gstin = customer[6]
                break
        
        # Clear previous old invoices
        for item in old_invoices_tree.get_children():
            old_invoices_tree.delete(item)

        if customer_id:
            conn = sqlite3.connect("company.db")
            c = conn.cursor()
            
            # Load past invoices
            c.execute("SELECT id, amount, date FROM invoices_table WHERE customer_id = ? ORDER BY date DESC", (customer_id,))
            past_invoices = c.fetchall()
            if past_invoices:
                for inv_id, inv_amount, inv_date in past_invoices:
                    old_invoices_tree.insert("", "end", values=(inv_id, f"₹{inv_amount:.2f}", inv_date))
            else:
                old_invoices_tree.insert("", "end", values=("", "No past invoices", ""))

            # Load products from the latest invoice for this customer
            c.execute("SELECT id FROM invoices_table WHERE customer_id = ? ORDER BY date DESC LIMIT 1", (customer_id,))
            latest_invoice_id_result = c.fetchone()
            
            if latest_invoice_id_result:
                latest_invoice_id = latest_invoice_id_result[0]
                # Fetch product details including category (SAC) and price from invoice_products
                c.execute("""
                    SELECT ip.product_id, i.name, i.category, ip.price, ip.quantity
                    FROM invoice_products ip
                    JOIN items i ON ip.product_id = i.item_id
                    WHERE ip.invoice_id = ?
                """, (latest_invoice_id,))
                fetched_products = c.fetchall()
                
                # Insert fetched products into the current product treeview
                for item_id, prod_name, category, price, qty in fetched_products:
                    discount = 0 # Assuming no discount stored in invoice_products
                    total = price * qty * (1 - discount / 100)
                    tree.insert("", "end", values=(item_id, prod_name, category, f"₹{price:,.2f}", qty, f"{discount}%", f"₹{total:,.2f}", "🖉 🗑"))
            conn.close()
        update_totals()

    customer_var.trace_add("write", update_customer_info_and_invoices)
    update_customer_info_and_invoices()  # Initialize info on first load

    def edit_product(row_id, values):
        # values: (Item ID, Name, SAC, Price, Qty, Discount, Total, Actions)
        item_id_val = values[0]
        name_val = values[1]
        sac_val = values[2]
        price_val = float(str(values[3]).replace("₹", "").strip())
        qty_val = int(values[4])
        discount_val = float(str(values[5]).replace("%", "").strip())

        popup = tk.Toplevel(main_frame)
        popup.title("Edit Product")
        popup.geometry("350x350")
        popup.configure(bg=SECONDARY_COLOR)

        tk.Label(popup, text="Edit Product", font=("Helvetica", 14, "bold"), bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(pady=10)

        tk.Label(popup, text="Item Name:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        item_name_entry = tk.Entry(popup, font=("Helvetica", 10))
        item_name_entry.insert(0, name_val) # Set initial value
        item_name_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="SAC Code:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        sac_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        sac_entry.insert(0, sac_val)
        sac_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="Price:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        price_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        price_entry.insert(0, price_val)
        price_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="Quantity:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        qty_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        qty_entry.insert(0, qty_val)
        qty_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="Discount (%):", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        discount_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        discount_entry.insert(0, discount_val)
        discount_entry.pack(padx=20, fill="x")

        def update_fields_from_selection(event=None): # Added event parameter
            selected_item_name = item_name_entry.get()
            # Filter item_names based on current input
            filtered_item_names = [name for name in item_names if selected_item_name.lower() in name.lower()]
            
            # Update the list of suggestions (if using a combobox or similar)
            # For a simple Entry, you might need a Listbox for suggestions
            # For now, just update the SAC and Price if a full match is found
            found_item = None
            for item in all_items:
                if item[1].lower() == selected_item_name.lower(): # Exact match
                    found_item = item
                    break
            
            if found_item:
                sac_entry.delete(0, tk.END)
                sac_entry.insert(0, found_item[2]) # category as SAC
                price_entry.delete(0, tk.END)
                price_entry.insert(0, found_item[3]) # price
            else:
                # Clear SAC and Price if no exact match
                sac_entry.delete(0, tk.END)
                price_entry.delete(0, tk.END)

        item_name_entry.bind("<KeyRelease>", update_fields_from_selection) # Bind to KeyRelease

        def save_changes():
            try:
                new_item_name = item_name_entry.get().strip()
                new_sac = sac_entry.get().strip()
                new_price = float(price_entry.get().strip())
                new_qty = int(qty_entry.get().strip())
                new_discount = float(discount_entry.get().strip())

                if new_qty <= 0 or new_price < 0 or new_discount < 0 or new_discount > 100:
                    messagebox.showerror("Invalid Input", "Quantity must be positive, Price and Discount must be non-negative, Discount must be <= 100.")
                    return

                # Get item_id for the selected item name
                selected_item_id = None
                for item in all_items:
                    if item[1] == new_item_name:
                        selected_item_id = item[0]
                        break
                if not selected_item_id:
                    messagebox.showerror("Error", "Selected item not found in inventory.")
                    return

                new_total = new_price * new_qty * (1 - new_discount / 100)
                
                tree.item(row_id, values=(selected_item_id, new_item_name, new_sac, f"₹{new_price:,.2f}", new_qty, f"{new_discount}%", f"₹{new_total:,.2f}", "🖉 🗑"))
                update_totals()
                popup.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for Price, Quantity, and Discount.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        save_btn = tk.Button(popup, text="Save Changes", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, command=save_changes)
        save_btn.pack(pady=10)
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg="#2563EB"))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg=ACCENT_COLOR))

    def on_tree_click(event):
        item_id = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if item_id and column == '#8':  # Action column (now 8th column)
            values = tree.item(item_id)['values']
            menu = tk.Menu(main_frame, tearoff=0)
            menu.add_command(label="Edit", command=lambda: edit_product(item_id, values))
            menu.add_command(label="Delete", command=lambda: (tree.delete(item_id), update_totals()))
            menu.tk_popup(event.x_root, event.y_root)

    tree.bind("<Button-1>", on_tree_click)

    def add_product_row():
        popup = tk.Toplevel(main_frame)
        popup.title("Add Product")
        popup.geometry("350x350")
        popup.configure(bg=SECONDARY_COLOR)

        tk.Label(popup, text="Add New Product", font=("Helvetica", 14, "bold"), bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(pady=10)

        tk.Label(popup, text="Item Name:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        item_name_entry = tk.Entry(popup, font=("Helvetica", 10)) # Changed to Entry
        item_name_entry.pack(padx=20, fill="x")

        # Autocomplete functionality for item_name_entry
        def autocomplete_item_name(event=None):
            current_text = item_name_entry.get().lower()
            if current_text:
                suggestions = [name for name in item_names if current_text in name.lower()]
                if suggestions:
                    # You might want to use a Listbox here for better suggestions display
                    # For now, let's just update the SAC and Price if a match is found
                    found_item = None
                    for item in all_items:
                        if item[1].lower() == current_text: # Exact match
                            found_item = item
                            break
                    if found_item:
                        sac_entry.delete(0, tk.END)
                        sac_entry.insert(0, found_item[2]) # category as SAC
                        price_entry.delete(0, tk.END)
                        price_entry.insert(0, found_item[3]) # price
                    else:
                        sac_entry.delete(0, tk.END)
                        price_entry.delete(0, tk.END)
                else:
                    sac_entry.delete(0, tk.END)
                    price_entry.delete(0, tk.END)
            else:
                sac_entry.delete(0, tk.END)
                price_entry.delete(0, tk.END)

        item_name_entry.bind("<KeyRelease>", autocomplete_item_name)


        tk.Label(popup, text="SAC Code:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        sac_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        sac_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="Price:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        price_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        price_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="Quantity:", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        qty_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        qty_entry.insert(0, "1") # Default quantity
        qty_entry.pack(padx=20, fill="x")

        tk.Label(popup, text="Discount (%):", bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(5,0))
        discount_entry = tk.Entry(popup, font=("Helvetica", 10), bd=1, relief="solid")
        discount_entry.insert(0, "0") # Default discount
        discount_entry.pack(padx=20, fill="x")

        def save_product():
            try:
                item_name = item_name_entry.get().strip()
                sac = sac_entry.get().strip()
                price = float(price_entry.get().strip())
                qty = int(qty_entry.get().strip())
                discount = float(discount_entry.get().strip())

                if not item_name:
                    messagebox.showerror("Input Error", "Please select an item name.")
                    return
                if qty <= 0 or price < 0 or discount < 0 or discount > 100:
                    messagebox.showerror("Invalid Input", "Quantity must be positive, Price and Discount must be non-negative, Discount must be <= 100.")
                    return

                # Get item_id for the selected item name
                selected_item_id = None
                for item in all_items:
                    if item[1] == item_name:
                        selected_item_id = item[0]
                        break
                if not selected_item_id:
                    messagebox.showerror("Error", "Selected item not found in inventory.")
                    return

                total = price * qty * (1 - discount / 100)
                tree.insert("", "end", values=(selected_item_id, item_name, sac, f"₹{price:,.2f}", qty, f"{discount}%", f"₹{total:,.2f}", "🖉 🗑"))
                update_totals()
                popup.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for Price, Quantity, and Discount.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        add_btn = tk.Button(popup, text="Add Product", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, command=save_product)
        add_btn.pack(pady=10)
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg="#2563EB"))
        add_btn.bind("<Leave>", lambda e: add_btn.config(bg=ACCENT_COLOR))

    add_product_button = tk.Button(product_frame, text="+ Add Product", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=5, command=add_product_row)
    add_product_button.pack(anchor="ne", pady=5) # Moved pack here
    add_product_button.bind("<Enter>", lambda e: add_product_button.config(bg="#2563EB"))
    add_product_button.bind("<Leave>", lambda e: add_product_button.config(bg=ACCENT_COLOR))

    eway_bill_button = tk.Button(product_frame, text="E-Way Bill", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=5, command=open_eway_bill_popup)
    eway_bill_button.pack(anchor="ne", pady=5)
    eway_bill_button.bind("<Enter>", lambda e: eway_bill_button.config(bg="#2563EB"))
    eway_bill_button.bind("<Leave>", lambda e: eway_bill_button.config(bg=ACCENT_COLOR))
   
    # Payment Section
    payment_frame = tk.LabelFrame(main_frame, text="Payment Info", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10, "bold"), padx=10, pady=10, bd=2, relief="groove")
    payment_frame.pack(pady=5, fill="x", padx=20)

    tk.Label(payment_frame, text="Payment Method:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).grid(row=0, column=0, sticky="w")
    payment_method = tk.StringVar(value="cash")
    for i, method in enumerate(["card", "cash", "UPI"]):
        tk.Radiobutton(payment_frame, text=method, variable=payment_method, value=method, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).grid(row=0, column=i+1)

    tk.Label(payment_frame, text="Amount Paid:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).grid(row=1, column=0, pady=5, sticky="w")
    amount_paid_entry = tk.Entry(payment_frame, font=("Helvetica", 10), bd=1, relief="solid")
    amount_paid_entry.grid(row=1, column=1, columnspan=2, sticky="we")

    tk.Label(payment_frame, text="Balance:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).grid(row=2, column=0, sticky="w")
    balance_entry = tk.Entry(payment_frame, font=("Helvetica", 10), bd=1, relief="solid")
    balance_entry.grid(row=2, column=1, columnspan=2, sticky="we")

    def show_invoice():
        # Store product data
        product_data = []
        for item_id in tree.get_children():
            values = tree.item(item_id)['values']
            # values: (Item ID, Name, SAC, Price, Qty, Discount, Total, Actions)
            # We need: (product_id, name, category, price, quantity) for invoice_products table
            # And for image: (name, SAC, price, qty)
            product_data.append((values[0], values[1], float(str(values[3]).replace("₹", "").strip()), int(values[4]))) # (item_id, name, price, qty)
            
        # Store totals and payment info
        total_amount_str = total_label.cget("text").split("₹")[1].replace(",", "").strip()
        invoice_amount = float(total_amount_str)
        
        amount_paid_val = amount_paid_entry.get().strip()
        if not amount_paid_val:
            amount_paid_val = str(invoice_amount) # Default to total if not entered
        try:
            amount_paid_float = float(amount_paid_val)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for Amount Paid.")
            return

        # Get selected customer details
        selected_customer_name = customer_var.get()
        customer_details = None
        if selected_customer_name == "Select a customer":
            # Use a predefined test customer or create one if it doesn't exist
            conn = sqlite3.connect("company.db")
            c = conn.cursor()
            c.execute("SELECT id, name, email, phone, customer_address, state_code, gstin FROM customers WHERE name = 'Test Customer' LIMIT 1")
            test_customer = c.fetchone()
            if not test_customer:
                c.execute("INSERT INTO customers (name, email, phone, customer_address, state_code, gstin) VALUES (?, ?, ?, ?, ?, ?)",
                          ('Test Customer', 'test@example.com', '1234567890', 'Test Address, Test City', '00', 'NOTAPPLICABLE'))
                conn.commit()
                c.execute("SELECT id, name, email, phone, customer_address, state_code, gstin FROM customers WHERE name = 'Test Customer' LIMIT 1")
                test_customer = c.fetchone()
            conn.close()
            customer_details = test_customer
        else:
            for cust in customer_list:
                if cust[1] == selected_customer_name:
                    customer_details = cust
                    break
        
        if not customer_details:
            messagebox.showerror("Customer Error", "Please select a valid customer.")
            return

        customer_id, name, email, phone, address, state_code, gstin = customer_details

        # Insert into invoices_table
        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        invoice_date_db = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO invoices_table (customer_id, amount, date, status) VALUES (?, ?, ?, ?)",
                  (customer_id, invoice_amount, invoice_date_db, 'paid'))
        invoice_id = c.lastrowid # Get the ID of the newly inserted invoice
        conn.commit()

        # Insert into invoice_products table
        # product_data contains (item_id, name, price, qty)
        for item_id, prod_name, price, qty in product_data:
            c.execute("INSERT INTO invoice_products (invoice_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                      (invoice_id, item_id, qty, price)) # Use item_id as product_id
        conn.commit()
        conn.close()

        # Prepare product data for image generation (name, SAC, price, qty)
        products_for_image = []
        for item_id, prod_name, price, qty in product_data:
            # Fetch SAC (category) from items table using item_id
            conn = sqlite3.connect("company.db")
            c = conn.cursor()
            c.execute("SELECT category FROM items WHERE item_id = ?", (item_id,))
            sac_code = c.fetchone()[0] if c.fetchone() else ""
            conn.close()
            products_for_image.append((prod_name, sac_code, price, qty))


        # Clear the main frame before displaying the invoice
        clear_main_frame()

        # Create a new frame for the invoice within main_frame
        invoice_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        invoice_frame.pack(fill="both", expand=True)

        # Top Buttons (Print, Download, Share)
        btn_frame = tk.Frame(invoice_frame, bg=BACKGROUND_COLOR)
        btn_frame.pack(anchor="ne", padx=20, pady=5)

        print_btn = tk.Button(
            btn_frame,
            text="TaxSign",
            font=("Helvetica", 10),
            bg=ACCENT_COLOR,
            fg=SECONDARY_COLOR,
            bd=0,
            pady=5,
            command=lambda: open_invoice_image(
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                customer_address=address,
                gstin=gstin,
                state_code=state_code,
                invoice_number=get_next_invoice_number(),
                products=products_for_image, # Pass products with SAC
                grand_total=invoice_amount
            )
        )
        print_btn.pack(side="left", padx=5)
        print_btn.bind("<Enter>", lambda e: print_btn.config(bg="#2563EB"))
        print_btn.bind("<Leave>", lambda e: print_btn.config(bg=ACCENT_COLOR))

        download_btn = tk.Button(
            btn_frame,
            text="TaxInvoice",
            font=("Helvetica", 10),
            bg=ACCENT_COLOR,
            fg=SECONDARY_COLOR,
            bd=0,
            pady=5,
            command=lambda: open_invoice_image1(
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                customer_address=address,
                gstin=gstin,
                state_code=state_code,
                invoice_number=get_next_invoice_number(),
                products=products_for_image, # Pass products with SAC
                grand_total=invoice_amount
            )
        )
        download_btn.pack(side="left", padx=5)
        download_btn.bind("<Enter>", lambda e: download_btn.config(bg="#2563EB"))
        download_btn.bind("<Leave>", lambda e: download_btn.config(bg=ACCENT_COLOR))

        back_btn = tk.Button(
            btn_frame,
            text="Back",
            font=("Helvetica", 10),
            bg="#777",
            fg=SECONDARY_COLOR,
            bd=0,
            pady=5,
            command=lambda: show_product_purchase_view(selected_customer_name=selected_customer_name)
        )
        back_btn.pack(side="left", padx=5)
        back_btn.bind("<Enter>", lambda e: back_btn.config(bg="#555"))
        back_btn.bind("<Leave>", lambda e: back_btn.config(bg="#777"))

        signature_btn = tk.Button(
            btn_frame,
            text="CashReceipt",
            font=("Helvetica", 10),
            bg="#777",
            fg=SECONDARY_COLOR,
            bd=0,
            pady=5,
            command=lambda: open_invoice_image2(
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                customer_address=address,
                gstin=gstin, # Cash receipt might not need GSTIN, but passing it for consistency
                state_code=state_code,
                invoice_number=get_simple_invoice_number(),
                products=products_for_image, # Pass products with SAC
                grand_total=invoice_amount
            )
        )
        signature_btn.pack(side="left", padx=5)
        signature_btn.bind("<Enter>", lambda e: signature_btn.config(bg="#555"))
        signature_btn.bind("<Leave>", lambda e: signature_btn.config(bg="#777"))

        # Header Section
        tk.Label(invoice_frame, text="Invoice", font=("Helvetica", 18, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(pady=(20, 10))

        # Box for From and Invoice Details Section
        details_box = tk.LabelFrame(invoice_frame, text="Invoice Information", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10, "bold"), padx=10, pady=10, bd=2, relief="groove")
        details_box.pack(fill="x", padx=40, pady=10)

        header_frame = tk.Frame(details_box, bg=BACKGROUND_COLOR)
        header_frame.pack(fill="x")

        from_frame = tk.Frame(header_frame, bg=BACKGROUND_COLOR)
        from_frame.pack(side="left", anchor="nw")

        from_text = f"""Bill From:
Novanectar Services Private Limited
Khasra No. 1336/3/1 Haripuram, Kanwali GMS Road,
Dehradun, Uttarakand-248001
Mob:- +91 8979891703
E-Mail:- account@novanectar.co.in
Bill To: {name}
{address}"""
        tk.Label(from_frame, text=from_text.strip(), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, justify="left", font=("Helvetica", 10)).pack(anchor="w")

        details_frame = tk.Frame(header_frame, bg=BACKGROUND_COLOR)
        details_frame.pack(side="right", anchor="ne")

        details_text = f"""Invoice Details:
Date: {datetime.now().strftime("%d/%m/%Y")}
Payment Method: {payment_method.get()}"""
        tk.Label(details_frame, text=details_text.strip(), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, justify="right", font=("Helvetica", 10)).pack(anchor="e")

        # Product Table (Display only, not interactive)
        prod_frame = tk.LabelFrame(
           invoice_frame,
           text="Product Details",
           bg=BACKGROUND_COLOR,
           fg=TEXT_COLOR,
           font=("Helvetica", 10, "bold"),
           padx=5,
           pady=5,
           bd=1,
           relief="groove"
        )
        prod_frame.pack(padx=10, pady=10)

        headers = ["Item ID", "Name", "SAC", "Price", "Qty", "Discount", "Total"]
        col_widths = [10, 20, 10, 10, 5, 10, 10] # Adjusted for display
        for i, header in enumerate(headers):
            tk.Label(prod_frame, text=header, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10, "bold"), width=col_widths[i], anchor="w").grid(row=0, column=i, padx=5, pady=5)
            tk.Frame(prod_frame, bg=TEXT_COLOR, height=1).grid(row=1, column=i, sticky="ew", padx=5)

        for i, values in enumerate(tree.get_children(), start=2):
            row_values = tree.item(values)['values']
            # row_values: (Item ID, Name, SAC, Price, Qty, Discount, Total, Actions)
            for j, val in enumerate(row_values[:7]): # Display all but 'Actions'
                tk.Label(prod_frame, text=str(val), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10), width=col_widths[j], anchor="w").grid(row=i, column=j, padx=5, pady=5)

        # Totals Section
        totals_frame = tk.Frame(invoice_frame, bg=BACKGROUND_COLOR)
        totals_frame.pack(fill="x", padx=40, pady=10)

        tk.Label(totals_frame, text=f"Subtotal: ₹{invoice_amount:,.2f}", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10), anchor="e").pack(anchor="e")
        tk.Label(totals_frame, text=f"Grand Total: ₹{invoice_amount:,.2f}", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 12, "bold"), anchor="e").pack(anchor="e", pady=(5, 10))

        # In Words and Amount Paid Section
        words_frame = tk.Frame(invoice_frame, bg=BACKGROUND_COLOR)
        words_frame.pack(fill="x", padx=40, pady=0)

        words = number_to_words(int(invoice_amount))
        tk.Label(words_frame, text=f"In Words: {words.title()}", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10), anchor="w").pack(anchor="w", pady=5)

        tk.Label(words_frame, text=f"Amount Paid: ₹{amount_paid_float:,.2f}", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10), anchor="w").pack(anchor="w", pady=5)

        # Thank You Message
        tk.Label(invoice_frame, text="Thank you for your purchase!!", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10, "italic")).pack(pady=0)

    # Bill Button
    bill_btn = tk.Button(payment_frame, text="Generate Bill", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=5, command=show_invoice)
    bill_btn.grid(row=3, column=0, columnspan=3, pady=5)
    bill_btn.bind("<Enter>", lambda e: bill_btn.config(bg="#2563EB"))
    bill_btn.bind("<Leave>", lambda e: bill_btn.config(bg=ACCENT_COLOR))

    payment_frame.columnconfigure(1, weight=1)
    payment_frame.columnconfigure(2, weight=1)


# ---------------------- Dashboard Data Loading ----------------------
# ---------------------- Dashboard Content ----------------------
def load_dashboard_data():
    global metrics, transactions, revenue_by_month
    metrics = {
        "revenue": 0,
        "pending": 0,
        "customers": 0,
        "inventory": 0
    }
    transactions = []
    revenue_by_month = [0] * 12

    try:
        conn = sqlite3.connect("company.db")
        c = conn.cursor()

        c.execute("SELECT SUM(amount) FROM revenue_table")
        metrics["revenue"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM invoices_table WHERE status='pending'")
        metrics["pending"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM customers")
        metrics["customers"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM items")
        metrics["inventory"] = c.fetchone()[0]

        c.execute("""SELECT name, amount, date FROM invoices_table
                     JOIN customers ON invoices_table.customer_id = customers.id
                     ORDER BY date DESC LIMIT 5""") # Corrected JOIN condition
        transactions = c.fetchall()

        c.execute("SELECT strftime('%m', date), SUM(amount) FROM revenue_table GROUP BY strftime('%m', date)")
        rows = c.fetchall()
        for m, amt in rows:
            revenue_by_month[int(m) - 1] = amt

        conn.close()
    except Exception as e:
        print("Error loading dashboard data:", e)
# ---------------------- Updated show_dashboard_view ----------------------
def show_dashboard_view():
    clear_main_frame()
    load_dashboard_data()

    # --- Dashboard Header with Title + Buttons ---
    header_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
    header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=(10, 0))

    # Title on left
    tk.Label(header_frame, text="Dashboard", font=("Helvetica", 16, "bold"),
             bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(side="left")

    # Buttons grouped on right
    button_frame = tk.Frame(header_frame, bg=BACKGROUND_COLOR)
    button_frame.pack(side="right")

    export_btn = tk.Button(button_frame, text="Export Reports", font=("Helvetica", 10), bg=SECONDARY_COLOR,
                           fg=PRIMARY_COLOR, relief="groove", padx=10, pady=5)

    export_btn.pack(side="left", padx=5)

    invoice_btn = tk.Button(button_frame, text="New Invoice", font=("Helvetica", 10), bg=ACCENT_COLOR,
                            fg=SECONDARY_COLOR, padx=10, pady=5, command=show_product_purchase_view)
    invoice_btn.pack(side="left", padx=5)

    # Metric Cards
    card_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
    card_frame.grid(row=1, column=0, columnspan=1, pady=10)

    icon_list = ["💰", "📄", "👥", "📦"]
    label_list = ["Total Revenue", "Pending Invoices", "Total Customers", "Inventory Items"]
    value_list = [metrics["revenue"], metrics["pending"], metrics["customers"], metrics["inventory"]]
    color_list = [colors['card_green'], colors['card_blue'], colors['card_yellow'], colors['card_red']]

    for i in range(4):
        card = tk.Frame(card_frame, bg=color_list[i], width=100, height=130)
        card.grid(row=0, column=i, padx=10)
        card.pack_propagate(False)

        tk.Label(card, text=icon_list[i], font=('Arial', 22), bg=color_list[i], fg='white').pack(pady=(15, 5))
        tk.Label(card, text=f"{value_list[i]:,}", font=('Arial', 22, 'bold'), bg=color_list[i], fg='white').pack()
        tk.Label(card, text=label_list[i], font=('Arial', 10), bg=color_list[i], fg='white').pack()

    split_frame = tk.Frame(main_frame, bg="#f1f5f9")
    split_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=20, pady=10)

    # Make columns flexible
    split_frame.columnconfigure(0, weight=3)  # Wider for graph
    split_frame.columnconfigure(1, weight=1)  # Narrower for transactions

    # Make the row flexible too
    split_frame.rowconfigure(0, weight=1)

    # Left: Graph Frame
    chart_frame = tk.Frame(split_frame, bg=BACKGROUND_COLOR)
    chart_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    revenue_lakh = [r / 100000 for r in revenue_by_month]

    fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
    ax.plot(months, revenue_lakh, color='#3B82F6', marker='o', linewidth=2)
    ax.fill_between(months, revenue_lakh, color='#3B82F6', alpha=0.2)
    ax.set_ylabel("Revenue (₹ Lakh)")
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

    # 🧾 Recent Transactions (right)
    trans_frame = tk.Frame(split_frame, bg=colors['white'], bd=1, relief="solid")
    trans_frame.grid(row=0, column=1, sticky='nsew')

    tk.Label(trans_frame, text="Recent Transactions", font=('Arial', 14, 'bold'),
             bg=colors['white'], fg=colors['text_dark']).pack(anchor='w', padx=10, pady=10)

    if not transactions:
        tk.Label(trans_frame, text="No transactions found.",
                 bg=colors['white'], fg="gray", font=('Arial', 10, 'italic')).pack(padx=10)
    else:
        for name, amount, date in transactions:
            row = tk.Frame(trans_frame, bg=colors['white'])
            row.pack(fill='x', padx=10, pady=4)
            tk.Label(row, text=name[:2].upper(), width=3, bg="#3B82F6", fg="white",
                     font=('Arial', 10, 'bold')).pack(side='left', padx=5)
            tk.Label(row, text=name, font=('Arial', 10), bg=colors['white']).pack(side='left', padx=5)
            tk.Label(row, text=f"₹{amount}", font=('Arial', 10), bg=colors['white']).pack(side='right', padx=5)
            tk.Label(row, text=date, font=('Arial', 9), bg=colors['white'], fg='gray').pack(side='right')

# ---------------------- Customer Popup ----------------------
def open_add_customer_popup():
    popup = tk.Toplevel()
    popup.title("Add New Customer")
    popup.geometry("400x550")
    popup.configure(bg=SECONDARY_COLOR)

    def save_customer(add_products=False):
        name = name_entry.get().strip()
        email = email_entry.get().strip()
        phone = phone_entry.get().strip()
        address_line1 = customer_address_entry.get().strip()
        state_code = state_code_entry.get().strip()
        gstin = gstin_entry.get().strip()

        if not name or not email or not phone or not address_line1:
            messagebox.showerror("Error", "Name, Email, Phone, and Address are required.")
            return

        # Save to database
        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO customers (name, email, phone, gstin, state_code, customer_address) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, phone, gstin, state_code, address_line1)
        )
        conn.commit()
        conn.close()

        popup.destroy()
        show_customer_details()

        if add_products:
           popup.destroy()  # 🟢 Customer form band karo
           show_product_purchase_view(name)  # 🟢 Direct name pass karo


    # --- UI FORM FIELDS ---
    tk.Label(popup, text="Add New Customer", font=("Helvetica", 14, "bold"), bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(pady=10)

    fields = [
        ("Name*", "name_entry"),
        ("Email*", "email_entry"),
        ("Phone*", "phone_entry"),
        ("Address*", "customer_address_entry")
    ]

    entries = {}
    for label_text, var_name in fields:
        tk.Label(popup, text=label_text, bg=SECONDARY_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(pady=(10, 0))
        entry = tk.Entry(popup, width=40, font=("Helvetica", 10), bd=1, relief="solid")
        entry.pack(pady=5)
        entries[var_name] = entry

    # Assign entry widgets to variables
    name_entry = entries["name_entry"]
    email_entry = entries["email_entry"]
    phone_entry = entries["phone_entry"]
    customer_address_entry = entries["customer_address_entry"]

    # State Code
    tk.Label(popup, text="State Code:", font=("Helvetica", 10), bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(pady=(10, 0))
    state_code_entry = tk.Entry(popup, font=("Helvetica", 10), width=25, justify='center')
    state_code_entry.pack(pady=(0, 10))

    # GSTIN
    tk.Label(popup, text="GSTIN:", font=("Helvetica", 10), bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(pady=(0, 0))
    gstin_entry = tk.Entry(popup, font=("Helvetica", 10), width=40, justify='center')
    gstin_entry.pack(pady=(0, 10))

    # --- BUTTONS ---
    btn_frame = tk.Frame(popup, bg=SECONDARY_COLOR)
    btn_frame.pack(pady=20)

    def styled_button(widget, normal, hover):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal))

    cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Helvetica", 10), bg="#D1D5DB", fg=TEXT_COLOR, bd=0, pady=5, command=popup.destroy)
    cancel_btn.pack(side="left", padx=10)
    styled_button(cancel_btn, "#D1D5DB", "#B0B5BB")

    save_btn = tk.Button(btn_frame, text="Save Customer", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=5, command=lambda: save_customer(False))
    save_btn.pack(side="left", padx=10)
    styled_button(save_btn, ACCENT_COLOR, "#2563EB")

    add_prod_btn = tk.Button(btn_frame, text="Add Products", font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=5, command=lambda: save_customer(True))
    add_prod_btn.pack(side="left", padx=10)
    styled_button(add_prod_btn, ACCENT_COLOR, "#2563EB")


def view_customer_old_records(customer_id, customer_name):
    """
    Displays a list of old invoices/records for a specific customer.
    """
    records_window = tk.Toplevel()
    records_window.title(f"Old Records for {customer_name}")
    records_window.geometry("800x600")
    records_window.configure(bg=BACKGROUND_COLOR)

    tk.Label(records_window, text=f"Invoices for {customer_name}", font=("Helvetica", 16, "bold"),
             bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(pady=10)

    tree_frame = tk.Frame(records_window, bg=BACKGROUND_COLOR)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

    columns = ("Invoice ID", "Amount", "Date", "Status", "Products") # Added Products column
    records_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

    for col in columns:
        records_tree.heading(col, text=col)
        records_tree.column(col, anchor="center", width=150)
    
    records_tree.pack(fill="both", expand=True)

    # Fetch invoices for the selected customer
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, date, status FROM invoices_table WHERE customer_id = ?", (customer_id,))
    invoices = cursor.fetchall()
    conn.close()

    if not invoices:
        tk.Label(records_window, text="No old invoices found for this customer.",
                 bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Helvetica", 12)).pack(pady=20)
    else:
        for inv_id, inv_amount, inv_date, inv_status in invoices:
            # Fetch products for each invoice
            products_in_invoice = get_products_by_invoice(inv_id)
            product_summary = ", ".join([f"{p[1]} (x{p[3]})" for p in products_in_invoice]) # p[1]=name, p[3]=quantity
            if not product_summary:
                product_summary = "N/A"
            records_tree.insert("", "end", values=(inv_id, f"₹{inv_amount:.2f}", inv_date, inv_status, product_summary))

    tk.Button(records_window, text="Close", command=records_window.destroy,
              font=("Helvetica", 10), bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=5).pack(pady=10)


def show_customer_details():
    clear_main_frame()

    # ✅ Fetch customers from database with correct column names
    conn = sqlite3.connect("company.db")
    c = conn.cursor()
    c.execute("SELECT id, name, email, phone, customer_address FROM customers ORDER BY id DESC")
    customer_list = c.fetchall()
    conn.close()

    # ✅ Create a responsive layout with frames
    outer_frame = tk.Frame(main_frame, bg="#F9FAFB")
    outer_frame.pack(fill="both", expand=True)
    
    outer_frame.grid_rowconfigure(0, weight=1)
    outer_frame.grid_columnconfigure(0, weight=1)

    customer_card = tk.Frame(outer_frame, bg="white", bd=1, relief="solid")
    customer_card.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    
    customer_card.grid_rowconfigure(3, weight=1)
    customer_card.grid_columnconfigure(0, weight=1)

    header_row = tk.Frame(customer_card, bg="white")
    header_row.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
    header_row.grid_columnconfigure(1, weight=1)

    title = tk.Label(header_row, text="Customers", font=("Helvetica", 18, "bold"),
                     bg="white", fg="#1F2937")
    title.grid(row=0, column=0, sticky="w")

    add_btn = tk.Button(header_row, text="Add Customer", bg="#3B82F6", fg="white",
                        font=("Helvetica", 10, "bold"), padx=12, pady=6, bd=0,
                        command=open_add_customer_popup, cursor="hand2", relief="flat")
    add_btn.grid(row=0, column=2, sticky="e")


    
    def on_enter(e):
        add_btn['background'] = '#2563EB'
    
    def on_leave(e):
        add_btn['background'] = '#3B82F6'
        
    add_btn.bind("<Enter>", on_enter)
    add_btn.bind("<Leave>", on_leave)

    search_frame = tk.Frame(customer_card, bg="white")
    search_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
    search_frame.grid_columnconfigure(0, weight=1)

    search_container = tk.Frame(search_frame, bg="#F3F4F6", bd=1, relief="solid")
    search_container.grid(row=0, column=0, sticky="ew")
    search_container.grid_columnconfigure(1, weight=1)

    search_icon = tk.Label(search_container, text="🔍", bg="#F3F4F6", font=("Helvetica", 11))
    search_icon.grid(row=0, column=0, padx=(8, 0), pady=6)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_container, textvariable=search_var, font=("Helvetica", 11),
                         bd=0, bg="#F3F4F6", highlightthickness=0)
    search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 8), pady=6)
    search_entry.insert(0, "Search customer by name, email")
    search_entry.config(fg="grey")
    
    def on_entry_click(event):
        if search_entry.get() == "Search customer by name, email":
            search_entry.delete(0, "end")
            search_entry.config(fg="#1F2937")

    def on_focusout(event):
        if not search_entry.get():
            search_entry.insert(0, "Search customer by name, email")
            search_entry.config(fg="grey")

    def filter_customers(event=None):
        search_text = search_var.get().lower()
        if not search_text or search_text == "search customer by name, email":
            draw_rows(customer_list)
            return
            
        filtered_list = []
        for customer in customer_list:
            if (search_text in customer[1].lower() or 
                search_text in customer[2].lower()):
                filtered_list.append(customer)
        
        draw_rows(filtered_list)
        detail_title.config(text=f"Customers Detail ({len(filtered_list)})")

    search_entry.bind("<FocusIn>", on_entry_click)
    search_entry.bind("<FocusOut>", on_focusout)
    search_entry.bind("<KeyRelease>", filter_customers)

    detail_header = tk.Frame(customer_card, bg="white")
    detail_header.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 8))
    detail_header.grid_columnconfigure(0, weight=1)

    detail_title = tk.Label(detail_header, text=f"Customers Detail ({len(customer_list)})",
                         font=("Helvetica", 13, "bold"), bg="white", fg="#1F2937")
    detail_title.grid(row=0, column=0, sticky="w")

    icons_frame = tk.Frame(detail_header, bg="white")
    icons_frame.grid(row=0, column=1, sticky="e")

    view_icon = tk.Label(icons_frame, text="☰", font=("Helvetica", 12), bg="white", 
                       padx=5, cursor="hand2", fg="#4B5563")
    view_icon.pack(side="right")
    
    more_icon = tk.Label(icons_frame, text="⋮", font=("Helvetica", 14), bg="white", 
                       padx=5, cursor="hand2", fg="#4B5563")
    more_icon.pack(side="right")

    table_container = tk.Frame(customer_card, bg="#F9FAFB", bd=1, relief="solid")
    table_container.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0, 15))
    table_container.grid_rowconfigure(0, weight=1)
    table_container.grid_columnconfigure(0, weight=1)

    table_frame = tk.Frame(table_container, bg="white")
    table_frame.grid(row=0, column=0, sticky="nsew")
    table_frame.grid_rowconfigure(1, weight=1)
    
    column_weights = [20, 25, 15, 30, 10]
    for i, weight in enumerate(column_weights):
        table_frame.grid_columnconfigure(i, weight=weight)

    header_labels = ["Name", "Email", "Phone", "Address", "Actions"]
    for col, text in enumerate(header_labels):
        header_bg = "#F3F4F6"
        header_fg = "#4B5563"
        header_font = ("Helvetica", 11, "bold")
        
        header_cell = tk.Frame(table_frame, bg=header_bg)
        header_cell.grid(row=0, column=col, sticky="nsew")
        header_cell.grid_columnconfigure(0, weight=1)
        
        lbl = tk.Label(header_cell, text=text, font=header_font,
                     bg=header_bg, fg=header_fg, anchor="w", padx=15, pady=12)
        lbl.grid(row=0, column=0, sticky="w")
        
        separator = tk.Frame(table_frame, height=1, bg="#E5E7EB")
        separator.grid(row=0, column=col, sticky="ews", pady=(32, 0))

    body_canvas_frame = tk.Frame(table_frame)
    body_canvas_frame.grid(row=1, column=0, columnspan=len(header_labels), sticky="nsew")
    body_canvas_frame.grid_rowconfigure(0, weight=1)
    body_canvas_frame.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(body_canvas_frame, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(body_canvas_frame, orient="vertical", command=canvas.yview)
    
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
    for i, weight in enumerate(column_weights):
        scrollable_frame.grid_columnconfigure(i, weight=weight)
    
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(scrollable_window, width=canvas.winfo_width())
        
    canvas.bind("<Configure>", lambda e: on_configure(e))
    scrollable_frame.bind("<Configure>", on_configure)
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    canvas.bind_all("<MouseWheel>", _on_mousewheel) # Corrected this line

    def draw_rows(data_list=None):
        if data_list is None:
            conn = sqlite3.connect("company.db")
            c = conn.cursor()
            c.execute("SELECT id, name, email, phone, customer_address FROM customers ORDER BY id DESC")
            data_list = c.fetchall()
            conn.close()

        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        row_colors = ["white", "#F9FAFB"]

        for idx, customer in enumerate(data_list):
            row_bg = row_colors[idx % 2]
            values = customer[1:5]  # Skip id

            for col, val in enumerate(values):
                cell_frame = tk.Frame(scrollable_frame, bg=row_bg)
                cell_frame.grid(row=idx, column=col, sticky="nsew")
                cell_frame.grid_columnconfigure(0, weight=1)

                lbl = tk.Label(cell_frame, text=val, font=("Helvetica", 10),
                               bg=row_bg, fg="#374151", anchor="w", padx=5, pady=15)
                lbl.grid(row=0, column=0, sticky="w")

                border = tk.Frame(cell_frame, height=1, bg="#E5E7EB")
                border.grid(row=1, column=0, sticky="ew")

            action_cell = tk.Frame(scrollable_frame, bg=row_bg)
            action_cell.grid(row=idx, column=4, sticky="nsew")

            actions_container = tk.Frame(action_cell, bg=row_bg)
            actions_container.pack(pady=6)

            view_btn = tk.Label(actions_container, text="👁", font=("Helvetica", 11),
                                bg=row_bg, fg="#3B82F6", cursor="hand2", padx=4)
            view_btn.pack(side="left")
            view_btn.bind("<Button-1>", lambda e, i=customer[0]: view_customer_details(i))

            edit_btn = tk.Label(actions_container, text="✏", font=("Helvetica", 11),
                                bg=row_bg, fg="#3B82F6", cursor="hand2", padx=4)
            edit_btn.pack(side="left")
            edit_btn.bind("<Button-1>", lambda e: show_product_purchase_view(selected_customer_name=customer[1]))

            delete_btn = tk.Label(actions_container, text="🗑", font=("Helvetica", 11),
                                  bg=row_bg, fg="#3B82F6", cursor="hand2", padx=4)
            delete_btn.pack(side="left")
            delete_btn.bind("<Button-1>", lambda e, i=customer[0]: delete_customer(i))

            # New button for old records
            old_records_btn = tk.Button(actions_container, text="📜 View", font=("Helvetica", 10),
                            bg=row_bg, fg="#3B82F6", cursor="hand2",
                            command=lambda cust_id=customer[0], cust_name=customer[1]: view_customer_old_records(cust_id, cust_name))
            old_records_btn.pack(side="left")



            checkbox_text = "☑" if idx in selected_customers else "☐"
            checkbox = tk.Label(actions_container, text=checkbox_text, font=("Helvetica", 13),
                                bg=row_bg, fg="#3B82F6", cursor="hand2", padx=4)
            checkbox.pack(side="left")
            checkbox.bind("<Button-1>", lambda e, i=idx: toggle_checkbox(i))

            border = tk.Frame(action_cell, height=1, bg="#E5E7EB")
            border.pack(side="bottom", fill="x")
    
    def toggle_checkbox(idx):
        if idx in selected_customers:
            selected_customers.remove(idx)
        else:
            selected_customers.add(idx)
        draw_rows()

    def view_customer_details(customer_id):
        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        c.execute("SELECT name, email, phone, customer_address FROM customers WHERE id = ?", (customer_id,))
        customer = c.fetchone()
        conn.close()
        if customer:
            messagebox.showinfo("Customer Details", f"Name: {customer[0]}\nEmail: {customer[1]}\nPhone: {customer[2]}\nAddress: {customer[3]}")

    def delete_customer(customer_id):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this customer?")
        if not confirm:
            return
        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        conn.close()
        selected_customers.clear()
        draw_rows()
        # Recalculate customer_list length after deletion
        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        c.execute("SELECT id FROM customers")
        updated_customer_count = len(c.fetchall())
        conn.close()
        detail_title.config(text=f"Customers Detail ({updated_customer_count})")

    def delete_selected():
        if not selected_customers:
            return

        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        for idx in sorted(selected_customers, reverse=True):
            if idx < len(customer_list):
                c.execute("DELETE FROM customers WHERE id = ?", (customer_list[idx][0],))
        conn.commit()
        conn.close()

        selected_customers.clear()
        draw_rows()
        # Recalculate customer_list length after deletion
        conn = sqlite3.connect("company.db")
        c = conn.cursor()
        c.execute("SELECT id FROM customers")
        updated_customer_count = len(c.fetchall())
        conn.close()
        detail_title.config(text=f"Customers Detail ({updated_customer_count})")

    draw_rows()



# ---------------------- Clear Main Frame ----------------------
def clear_main_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()

# ---------------------- Login Page ----------------------

def show_login_screen():
    global root, email_entry, password_entry

    root = tk.Tk()
    root.title("Login Page")
    root.state('zoomed')
    root.configure(bg="#FFFFFF")  # pure white background
    form_frame = tk.Frame(root, bg="#FFFFFF")
    form_frame.place(relx=0.5, rely=0.5, anchor="center")  # Centered in entire window

    # === Load and show logo ===
    logo_path = resource_path("nova.png")  # Safe path handling for .exe

    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((256, 75), Image.LANCZOS)  # Resize if needed
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(form_frame, image=logo_photo, bg=SECONDARY_COLOR)
            logo_label.image = logo_photo  # Prevent garbage collection
            logo_label.pack(pady=(0, 10))
        except Exception as e:
            print("Error loading logo:", e)
            tk.Label(form_frame, text="🧾", font=("Helvetica", 50), bg=SECONDARY_COLOR, fg=PRIMARY_COLOR).pack(pady=(0, 10))
    else:
        print("Logo not found:", logo_path)
        tk.Label(form_frame, text="🧾", font=("Helvetica", 50), bg=SECONDARY_COLOR, fg=PRIMARY_COLOR).pack(pady=(0, 10))

    # === App Title ===
    tk.Label(form_frame, text="NN Billing System", font=("Helvetica", 19, "bold"), fg=PRIMARY_COLOR, bg=SECONDARY_COLOR).pack(pady=(0, 10))
    tk.Label(form_frame, text="Login to continue", font=("Helvetica", 14), bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack()

    # === Company Email ===
    email_frame = tk.Frame(form_frame, bg=SECONDARY_COLOR)
    email_frame.pack(pady=(0, 15))  # Space between fields

    tk.Label(email_frame, text="Admin Email / UserName", font=("Helvetica", 10), 
             bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(anchor="w")
    email_entry = tk.Entry(email_frame, width=40, font=("Helvetica", 10), 
                           bd=1, relief="solid")
    email_entry.pack(pady=(5, 0))

    # === Password ===
    password_frame = tk.Frame(form_frame, bg=SECONDARY_COLOR)
    password_frame.pack(pady=(0, 15))

    tk.Label(password_frame, text="Password", font=("Helvetica", 10), 
             bg=SECONDARY_COLOR, fg=TEXT_COLOR).pack(anchor="w")
    password_entry = tk.Entry(password_frame, show="*", width=40, font=("Helvetica", 10), 
                              bd=1, relief="solid")
    password_entry.pack(pady=(5, 0))

    # === Sign In Button ===
    btn_frame = tk.Frame(form_frame, bg=SECONDARY_COLOR)
    btn_frame.pack(pady=(10, 0))

    signin_btn = tk.Button(btn_frame, text="Sign in", width=30, font=("Helvetica", 10, "bold"),
                           bg=ACCENT_COLOR, fg=SECONDARY_COLOR, bd=0, pady=6, command=on_signin)
    signin_btn.pack()

    # Hover effects
    signin_btn.bind("<Enter>", lambda e: signin_btn.config(bg="#2563EB"))
    signin_btn.bind("<Leave>", lambda e: signin_btn.config(bg=ACCENT_COLOR))

    root.mainloop()
    # ✅ Fetch last invoice ID for a customer
def get_last_invoice_id(customer_id):
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM invoices_table 
        WHERE customer_id = ? 
        ORDER BY date DESC LIMIT 1
    """, (customer_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# ✅ Fetch products from a given invoice ID
def get_products_by_invoice(invoice_id):
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ip.product_id, i.name, i.category, ip.quantity, ip.price
        FROM invoice_products ip
        JOIN items i ON ip.product_id = i.item_id
        WHERE ip.invoice_id = ?
    """, (invoice_id,))
    data = cursor.fetchall()
    conn.close()
    return data
# ✅ Get customer_id using name and phone
def get_customer_id_by_name_and_phone(name, phone):
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM customers WHERE name=? AND phone=?
    """, (name, phone))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


# Call the login screen function to start the application
if __name__ == "__main__":
    show_login_screen()

