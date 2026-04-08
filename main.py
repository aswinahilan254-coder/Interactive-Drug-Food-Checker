import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# ==========================================
# CONFIGURATION: EDIT COLUMN NAMES HERE
# ==========================================
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "drug_data.csv")  # Load from same folder as script
COL_DRUG = "drug_name"          # Name of the medication
COL_FOOD = "food_item"          # The food/drink involved
COL_SEVERITY = "severity"       # Major, Moderate, or Minor
COL_DESC = "description"        # Technical clinical description
COL_CLASS = "drug_class"        # e.g., Antibiotic, Statin (Optional)

# ==========================================
# LOGIC & UTILITIES
# ==========================================

def get_plain_english(tech_text, food_item):
    """Converts clinical jargon into simple patient advice."""
    text = str(tech_text).lower()
    food = str(food_item).lower()
    
    advice = "Consult your pharmacist for specific timing."
    
    if "grapefruit" in food or "grapefruit" in text:
        advice = "Avoid grapefruit; it can make the drug level too high in your body."
    elif "alcohol" in food or "ethanol" in text:
        advice = "Avoid or limit alcohol as it may increase drowsiness or side effects."
    elif "empty stomach" in text or "before meals" in text:
        advice = "Take on an empty stomach (1 hour before or 2 hours after eating)."
    elif "with food" in text or "after meals" in text:
        advice = "Take with food to prevent stomach upset."
    elif "vitamin k" in text or "leafy green" in food:
        advice = "Keep your intake of green leafy vegetables consistent every day."
    elif "dairy" in food or "milk" in food or "calcium" in text:
        advice = "Avoid taking this with milk or antacids; they can block absorption."
    
    return advice

# ==========================================
# MAIN APPLICATION CLASS
# ==========================================

class DrugFoodApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Drug-Food Interaction Checker")
        self.root.geometry("900x700")
        
        # Load Data
        if not self.load_data():
            return
        
        # UI Setup
        self.setup_ui()

    def load_data(self):
        try:
            self.df = pd.read_csv(DATASET_PATH)
            # Clean data: remove empty rows and standardize case for searching
            self.df = self.df.fillna("Not Available")
            return True
        except FileNotFoundError:
            messagebox.showerror("Error", f"Dataset not found!\nPlease ensure '{DATASET_PATH}' is in the folder.")
            self.root.destroy()
            return False

    def setup_ui(self):
        # --- Header ---
        header = tk.Label(self.root, text="💊 Drug-Food Interaction Checker", font=("Arial", 18, "bold"), pady=10)
        header.pack()

        # --- Search Frame ---
        search_frame = tk.Frame(self.root, padx=20, pady=10)
        search_frame.pack(fill="x")

        tk.Label(search_frame, text="Enter Drug Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.grid(row=0, column=1, padx=10)
        
        search_btn = ttk.Button(search_frame, text="Search", command=self.perform_search)
        search_btn.grid(row=0, column=2, padx=5)

        # --- Filter Frame ---
        filter_frame = tk.Frame(self.root, padx=20)
        filter_frame.pack(fill="x")
        
        tk.Label(filter_frame, text="Filter Severity:").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filters = ["All", "Major", "Moderate", "Minor"]
        self.filter_menu = ttk.OptionMenu(filter_frame, self.filter_var, *filters, command=lambda _: self.perform_search())
        self.filter_menu.pack(side="left", padx=10)

        # --- Results Area (Scrollable) ---
        result_container = tk.Frame(self.root, padx=20, pady=10)
        result_container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(result_container, columns=("Drug", "Food", "Severity", "Advice"), show='headings')
        self.tree.heading("Drug", text="Drug Name")
        self.tree.heading("Food", text="Food Involved")
        self.tree.heading("Severity", text="Severity")
        self.tree.heading("Advice", text="Patient Advice")
        
        self.tree.column("Drug", width=120)
        self.tree.column("Food", width=120)
        self.tree.column("Severity", width=80)
        self.tree.column("Advice", width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Details Text Area ---
        tk.Label(self.root, text="Clinical Description (Selected Item):", font=("Arial", 10, "italic")).pack(anchor="w", padx=20)
        self.details_box = tk.Text(self.root, height=5, padx=10, pady=10, state="disabled", wrap="word")
        self.details_box.pack(fill="x", padx=20, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.show_details)

        # --- Buttons Frame ---
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        ttk.Button(btn_frame, text="Analyze Trends", command=self.show_analytics).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export CSV", command=self.export_results).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)

        # --- Disclaimer ---
        disclaimer = tk.Label(self.root, text="⚠️ This tool is for educational support only. Not medical advice.", fg="red", font=("Arial", 8))
        disclaimer.pack(side="bottom", pady=5)

    def perform_search(self):
        query = self.search_var.get().strip().lower()
        severity_filter = self.filter_var.get()

        if not query:
            messagebox.showwarning("Input Needed", "Please enter a drug name to search.")
            return

        # Clear existing results
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter logic
        results = self.df[self.df[COL_DRUG].str.contains(query, case=False, na=False)]
        
        if severity_filter != "All":
            results = results[results[COL_SEVERITY].str.contains(severity_filter, case=False, na=False)]

        if results.empty:
            messagebox.showinfo("No Match", f"No interactions found for '{query}'.")
            return

        # Populate Treeview
        for _, row in results.iterrows():
            advice = get_plain_english(row[COL_DESC], row[COL_FOOD])
            self.tree.insert("", "end", values=(row[COL_DRUG], row[COL_FOOD], row[COL_SEVERITY], advice), tags=(row[COL_SEVERITY],))
        
        # Color Coding
        self.tree.tag_configure("Major", foreground="red")
        self.tree.tag_configure("Moderate", foreground="orange")
        self.tree.tag_configure("Minor", foreground="blue")

    def show_details(self, event):
        try:
            selected = self.tree.selection()
            if not selected: return
            
            item = self.tree.item(selected[0])
            drug_name = item['values'][0]
            
            # Get description from original DF
            match_rows = self.df[self.df[COL_DRUG] == drug_name]
            if match_rows.empty:
                self.details_box.config(state="normal")
                self.details_box.delete("1.0", "end")
                self.details_box.insert("end", "No details found for this drug.")
                self.details_box.config(state="disabled")
                return
            
            match = match_rows.iloc[0]
            
            self.details_box.config(state="normal")
            self.details_box.delete("1.0", "end")
            self.details_box.insert("end", f"TECHNICAL NOTE:\n{match[COL_DESC]}")
            self.details_box.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading details: {e}")

    def show_analytics(self):
        # Create a new Popup Window
        top = tk.Toplevel(self.root)
        top.title("Interaction Trends Analysis")
        top.geometry("600x600")

        # Basic Stats calculation
        total_rec = len(self.df)
        unique_drugs = self.df[COL_DRUG].nunique()
        sev_counts = self.df[COL_SEVERITY].value_counts()

        summary_text = f"Total Records: {total_rec}\nUnique Drugs: {unique_drugs}\n\nTop 5 Common Interacting Foods:\n{self.df[COL_FOOD].value_counts().head(5).to_string()}"
        
        tk.Label(top, text="Data Summary", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(top, text=summary_text, justify="left").pack()

        # Plot Severity Chart
        fig, ax = plt.subplots(figsize=(4, 3))
        sev_counts.plot(kind='bar', color=['red', 'orange', 'blue'], ax=ax)
        ax.set_title("Interactions by Severity")
        
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    def export_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path: return
        
        # Grab current treeview items
        data = []
        for item in self.tree.get_children():
            data.append(self.tree.item(item)['values'])
        
        export_df = pd.DataFrame(data, columns=["Drug", "Food", "Severity", "Advice"])
        export_df.to_csv(file_path, index=False)
        messagebox.showinfo("Success", "Report exported successfully!")

    def clear_all(self):
        self.search_var.set("")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.details_box.config(state="normal")
        self.details_box.delete("1.0", "end")
        self.details_box.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrugFoodApp(root)
    root.mainloop()