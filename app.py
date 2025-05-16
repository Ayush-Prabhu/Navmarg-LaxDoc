import os
import csv
import re
import subprocess
import customtkinter as ctk
import shutil
from TexSoup import TexSoup
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from datetime import datetime

# Constants
TEMPLATE_FOLDER = "templates"
TEMP_TEX_DIR = "temp"
DOCUMENTS_DIR = "documents"
# CSV_FILE = "index.csv"
TEMPLATES_CSV = "templates.csv"
DOCUMENTS_CSV = "documents.csv"
CTK_FRAME_PAD = 20

# Helper functions
def check_and_create_index():
    """
    Checks if the templates.csv and documents.csv files exist. If not, creates them with appropriate headers.
    """
    template_headers = [
        "Template Index",
        "Template Type Name",
        "Date of Import",
        "Short Description",
        "Path to Template File"
    ]
    document_headers = [
        "Document Index Number",
        "Template Type Name",
        "Date of Generation",
        "Short Description",
        "Path to Parameter File",
        "Path to Generated PDF"
    ]

    if not os.path.exists(TEMPLATES_CSV):
        with open(TEMPLATES_CSV, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(template_headers)
        print(f"'{TEMPLATES_CSV}' created with headers.")
    else:
        print(f"'{TEMPLATES_CSV}' already exists.")

    if not os.path.exists(DOCUMENTS_CSV):
        with open(DOCUMENTS_CSV, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(document_headers)
        print(f"'{DOCUMENTS_CSV}' created with headers.")
    else:
        print(f"'{DOCUMENTS_CSV}' already exists.")

def is_valid_filename(name):
    """Validate filename doesn't contain special characters"""
    return not re.search(r'[\\/:*?"<>|]', name)

def parse_placeholders(content):
    """Detect placeholders in the LaTeX template using regex."""
    return re.findall(r'\{\{(\w+)\}\}', content)

def validate_latex(content, placeholders):
    """
    Validate LaTeX structure and ensure placeholders are present.
    """
    if not placeholders:
        raise ValueError("No placeholders detected (use {{name}} syntax).")
    
    try:
        TexSoup(content)  # Validate LaTeX syntax
    except Exception as e:
        raise ValueError(f"LaTeX validation failed: {str(e)}")
    
    return True

def save_template(content, save_path):
    """Save the LaTeX template to the templates folder."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        f.write(content)

def get_next_index(csv_file):
    """Get the next sequential index number for the CSV."""
    if not os.path.exists(csv_file):
        return 1
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        indices = [int(row[0]) for row in reader if row[0].isdigit()]
    
    return max(indices) + 1 if indices else 1

def add_csv_entry(index, name, desc, template_path):
    """Add a new entry to index.csv with template metadata."""
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = [
        index,
        name,
        current_date,
        desc,
        template_path
    ]
    
    with open(TEMPLATES_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(new_row)

def generate_document_id(template_type,template_index, csv_path, custom_format=None):
    """
    Generate document ID from a tokenized format string.
    Supported tokens: {TEMPLATE}, {YYMMDD}, {DDMMYYYY}, {YYYYMMDD}, {seq}
    """
    now = datetime.now()
    token_map = {
        "{TEMPLATE}": template_index, 
        "{YYMMDD}": now.strftime("%y%m%d"),
        "{DDMMYYYY}": now.strftime("%d%m%Y"),
        "{YYYYMMDD}": now.strftime("%Y%m%d"),
        "{DDMMYY}": now.strftime("%d%m%y"),
        "{YYYYMM}": now.strftime("%Y%m"),
        "{YYMM}": now.strftime("%y%m"),
        "{YYYY}": now.strftime("%Y"),
        "{YY}": now.strftime("%y"),
        "{MM}": now.strftime("%m"),
        "{DD}": now.strftime("%d"),
    }

    existing_ids = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_ids.add(row["Document Index Number"])

    if not custom_format:
        # fallback format
        custom_format = "{TEMPLATE}-{YYYYMMDD}-{seq}"

    for i in range(1, 1000):
        seq_str = f"{i:02d}"
        doc_id = custom_format
        for key, val in token_map.items():
            doc_id = doc_id.replace(key, val)
        doc_id = doc_id.replace("{seq}", seq_str)

        if doc_id not in existing_ids:
            return doc_id

    raise ValueError("Exceeded max document ID attempts.")

def acronymize(name):
    words = name.strip().split()

    if len(words) == 1:
        # Single word → take first 3 letters uppercased
        return words[0][:3].upper()
    else:
        # Multi-word → acronym (first letters)
        return ''.join(word[0] for word in words).upper()

def validate_custom_id_format(fmt):
    """
    Validates that the custom format:
    - Uses only supported tokens
    - Contains {seq}
    """
    allowed_tokens = {
        "{TEMPLATE}", "{seq}",
        "{YYYY}", "{YY}", "{MM}", "{DD}",
        "{YYYYMMDD}", "{DDMMYYYY}", "{YYMMDD}"," {DDMMYY}","{YYYYMM}","{YYMM}"
    }

    used_tokens = set(re.findall(r"\{[A-Z]+\}", fmt))
    unknown = used_tokens - allowed_tokens

    if unknown:
        raise ValueError(f"Invalid token(s) in format: {', '.join(unknown)}")

    if "{seq}" not in fmt:
        raise ValueError("Format must include the {seq} token to ensure uniqueness.")
    
    if "{TEMPLATE}" not in fmt:
        raise ValueError("Format must include the {TEMPLATE} token.")
    
def generate_unique_template_index(name, csv_file=TEMPLATES_CSV):
    """
    Generate a unique abbreviation (acronym or prefix) for the template.
    Avoids duplication with existing entries in templates.csv.
    """
    # Step 1: Load existing index codes
    existing = set()
    if os.path.exists(csv_file):
        with open(csv_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add(row["Template Index"])

    # Step 2: Start with acronym logic
    words = name.strip().split()
    print(words)
    if len(words) == 1:
        base_code = words[0][:3].upper()
    else:
        base_code = ''.join(word[0] for word in words).upper()

    # Step 3: Check for uniqueness
    code = base_code
    suffix = 2
    while code in existing:
        code = f"{base_code}{suffix}"
        suffix += 1

    return code



def ask_large_text(title="Input", prompt="Enter text:", initial_text="", width=60, height=5):
    """Safe large input window that sanitizes newline characters for CSV compatibility."""
    result = {"text": None}

    def on_ok():
        raw_text = text_widget.get("1.0", "end-1c")
        sanitized = raw_text.replace("\n", " ").replace("\r", " ").strip()
        result["text"] = sanitized
        dialog.destroy()

    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry("600x200")
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog, text=prompt, anchor="w").pack(pady=5, padx=10, anchor="w")

    text_widget = tk.Text(dialog, wrap="word", width=width, height=height)
    text_widget.insert("1.0", initial_text)
    text_widget.pack(padx=10, pady=5, fill="both", expand=True)

    tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    dialog.wait_window()
    return result["text"]

def ask_wide_entry(title="Input", prompt="Enter value:", initial_value="", width=60):
    """Custom dialog for single-line wide input (e.g., for template name)."""
    result = {"value": None}

    def on_ok():
        val = entry.get().strip()
        result["value"] = val
        dialog.destroy()

    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry("500x120")
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog, text=prompt, anchor="w").pack(pady=10, padx=15, anchor="w")

    entry = tk.Entry(dialog, width=width)
    entry.insert(0, initial_value)
    entry.pack(padx=15, pady=5, fill="x")

    tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    dialog.wait_window()
    return result["value"]


class LaxDocApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LaxDoc - Document Management System")
        self.geometry("1200x800")
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Sidebar buttons
        self.btn_import = ctk.CTkButton(
            self.sidebar,
            text="Import Template",
            command=self.show_import_frame,
            fg_color="#2A8CBB",
            hover_color="#1F6A8A"
        )
        self.btn_import.pack(pady=CTK_FRAME_PAD, padx=CTK_FRAME_PAD, fill="x")
        
        self.btn_generate = ctk.CTkButton(
            self.sidebar,
            text="Generate Document",
            command=self.show_generate_frame,
            fg_color="#2A8CBB",
            hover_color="#1F6A8A"
        )
        self.btn_generate.pack(pady=CTK_FRAME_PAD, padx=CTK_FRAME_PAD, fill="x")

        self.btn_search_doc = ctk.CTkButton(
            self.sidebar,
            text="Search Document",
            command=self.show_search_frame,
            fg_color="#2A8CBB",
            hover_color="#1F6A8A"
        )
        self.btn_search_doc.pack(pady=CTK_FRAME_PAD, padx=CTK_FRAME_PAD, fill="x")
        
        self.btn_search_tem = ctk.CTkButton(
            self.sidebar,
            text="Search Template",
            command=self.show_search_temp_frame,
            fg_color="#2A8CBB",
            hover_color="#1F6A8A"
        )
        self.btn_search_tem.pack(pady=CTK_FRAME_PAD, padx=CTK_FRAME_PAD, fill="x")

        # Create main content area
        self.main_content = ctk.CTkFrame(self, corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew")
        
        # Initialize frames
        self.import_frame = ImportTemplateFrame(self.main_content)
        self.generate_frame = DocumentGenerationFrame(self.main_content)
        self.search_frame = SearchDocumentFrame(self.main_content)
        self.search_temp_frame = SearchTemplateFrame(self.main_content)

        
        # Show default frame
        self.show_import_frame()
        
        # Check required files
        check_and_create_index()
        
    def show_import_frame(self):
        self.generate_frame.pack_forget()
        self.search_frame.pack_forget()
        self.search_temp_frame.pack_forget()
        self.import_frame.pack(fill="both", expand=True, padx=CTK_FRAME_PAD, pady=CTK_FRAME_PAD)
        
    def show_generate_frame(self):
        self.import_frame.pack_forget()
        self.search_frame.pack_forget()
        self.search_temp_frame.pack_forget()
        self.generate_frame.update_template_dropdown()
        self.generate_frame.pack(fill="both", expand=True, padx=CTK_FRAME_PAD, pady=CTK_FRAME_PAD)
    
    def show_search_frame(self):
        self.import_frame.pack_forget()
        self.generate_frame.pack_forget() 
        self.search_temp_frame.pack_forget()
        self.search_frame.pack(fill="both", expand=True, padx=CTK_FRAME_PAD, pady=CTK_FRAME_PAD)
        
    def show_search_temp_frame(self):
        self.generate_frame.pack_forget()
        self.search_frame.pack_forget()
        self.import_frame.pack_forget()
        self.search_temp_frame.pack(fill="both", expand=True, padx=CTK_FRAME_PAD, pady=CTK_FRAME_PAD)

    def show_regenerate_frame(self, row_data,edit_mode=False):
        self.import_frame.pack_forget()
        self.search_frame.pack_forget()
        self.search_temp_frame.pack_forget()

        # Load the template & values into generate_frame
        self.generate_frame.pack(fill="both", expand=True, padx=CTK_FRAME_PAD, pady=CTK_FRAME_PAD)
        self.generate_frame.load_regeneration_data(row_data, edit_mode=edit_mode)

        

class ImportTemplateFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.label = ctk.CTkLabel(self, text="Import LaTeX Template", font=("Arial", 16))
        self.label.pack(pady=CTK_FRAME_PAD)
        
        self.btn_select = ctk.CTkButton(
            self,
            text="Select .tex File",
            command=self.select_template_file,
            fg_color="#2A8CBB",
            hover_color="#1F6A8A"
        )
        self.btn_select.pack(pady=CTK_FRAME_PAD)
        
    def select_template_file(self):
        file_path = filedialog.askopenfilename(
            title="Select LaTeX Template",
            filetypes=[("LaTeX Files", "*.tex")],
            initialdir=os.getcwd()
        )
        
        if not file_path:
            return

        save_path = None
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                placeholders = parse_placeholders(content)
                
                if validate_latex(content, placeholders):
                    # template_name = simpledialog.askstring(
                    #     "Template Name",
                    #     "Enter template name (without extension):"
                    # )
                    
                    template_name = ask_wide_entry(
                        title="Template Name",
                        prompt="Enter template name (without extension):"
                    )


                    if not template_name or not is_valid_filename(template_name):
                        messagebox.showerror("Error", "Invalid or empty template name")
                        return
                    
                    # short_desc = simpledialog.askstring(
                    #     "Template Description",
                    #     "Enter short description:",
                    #     parent=self
                    # )
                    short_desc = ask_large_text(
                        title="Template Description",
                        prompt="Enter a short description of the template:"
                    )

                    if not short_desc:
                        messagebox.showerror("Error", "Description cannot be empty")
                        return

                    final_name = f"{template_name}.tex"
                    save_path = os.path.join(TEMPLATE_FOLDER, final_name)
                    
                    if os.path.exists(save_path):
                        messagebox.showerror("Error", "Template name already exists!")
                        return
                    
                    save_template(content, save_path)
                    add_csv_entry(
                        index=generate_unique_template_index(template_name,TEMPLATES_CSV),
                        name=template_name,
                        desc=short_desc,
                        template_path=save_path
                    )
                    
                    messagebox.showinfo("Success", "Template imported successfully!")
                
                
        except Exception as e:
            if save_path and os.path.exists(save_path):
                os.remove(save_path)
            messagebox.showerror("Error", str(e))

class DocumentGenerationFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Template Selection
        self.template_var = ctk.StringVar()
        self.templates = self.load_templates()  # Load templates from CSV
        print(self.templates)  # Debugging line to check loaded templates
        self.template_label = ctk.CTkLabel(self, text="Select Template:")
        self.template_dropdown = ctk.CTkComboBox(
            self, 
            variable=self.template_var,
            values=[tpl[1] for tpl in self.templates],  # Populate dropdown with template names
            command=self.load_template_fields
        )
        
        # Input Fields Container
        self.input_fields_frame = ctk.CTkScrollableFrame(self, height=300)
        self.input_fields = {}
        
        # Generate Button
        self.generate_btn = ctk.CTkButton(
            self, 
            text="Generate Document", 
            command=self.generate_document,
            fg_color="#2A8CBB",
            hover_color="#1F6A8A"
        )
        
        # Error Log Display
        self.error_log = ctk.CTkTextbox(self, height=150, state="disabled")
        
        # Layout
        self.template_label.pack(pady=5)
        self.template_dropdown.pack(pady=5, fill="x")
        self.input_fields_frame.pack(pady=10, fill="both", expand=True)
        self.generate_btn.pack(pady=10)
        # Custom ID Option
        self.use_custom_id = ctk.BooleanVar(value=False)
        self.custom_id_checkbox = ctk.CTkCheckBox(
            self, 
            text="Use Custom Document ID prefix(e.g.:{TEMPLATE}-{YYMMDD}-{seq})",
            variable=self.use_custom_id,
            command=self.toggle_custom_id
        )

        self.custom_id_entry = ctk.CTkEntry(
            self,
            placeholder_text="e.g. {TEMPLATE}-{YYMMDD}-{seq}",
            state="readonly",
            # textvariable=None
        )


        # Add to layout
        self.custom_id_checkbox.pack(pady=5)
        self.custom_id_entry.pack(pady=5, fill="x")
        # self.custom_id_entry.insert(0,"{TEMPLATE}-{YYMMDD}-{seq}")        

        self.error_log.pack(pady=10, fill="x")

    def toggle_custom_id(self):
        if self.use_custom_id.get():
            self.custom_id_entry.configure(state="normal")
        else:
            self.custom_id_entry.delete(0, "end")
            self.custom_id_entry.configure(state="readonly")


    def update_template_dropdown(self):
        """Update the template dropdown with the latest templates."""
        self.templates = self.load_templates()  # Reload templates from CSV
        template_names = [tpl[1] for tpl in self.templates]
        self.template_dropdown.configure(values=template_names)  # Update dropdown values
    def load_templates(self):
        """Load templates from index.csv"""
        templates = []
        if os.path.exists(TEMPLATES_CSV):
            with open(TEMPLATES_CSV, "r") as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 5:
                        templates.append((row[0],row[1], row[4]))  # (name, path)
        return templates

    def load_regeneration_data(self, row_data, edit_mode=False):
        self.template_var.set(row_data["Template Type Name"])
        self.load_template_fields(row_data["Template Type Name"])

        # Load parameters from .txt
        param_file = row_data["Path to Parameter File"]
        if not os.path.exists(param_file):
            messagebox.showerror("Error", f"Parameter file missing: {param_file}")
            return
        try:
            with open(param_file, "r") as f:
                param_lines = f.readlines()
                for line in param_lines:
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip()
                        if key in self.input_fields:
                            self.input_fields[key].delete(0, "end")
                            self.input_fields[key].insert(0, val)
            if edit_mode:
                self.editing_existing = True
                self.document_id = row_data["Document Index Number"]
                self.param_file_path = row_data["Path to Parameter File"]
                self.pdf_path = row_data["Path to Generated PDF"]
            else:
                self.editing_existing = False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parameters: {e}")



    def load_template_fields(self, choice):
        """Load input fields based on selected template"""
        # Clear existing fields
        for widget in self.input_fields_frame.winfo_children():
            widget.destroy()
        self.input_fields.clear()
        
        # Find selected template path
        template_path = next((tpl[2] for tpl in self.templates if tpl[1] == choice), None)
        
        if template_path and os.path.exists(template_path):
            with open(template_path, "r") as f:
                content = f.read()
                placeholders = parse_placeholders(content)
                
                for ph in placeholders:
                    frame = ctk.CTkFrame(self.input_fields_frame)
                    label = ctk.CTkLabel(frame, text=f"{ph}:")
                    entry = ctk.CTkEntry(frame)
                    
                    label.pack(side="left", padx=5)
                    entry.pack(side="right", fill="x", expand=True)
                    frame.pack(fill="x", pady=2)
                    
                    self.input_fields[ph] = entry

    def generate_document(self):
        """Handle document generation process."""
        # Validate inputs
        if not self.template_var.get():
            messagebox.showerror("Error", "Please select a template first!")
            return

        missing_fields = [ph for ph, entry in self.input_fields.items() if not entry.get()]
        if missing_fields:
            messagebox.showerror("Error", f"Missing values for: {', '.join(missing_fields)}")
            return

        try:
            # doc_description = simpledialog.askstring(
            #     "Document Description",
            #     "Enter a short description for the generated document:"
            # )

            doc_description = ask_large_text(
                title="Document Description",
                prompt="Enter a short description for the generated document:"
            )

            if not doc_description:
                messagebox.showerror("Error", "Description cannot be empty!")
                return
            # Get template content
            template_path = next(tpl[2] for tpl in self.templates if tpl[1] == self.template_var.get())
            template_index = next(tpl[0] for tpl in self.templates if tpl[1] == self.template_var.get())
            with open(template_path, "r") as f:
                content = f.read()

            # Replace placeholders with user input
            parameters = {}  # Dictionary to store key-value pairs
            for ph, entry in self.input_fields.items():
                value = entry.get()
                content = content.replace(f"{{{{{ph}}}}}", value)
                parameters[ph] = value  # Save key-value pair

            # Create temp directory for LaTeX compilation
            os.makedirs(TEMP_TEX_DIR, exist_ok=True)
            temp_tex = os.path.join(TEMP_TEX_DIR, "temp.tex")

            # Save the temporary .tex file
            with open(temp_tex, "w") as f:
                f.write(content)

            # Save parameters to a .txt file in the data subdirectory
            os.makedirs("data", exist_ok=True)
            param_file_name = f"{self.template_var.get()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            param_file_path = os.path.join("data", param_file_name)
            
            with open(param_file_path, "w") as param_file:
                for key, value in parameters.items():
                    param_file.write(f"{key} = {value}\n")

            # Compile LaTeX to PDF
            os.makedirs(DOCUMENTS_DIR, exist_ok=True)
            # Ask user for custom prefix or use default
            custom_prefix = self.custom_id_entry.get().strip() if self.use_custom_id.get() else None
            if custom_prefix:
                try:
                    validate_custom_id_format(custom_prefix)
                except ValueError as ve:
                    messagebox.showerror("Invalid Format", str(ve))
                    return


            document_id = generate_document_id(self.template_var.get(),template_index, DOCUMENTS_CSV, custom_prefix)
            output_name = document_id  # Ensures uniqueness + clear reference

            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    f"-output-directory={DOCUMENTS_DIR}",
                    f"-jobname={output_name}",
                    f"./{TEMP_TEX_DIR}/{temp_tex}"
                ],
                capture_output=True,
                text=True
            )

            # Check compilation result
            if result.returncode != 0:
                self.show_error_log(result.stderr)
                messagebox.showerror("Compilation Error", "Failed to generate PDF. Check error log.")
            else:
                # Update index.csv with parameter file reference
                self.update_index(output_name, param_file_path, doc_description)
                messagebox.showinfo("Success", f"Document generated: {output_name}.pdf")
                pdf_path = os.path.join(DOCUMENTS_DIR, f"{output_name}.pdf")
                if os.name == 'nt':
                    os.startfile(pdf_path)
                elif os.name == 'posix':
                    subprocess.Popen(['xdg-open', pdf_path])
                else:
                    subprocess.Popen(['open', pdf_path])

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def update_index(self, output_name, param_file_path, doc_description):
        """Update index.csv with new document entry."""
        next_index = get_next_index(DOCUMENTS_CSV)
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_path = os.path.join(DOCUMENTS_DIR, f"{output_name}.pdf")

        new_row = [
            output_name,
            self.template_var.get(),
            current_date,
            doc_description, 
            param_file_path,
            pdf_path
        ]

        with open(DOCUMENTS_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(new_row)

    def show_error_log(self, log):
        """Display LaTeX compilation errors."""
        self.error_log.configure(state="normal")
        self.error_log.delete("1.0", "end")
        self.error_log.insert("end", log)
        self.error_log.configure(state="disabled")

    


class SearchDocumentFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        self.search_vars = {
            "index": ctk.StringVar(),
            "type": ctk.StringVar(),
            "date": ctk.StringVar(),
            "desc": ctk.StringVar()
        }

        ctk.CTkLabel(self, text="Search Previously Generated Documents", font=("Arial", 18)).grid(row=0, column=0, pady=10)

        # Filters
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        filter_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Add labels and entries
        ctk.CTkLabel(filter_frame, text="Document Index").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(filter_frame, text="Date").grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(filter_frame, text="Short Description").grid(row=0, column=2, sticky="w", padx=5)
        ctk.CTkLabel(filter_frame, text="Template Type").grid(row=0, column=3, sticky="w", padx=5)

        ctk.CTkEntry(filter_frame, textvariable=self.search_vars["index"]).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkEntry(filter_frame, textvariable=self.search_vars["date"]).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkEntry(filter_frame, textvariable=self.search_vars["desc"]).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.type_dropdown = ctk.CTkComboBox(filter_frame, values=[], variable=self.search_vars["type"])
        self.type_dropdown.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Search Button
        ctk.CTkButton(self, text="Search", command=self.perform_search).grid(row=2, column=0, pady=10)

        # Scrollable result view
        self.result_frame = ctk.CTkScrollableFrame(self, height=300)
        self.result_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.result_frame.grid_columnconfigure(0, weight=1)

        # Load template types for dropdown
        self.load_template_types()


    def load_template_types(self):
        types = set()
        if os.path.exists("documents.csv"):
            with open("documents.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    types.add(row["Template Type Name"])
        self.type_dropdown.configure(values=[""] + sorted(types))

    def perform_search(self):
        # Clear previous results
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        if not os.path.exists("documents.csv"):
            ctk.CTkLabel(self.result_frame, text="No documents found.").pack()
            return

        with open("documents.csv", newline="") as f:
            reader = csv.DictReader(f)
            matches = []

            for row in reader:
                if self.filter_row(row):
                    matches.append(row)

        if not matches:
            ctk.CTkLabel(self.result_frame, text="No matches found.").pack()
            return

        for i, row in enumerate(matches, start=1):
            self.add_result_row(i, row)

    def filter_row(self, row):
        idx = self.search_vars["index"].get().strip()
        typ = self.search_vars["type"].get().strip()
        date = self.search_vars["date"].get().strip()
        desc = self.search_vars["desc"].get().strip().lower()

        return all([
            (not idx or idx.lower() in row["Document Index Number"].lower()),
            (not typ or typ.lower() in row["Template Type Name"].lower()),
            (not date or date in row["Date of Generation"]),
            (not desc or desc in row["Short Description"].lower()),
        ])


    def add_result_row(self, count, row):
        entry_frame = ctk.CTkFrame(self.result_frame)
        entry_frame.pack(fill="x", pady=4, padx=4)

        summary = f"#{row['Document Index Number']} | {row['Template Type Name']} | {row['Date of Generation']} | {row['Short Description']}"
        ctk.CTkLabel(entry_frame, text=summary, anchor="w").pack(side="left", padx=5, expand=True, fill="x")

        if os.path.exists(row["Path to Generated PDF"]):
            ctk.CTkButton(entry_frame, text="Open PDF", width=100,
                        command=lambda path=row["Path to Generated PDF"]: self.open_pdf(path)).pack(side="right", padx=5)


            # NEW: Delete Button
            ctk.CTkButton(entry_frame, text=" Delete", width=60,
                        command=lambda r=row: self.delete_document(r)).pack(side="right", padx=4)
        if os.path.exists(row["Path to Parameter File"]):
            ctk.CTkButton(entry_frame, text="Regenerate", width=100,
                        command=lambda r=row: self.master.master.show_regenerate_frame(r,edit_mode=False)).pack(side="right", padx=5)
                    # NEW: Edit Button
            ctk.CTkButton(entry_frame, text=" Edit", width=60,
                        command=lambda r=row: self.edit_document(r,True)).pack(side="right", padx=4)


        else:
            ctk.CTkLabel(entry_frame, text="PDF not found", text_color="red").pack(side="right", padx=5)

    def edit_document(self, row_data, mode):
        self.master.master.show_regenerate_frame(row_data, edit_mode=mode)

    def delete_document(self, row_data):
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete document #{row_data['Document Index Number']}?"
        )
        if not confirm:
            return

        # Remove files
        try:
            for path_key in ["Path to Generated PDF", "Path to Parameter File"]:
                path = row_data.get(path_key)
                if path and os.path.exists(path):
                    os.remove(path)

            # Remove .txt parameter file (might be stored in "Path to Template File" by mistake in current code)
            # Check with Sir: if parameter file needs to be deleted
            param_file = row_data.get("Path to Parameter File", "")
            if param_file.endswith(".txt") and os.path.exists(param_file):
                os.remove(param_file)

            # Rewrite CSV without the deleted entry
            updated_rows = []
            with open(DOCUMENTS_CSV, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Document Index Number"] != row_data["Document Index Number"]:
                        updated_rows.append(row)

            with open(DOCUMENTS_CSV, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Document Index Number", "Template Type Name", "Date of Generation",
                    "Short Description", "Path to Parameter File", "Path to Generated PDF"
                ])
                writer.writeheader()
                writer.writerows(updated_rows)

            messagebox.showinfo("Deleted", f"Document #{row_data['Document Index Number']} has been deleted.")
            self.perform_search()  # Refresh results

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete document: {e}")



    def open_pdf(self, path):
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', path])
            else:
                subprocess.Popen(['open', path])
        except Exception as e:
            print(f"Failed to open PDF: {e}")

class SearchTemplateFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        self.search_vars = {
            "index": ctk.StringVar(),
            "type": ctk.StringVar(),
            "date": ctk.StringVar(),
        }

        ctk.CTkLabel(self, text="Search Imported Templates", font=("Arial", 18)).grid(row=0, column=0, pady=10)

        # Filters
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        filter_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Labels
        ctk.CTkLabel(filter_frame, text="Template Index").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(filter_frame, text="Template Name").grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(filter_frame, text="Date of Import (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5)

        # Inputs
        ctk.CTkEntry(filter_frame, textvariable=self.search_vars["index"]).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkEntry(filter_frame, textvariable=self.search_vars["type"]).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkEntry(filter_frame, textvariable=self.search_vars["date"]).grid(row=1, column=2, padx=5, pady=5, sticky="ew")


        # Search button
        ctk.CTkButton(self, text="Search", command=self.perform_search).grid(row=2, column=0, pady=10)

        # Results
        self.result_frame = ctk.CTkScrollableFrame(self, height=300)
        self.result_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.result_frame.grid_columnconfigure(0, weight=1)

        # Populate dropdown values
        # self.load_template_types()

    # def load_template_types(self):
    #     """Load unique template types from templates.csv into the dropdown."""
    #     template_types = set()
    #     if os.path.exists(TEMPLATES_CSV):
    #         with open(TEMPLATES_CSV, newline="") as file:
    #             reader = csv.DictReader(file)
    #             for row in reader:
    #                 template_types.add(row.get("Template Type Name", ""))
    #     self.type_dropdown.configure(values=sorted(list(template_types)))

    def perform_search(self):
        """Search templates.csv using filter criteria and populate results."""
        # Clear previous results
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        filters = {
            "Template Index": self.search_vars["index"].get().strip(),
            "Template Type Name": self.search_vars["type"].get().strip(),
            "Date of Import": self.search_vars["date"].get().strip()
        }

        results = []
        if os.path.exists(TEMPLATES_CSV):
            with open(TEMPLATES_CSV, newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    match = True
                    for key, val in filters.items():
                        if val and val.lower() not in row.get(key, "").lower():
                            match = False
                            break
                    if match:
                        results.append(row)

        if not results:
            ctk.CTkLabel(self.result_frame, text="No matching templates found.").pack(pady=10)
            return

        for row in results:
            row_text = f"{row['Template Index']} | {row['Template Type Name']} | {row['Date of Import']} | {row['Short Description']}"
            entry_frame = ctk.CTkFrame(self.result_frame)
            entry_frame.pack(fill="x", padx=5, pady=2)

            ctk.CTkLabel(entry_frame, text=row_text, anchor="w").pack(side="left", expand=True, fill="x", padx=5)

            ctk.CTkButton(entry_frame, text="Export", width=80,
                        command=lambda r=row: self.export_template(r)).pack(side="right", padx=4)

            ctk.CTkButton(entry_frame, text="Delete", width=80,
                        command=lambda r=row: self.delete_template(r)).pack(side="right", padx=4)
            
    def export_template(self, row_data):
        template_path = row_data.get("Path to Template File")
        if not template_path or not os.path.exists(template_path):
            messagebox.showerror("Error", "Template file not found.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".tex",
            initialfile=os.path.basename(template_path),
            filetypes=[("LaTeX files", "*.tex")],
            title="Export Template"
        )
        if not save_path:
            return

        try:
            shutil.copy(template_path, save_path)
            messagebox.showinfo("Exported", f"Template exported to: {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def delete_template(self, row_data):
        template_name = row_data["Template Type Name"]
        template_path = row_data.get("Path to Template File")

        # Check if template is in use by any document
        in_use = False
        if os.path.exists(DOCUMENTS_CSV):
            with open(DOCUMENTS_CSV, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Template Type Name") == template_name:
                        in_use = True
                        break

        msg = f"Are you sure you want to delete template '{template_name}'?"
        if in_use:
            msg += "\n\n⚠ Warning: This template is referenced by one or more documents!"

        confirm = messagebox.askyesno("Confirm Delete", msg)
        if not confirm:
            return

        try:
            # Remove the .tex file
            if template_path and os.path.exists(template_path):
                os.remove(template_path)

            # Rewrite templates.csv without this row
            updated_rows = []
            with open(TEMPLATES_CSV, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Template Type Name"] != template_name:
                        updated_rows.append(row)

            with open(TEMPLATES_CSV, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Template Index", "Template Type Name", "Date of Import",
                    "Short Description", "Path to Template File"
                ])
                writer.writeheader()
                writer.writerows(updated_rows)

            messagebox.showinfo("Deleted", f"Template '{template_name}' has been deleted.")
            # self.master.master.generate_frame.load_templates()
            self.perform_search()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete template: {e}")



if __name__ == "__main__":
    if shutil.which("pdflatex") is None:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide the base window
        messagebox.showerror(
            "LaTeX Compiler Not Found",
            "The LaTeX engine 'pdflatex' is not available on this system.\n\n"
            "Please install TeX Live or MiKTeX and ensure 'pdflatex' is in your system PATH."
        )
        sys.exit(1)

    app = LaxDocApp()
    app.mainloop()

