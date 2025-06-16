import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import re
from datetime import datetime
from urllib.parse import urlparse
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO


class ClassifiedAdsViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Classified Ads Viewer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')

        self.ads_data = []
        self.filtered_ads = []
        self.current_sort = "default"
        self.search_term = ""

        # Create main interface
        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header frame
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        title_label = ttk.Label(header_frame, text="Classified Ads Viewer",
                                font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)

        # Upload button
        self.upload_btn = ttk.Button(header_frame, text="Upload JSON File",
                                     command=self.upload_file)
        self.upload_btn.pack(side=tk.RIGHT)

        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Search
        ttk.Label(controls_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Sort
        ttk.Label(controls_frame, text="Sort by:").pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="default")
        sort_combo = ttk.Combobox(controls_frame, textvariable=self.sort_var,
                                  values=["default", "price-low", "price-high", "date-new", "date-old"],
                                  state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_change)

        # Results info
        self.info_label = ttk.Label(controls_frame, text="No data loaded")
        self.info_label.pack(side=tk.RIGHT)

        # Create scrollable frame for ads
        self.create_scrollable_frame(main_frame)

        # Show upload prompt initially
        self.show_upload_prompt()

    def create_scrollable_frame(self, parent):
        # Canvas and scrollbar for scrolling
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show_upload_prompt(self):
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        prompt_frame = ttk.Frame(self.scrollable_frame)
        prompt_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=100)

        ttk.Label(prompt_frame, text="📁", font=('Arial', 48)).pack(pady=20)
        ttk.Label(prompt_frame, text="Upload a JSON file to get started",
                  font=('Arial', 14)).pack(pady=10)
        ttk.Button(prompt_frame, text="Choose File",
                   command=self.upload_file).pack(pady=10)

    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                if not isinstance(data, list):
                    messagebox.showerror("Error", "JSON file must contain an array of ads")
                    return

                self.ads_data = data
                self.apply_filters_and_sort()
                messagebox.showinfo("Success", f"Loaded {len(data)} ads successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def extract_price_value(self, ad):
        """Extract numeric price value from ad data"""
        try:
            # Try regularPrice.value first
            if ad.get('price', {}).get('regularPrice', {}).get('value'):
                return float(ad['price']['regularPrice']['value'])

            # Fallback: parse displayValue
            display_value = ad.get('price', {}).get('displayValue', '0')
            # Remove currency symbols and spaces, extract numbers
            numeric_string = re.sub(r'[^\d,.-]', '', display_value).replace(' ', '')
            # Handle Polish format (comma as decimal separator)
            normalized_string = numeric_string.replace(',', '.')
            return float(normalized_string) if normalized_string else 0
        except:
            return 0

    def apply_filters_and_sort(self):
        """Apply search filter and sorting to ads data"""
        # Filter by search term
        if self.search_term:
            self.filtered_ads = [
                ad for ad in self.ads_data
                if self.search_term.lower() in ad.get('title', '').lower() or
                   self.search_term.lower() in ad.get('location', {}).get('cityName', '').lower()
            ]
        else:
            self.filtered_ads = self.ads_data.copy()

        # Sort
        if self.current_sort == "price-low":
            self.filtered_ads.sort(key=self.extract_price_value)
        elif self.current_sort == "price-high":
            self.filtered_ads.sort(key=self.extract_price_value, reverse=True)
        elif self.current_sort == "date-new":
            self.filtered_ads.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
        elif self.current_sort == "date-old":
            self.filtered_ads.sort(key=lambda x: x.get('createdTime', ''))

        self.update_display()

    def update_display(self):
        """Update the display with filtered and sorted ads"""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Update info label
        total = len(self.ads_data)
        showing = len(self.filtered_ads)
        self.info_label.config(text=f"Showing {showing} of {total} ads")

        if not self.filtered_ads:
            if self.search_term:
                ttk.Label(self.scrollable_frame, text=f"No ads found matching '{self.search_term}'",
                          font=('Arial', 12)).pack(pady=50)
            return

        # Create grid of ad cards
        self.create_ads_grid()

    def create_ads_grid(self):
        """Create a grid layout of ad cards"""
        cols = 2  # Number of columns

        for i, ad in enumerate(self.filtered_ads):
            row = i // cols
            col = i % cols

            # Create card frame
            card_frame = ttk.LabelFrame(self.scrollable_frame, padding=10)
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

            # Configure grid weights
            self.scrollable_frame.grid_columnconfigure(col, weight=1)

            self.create_ad_card(card_frame, ad)

    def create_ad_card(self, parent, ad):
        """Create individual ad card"""
        # Title
        title = ad.get('title', 'No title')
        title_label = ttk.Label(parent, text=title[:60] + "..." if len(title) > 60 else title,
                                font=('Arial', 12, 'bold'), wraplength=300)
        title_label.pack(anchor='w', pady=(0, 5))

        # Price
        price = ad.get('price', {}).get('displayValue', 'No price')
        price_label = ttk.Label(parent, text=price, font=('Arial', 14, 'bold'),
                                foreground='green')
        price_label.pack(anchor='w', pady=(0, 5))

        # Location
        location = ad.get('location', {}).get('pathName', 'Unknown location')
        location_label = ttk.Label(parent, text=f"📍 {location}", font=('Arial', 10))
        location_label.pack(anchor='w', pady=(0, 3))

        # Seller
        seller = ad.get('user', {}).get('company_name') or ad.get('user', {}).get('name', 'Unknown seller')
        seller_label = ttk.Label(parent, text=f"👤 {seller}", font=('Arial', 10))
        seller_label.pack(anchor='w', pady=(0, 3))

        # Date
        created_time = ad.get('createdTime', '')
        if created_time:
            try:
                date_obj = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y-%m-%d')
                date_label = ttk.Label(parent, text=f"📅 {date_str}", font=('Arial', 10))
                date_label.pack(anchor='w', pady=(0, 5))
            except:
                pass

        # Badges
        badges_frame = ttk.Frame(parent)
        badges_frame.pack(anchor='w', pady=(0, 5))

        if ad.get('isPromoted'):
            ttk.Label(badges_frame, text="⭐ Promoted", background='yellow',
                      font=('Arial', 8)).pack(side='left', padx=(0, 5))

        if ad.get('isHighlighted'):
            ttk.Label(badges_frame, text="🔥 Highlighted", background='orange',
                      font=('Arial', 8)).pack(side='left', padx=(0, 5))

        # Description preview
        description = ad.get('description', '')
        if description:
            # Strip HTML and limit length
            clean_desc = re.sub('<[^<]+?>', '', description)
            preview = clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc
            desc_label = ttk.Label(parent, text=preview, font=('Arial', 9),
                                   wraplength=300, justify='left')
            desc_label.pack(anchor='w', pady=(5, 5))

        # Parameters
        params = ad.get('params', [])
        if params:
            params_frame = ttk.Frame(parent)
            params_frame.pack(anchor='w', pady=(0, 5))

            for i, param in enumerate(params[:3]):  # Show max 3 params
                param_text = f"{param.get('name', '')}: {param.get('value', '')}"
                ttk.Label(params_frame, text=param_text, font=('Arial', 8),
                          background='lightgray').pack(side='left', padx=(0, 5))

        # View original button
        if ad.get('url'):
            def open_url(url=ad['url']):
                import webbrowser
                webbrowser.open(url)

            ttk.Button(parent, text="View Original",
                       command=open_url).pack(anchor='w', pady=(5, 0))

    def on_search_change(self, *args):
        """Handle search term change"""
        self.search_term = self.search_var.get()
        if self.ads_data:
            self.apply_filters_and_sort()

    def on_sort_change(self, event):
        """Handle sort option change"""
        self.current_sort = self.sort_var.get()
        if self.ads_data:
            self.apply_filters_and_sort()


def main():
    root = tk.Tk()
    app = ClassifiedAdsViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()