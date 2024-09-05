import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import ttkbootstrap as ttk
import random
import string  # Import the string module
import cv2
import mediapipe as mp
import pyautogui

# Sample data for menu items with images
menu_items = {
    "Burgers": [("Chicken Burger", 5, "chicken_burger.png"), ("Veggie Burger", 4, "veggie_burger.png"),
                ("Cheese Burger", 6, "cheese_burger.png")],
    "Sides": [("Fries", 2, "fries.png"), ("Onion Rings", 3, "onion_rings.png"), ("Salad", 4, "salad.png")],
    "Drinks": [("Coke", 1, "coke.png"), ("Pepsi", 1, "pepsi.png"), ("Water", 0.5, "water.png")]
}

class FoodOrderingApp:
    def _init_(self, root):
        self.root = root
        self.root.title("Gesture Controlled Food Ordering System")

        # Set the initial position and size of the window
        self.root.geometry("1000x700+0+0")

        # Apply ttkbootstrap theme
        self.style = ttk.Style("litera")

        # Create a custom style for buttons with a larger font
        self.style.configure('Custom.TButton', font=('Arial', 16))

        # Create frames
        self.create_frames()

        # Create menu and cart
        self.create_menu_buttons()

        self.create_cart()

        # Initialize cart and order ID
        self.cart_items = {}

        self.order_id = None  # Will be set during checkout

        # Initialize computer vision
        self.cap = cv2.VideoCapture(0)
        self.hand_detector = mp.solutions.hands.Hands()
        self.drawing_utils = mp.solutions.drawing_utils

        # Global variables for hand positions
        self.index_x = 0
        self.index_y = 0

        # Start gesture detection loop
        self.detect_gestures()

    def create_frames(self):
        self.menu_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        self.menu_frame.grid(row=0, column=0, sticky="ns")

        self.items_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        self.items_frame.grid(row=0, column=1, sticky="nsew")

        self.cart_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        self.cart_frame.grid(row=0, column=2, sticky="ns")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def create_menu_buttons(self):
        ttk.Label(self.menu_frame, text="Menu Categories", style='primary.TLabel').pack(pady=10)
        for category, items in menu_items.items():
            btn = ttk.Button(self.menu_frame, text=category, command=lambda c=category: self.show_items(c),
                             style='Custom.TButton')
            btn.pack(fill=tk.BOTH, pady=5)

    def create_cart(self):
        ttk.Label(self.cart_frame, text="Cart", style='primary.TLabel', font=('Arial', 18)).pack(pady=10)
        self.cart_listbox = tk.Listbox(self.cart_frame, font=('Arial', 14))
        self.cart_listbox.pack(fill=tk.BOTH, expand=True)

        self.total_label = ttk.Label(self.cart_frame, text="Total: $0", style='primary.TLabel', font=('Arial', 18))
        self.total_label.pack(pady=10)

        self.checkout_button = ttk.Button(self.cart_frame, text="Checkout", command=self.checkout,
                                          style='Custom.TButton')
        self.checkout_button.pack()

    def show_items(self, category):
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.items_frame, text=f"{category}", style='primary.TLabel', font=('Arial', 16)).pack(pady=10)

        for item, price, img_path in menu_items[category]:
            frame = ttk.Frame(self.items_frame, padding=5, style='TFrame')
            frame.pack(fill=tk.BOTH, pady=5)

            img = Image.open(img_path)
            img = img.resize((100, 100), Image.LANCZOS)  # Use LANCZOS for resizing
            photo = ImageTk.PhotoImage(img)

            img_label = ttk.Label(frame, image=photo)
            img_label.image = photo
            img_label.grid(row=0, column=0, rowspan=2, padx=10, pady=5)

            label = ttk.Label(frame, text=f"{item} - ${price}", style='TLabel', font=('Arial', 14))
            label.grid(row=0, column=1, sticky="w", padx=10, pady=5)

            qty_var = tk.IntVar(value=1)

            qty_frame = ttk.Frame(frame, padding=0)
            qty_frame.grid(row=1, column=1, sticky="w", padx=10, pady=5)

            dec_btn = ttk.Button(qty_frame, text="-", command=lambda q=qty_var: self.update_quantity(q, -1), width=3,
                                 style='Custom.TButton')
            dec_btn.pack(side=tk.LEFT)

            qty_label = ttk.Label(qty_frame, textvariable=qty_var, width=3, style='TLabel', anchor='center',
                                  font=('Arial', 14))
            qty_label.pack(side=tk.LEFT)

            inc_btn = ttk.Button(qty_frame, text="+", command=lambda q=qty_var: self.update_quantity(q, 1), width=3,
                                 style='Custom.TButton')
            inc_btn.pack(side=tk.LEFT)

            add_btn = ttk.Button(frame, text="Add",
                                 command=lambda i=item, p=price, q=qty_var: self.add_to_cart(i, p, q), width=5,
                                 style='Custom.TButton')
            add_btn.grid(row=1, column=2, padx=10, sticky='w')

    def update_quantity(self, qty_var, delta):
        current_qty = qty_var.get()
        new_qty = max(1, current_qty + delta)
        qty_var.set(new_qty)

    def add_to_cart(self, item, price, qty_var):
        quantity = qty_var.get()
        if item in self.cart_items:
            self.cart_items[item]['quantity'] += quantity
        else:
            self.cart_items[item] = {'price': price, 'quantity': quantity}
        self.update_cart()

    def update_cart(self):
        self.cart_listbox.delete(0, tk.END)
        total = 0
        for item, details in self.cart_items.items():
            price = details['price']
            qty = details['quantity']
            self.cart_listbox.insert(tk.END, f"{item} - ${price} x {qty}")
            total += price * qty
        self.total_label.config(text=f"Total: ${total:.2f}")

    # def checkout(self):
    #     if not self.cart_items:
    #         messagebox.showwarning("Empty Cart", "Your cart is empty!")
    #         return
    #
    #     total = sum(details['price'] * details['quantity'] for details in self.cart_items.values())
    #
    #     # Generate a unique order ID
    #     self.order_id = self.generate_order_id()
    #
    #     # Print the detailed bill to the terminal with order ID
    #     print("----- Detailed Bill -----")
    #     print(f"Order ID: {self.order_id}")
    #     print("{:<20} {:<10} {:<10} {:<10}".format("Item", "Price", "Quantity", "Total"))
    #     print("-" * 50)
    #     for item, details in self.cart_items.items():
    #         price = details['price']
    #         quantity = details['quantity']
    #         total_price = price * quantity
    #         print("{:<20} ${:<9.2f} {:<10} ${:<10.2f}".format(item, price, quantity, total_price))
    #     print("-" * 50)
    #     print("{:<20} {:<10} {:<10} ${:<10.2f}".format("", "", "Total:", total))
    #     print("-------------------------")
    #
    #     messagebox.showinfo("Order Placed", f"Your order has been placed!\nTotal amount: ${total:.2f}")
    #
    #     # Clear cart and update UI
    #     self.cart_items.clear()
    #     self.update_cart()
    def checkout(self):
        if not self.cart_items:
            messagebox.showwarning("Empty Cart", "Your cart is empty!")
            return

        total = sum(details['price'] * details['quantity'] for details in self.cart_items.values())

        # Generate a unique order ID
        self.order_id = self.generate_order_id()

        # Show a confirmation window
        confirmation = messagebox.askyesno("Confirm Order",
                                           f"Do you want to Confirm the order ?\nTotal amount: ${total:.2f}\n")
        if confirmation:
            # Print the detailed bill to the terminal with order ID
            print("----- Detailed Bill -----")
            print(f"Order ID: {self.order_id}")
            print("{:<20} {:<10} {:<10} {:<10}".format("Item", "Price", "Quantity", "Total"))
            print("-" * 50)
            for item, details in self.cart_items.items():
                price = details['price']
                quantity = details['quantity']
                total_price = price * quantity
                print("{:<20} ${:<9.2f} {:<10} ${:<10.2f}".format(item, price, quantity, total_price))
            print("-" * 50)
            print("{:<20} {:<10} {:<10} ${:<10.2f}".format("", "", "Total:", total))
            print("-------------------------")

            messagebox.showinfo("Order Placed", f"Your order has been placed!\nTotal amount: ${total:.2f}")

            # Clear cart and update UI
            self.cart_items.clear()
            self.update_cart()
        else:
            return
    def generate_order_id(self):
        return f"ORDER-{random.choice(string.ascii_uppercase)}{''.join(random.choices(string.digits, k=3))}"

    def detect_gestures(self):
        _, frame = self.cap.read()
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = self.hand_detector.process(rgb_frame)
        hands = output.multi_hand_landmarks
        if hands:
            for hand in hands:
                landmarks = hand.landmark
                for id, landmark in enumerate(landmarks):
                    x = int(landmark.x * frame_width)
                    y = int(landmark.y * frame_height)
                    if id == 8:  # Tip of index finger
                        self.index_x = x
                        self.index_y = y
                        pyautogui.moveTo(self.index_x, self.index_y)
                    if id == 4:  # Tip of thumb
                        thumb_x = x
                        thumb_y = y
                        if abs(self.index_y - thumb_y) < 50:
                            pyautogui.click()
                            pyautogui.sleep(1)
        self.root.after(100, self.detect_gestures)

# Create the main window and run the app
if _name_ == "_main_":
    root = ttk.Window(themename="litera")
    app = FoodOrderingApp(root)
    root.mainloop()