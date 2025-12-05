import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import yaml
import json
from generator import generate_document, get_identifiers_from_template

# Set appearance mode and color theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class DataEditor(ctk.CTkToplevel):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.file_path = file_path
        self.title(f"Éditeur de Données - {os.path.basename(file_path)}")
        self.geometry("600x500")
        
        self.rows = []
        
        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.header_frame, text="Clé", width=200, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Valeur", width=300, anchor="w").pack(side="left", padx=5)
        
        # Scrollable Frame for rows
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self.btn_frame, text="Ajouter une ligne", command=self.add_row).pack(side="left", padx=10)
        ctk.CTkButton(self.btn_frame, text="Enregistrer", command=self.save_data, fg_color="green").pack(side="right", padx=10)
        ctk.CTkButton(self.btn_frame, text="Fermer", command=self.destroy, fg_color="gray").pack(side="right", padx=10)
        
        self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                if self.file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f) or {}
            
            # Flatten data purely for simple key-value editing if possible, 
            # OR just handle top-level keys. For this complexity, let's assume flat or user manages keys manually.
            # If data contains nested structures (lists/dicts), showing them as string representation might be safer for now
            # to avoid building a complex tree editor.
            for key, value in data.items():
                self.add_row(key, str(value))
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier : {e}")

    def add_row(self, key="", value=""):
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", pady=2)
        
        entry_key = ctk.CTkEntry(row_frame, width=200)
        entry_key.pack(side="left", padx=5)
        entry_key.insert(0, str(key))
        
        entry_value = ctk.CTkEntry(row_frame, width=300)
        entry_value.pack(side="left", padx=5)
        entry_value.insert(0, str(value))
        
        btn_del = ctk.CTkButton(row_frame, text="X", width=30, fg_color="red", command=lambda f=row_frame: self.delete_row(f))
        btn_del.pack(side="right", padx=5)
        
        self.rows.append((row_frame, entry_key, entry_value))

    def delete_row(self, frame):
        frame.destroy()
        # Remove from list
        self.rows = [r for r in self.rows if r[0] != frame]

    def save_data(self):
        new_data = {}
        try:
            for _, k_entry, v_entry in self.rows:
                key = k_entry.get().strip()
                val = v_entry.get().strip()
                
                # Attempt to convert numbers numbers/booleans if it looks like one
                if val.lower() == 'true': val = True
                elif val.lower() == 'false': val = False
                elif val.isdigit(): val = int(val)
                else:
                    try:
                        val = float(val)
                    except ValueError:
                        pass # Keep as string
                
                if key:
                    new_data[key] = val
                    
            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.file_path.endswith('.json'):
                    json.dump(new_data, f, indent=4, ensure_ascii=False)
                else:
                    yaml.dump(new_data, f, allow_unicode=True)
            
            messagebox.showinfo("Succès", "Données enregistrées avec succès !")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Générateur de Documents Neuropsy")
        self.geometry("750x650")

        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.label_title = ctk.CTkLabel(self, text="Générateur de Documents", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Create Tabview
        self.tabview = ctk.CTkTabview(self, width=700, height=400)
        self.tabview.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_gen = self.tabview.add("Génération")
        self.tab_edit = self.tabview.add("Édition de Données")
        
        self.setup_gen_tab()
        self.setup_edit_tab()

        # Logs/Status (Shared or at bottom)
        self.textbox_logs = ctk.CTkTextbox(self, width=250, height=100)
        self.textbox_logs.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_message("Application prête.")

    def setup_gen_tab(self):
        # Configure grid for Gen tab
        self.tab_gen.grid_columnconfigure(0, weight=1)
        
        # --- Template Selection ---
        self.frame_template = ctk.CTkFrame(self.tab_gen)
        self.frame_template.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frame_template.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_template, text="Modèle (.docx):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_template = ctk.CTkEntry(self.frame_template, placeholder_text="Sélectionner le fichier modèle")
        self.entry_template.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.frame_template, text="Parcourir", command=self.browse_template).grid(row=0, column=2, padx=10, pady=10)

        # --- Data Selection ---
        self.frame_data = ctk.CTkFrame(self.tab_gen)
        self.frame_data.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.frame_data.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_data, text="Données (.yaml):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_data = ctk.CTkEntry(self.frame_data, placeholder_text="Sélectionner le fichier de données")
        self.entry_data.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.frame_data, text="Parcourir", command=self.browse_data).grid(row=0, column=2, padx=10, pady=10)

        # --- Output Selection ---
        self.frame_output = ctk.CTkFrame(self.tab_gen)
        self.frame_output.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.frame_output.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_output, text="Sortie (Optionnel):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_output = ctk.CTkEntry(self.frame_output, placeholder_text="Dossier ou nom de fichier (ex: rapport.docx)")
        self.entry_output.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.frame_output, text="Dossier", command=self.browse_output_dir).grid(row=0, column=2, padx=5, pady=10)
        ctk.CTkButton(self.frame_output, text="Fichier", command=self.browse_output_file).grid(row=0, column=3, padx=5, pady=10)

        # --- Generate Button ---
        self.btn_generate = ctk.CTkButton(self.tab_gen, text="Générer le Document", command=self.start_generation, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_generate.grid(row=3, column=0, padx=20, pady=20)

    def setup_edit_tab(self):
        # Configure grid for Edit tab
        self.tab_edit.grid_columnconfigure(0, weight=1)
        
        # --- Edit Existing ---
        self.frame_edit_exist = ctk.CTkFrame(self.tab_edit)
        self.frame_edit_exist.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frame_edit_exist.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.frame_edit_exist, text="Éditer un fichier existant", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=5)
        
        ctk.CTkLabel(self.frame_edit_exist, text="Fichier (.yaml):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_edit_path = ctk.CTkEntry(self.frame_edit_exist, placeholder_text="Chemin du fichier à éditer")
        self.entry_edit_path.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.frame_edit_exist, text="Parcourir", command=self.browse_edit_file).grid(row=1, column=2, padx=10, pady=5)
        
        ctk.CTkButton(self.frame_edit_exist, text="Ouvrir l'Éditeur", command=self.open_editor, fg_color="orange").grid(row=2, column=0, columnspan=3, pady=10)

        # --- Divider ---
        ctk.CTkLabel(self.tab_edit, text="--- OU ---").grid(row=1, column=0, pady=5)

        # --- Create from Template ---
        self.frame_create = ctk.CTkFrame(self.tab_edit)
        self.frame_create.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.frame_create.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_create, text="Créer un nouveau fichier depuis un Template Word", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=5)

        ctk.CTkLabel(self.frame_create, text="Modèle (.docx):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_create_template = ctk.CTkEntry(self.frame_create, placeholder_text="Séléctionner le template source")
        self.entry_create_template.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.frame_create, text="Parcourir", command=self.browse_create_template).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkButton(self.frame_create, text="Générer Configuration Vide", command=self.create_config_from_template, fg_color="teal").grid(row=2, column=0, columnspan=3, pady=10)

    # --- Callbacks ---

    def browse_template(self):
        initial_dir = os.path.join(os.getcwd(), "templates")
        if not os.path.exists(initial_dir): os.makedirs(initial_dir)
        filename = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Word Documents", "*.docx")])
        if filename:
            self.entry_template.delete(0, tk.END)
            self.entry_template.insert(0, filename)

    def browse_data(self):
        initial_dir = os.path.join(os.getcwd(), "data")
        if not os.path.exists(initial_dir): os.makedirs(initial_dir)
        filename = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Data Files", "*.yaml *.yml *.json")])
        if filename:
            self.entry_data.delete(0, tk.END)
            self.entry_data.insert(0, filename)
    
    def browse_output_dir(self):
        initial_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(initial_dir): os.makedirs(initial_dir)
        dirname = filedialog.askdirectory(initialdir=initial_dir)
        if dirname:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, dirname)

    def browse_output_file(self):
        initial_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(initial_dir): os.makedirs(initial_dir)
        filename = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx")],
            title="Enregistrer sous..."
        )
        if filename:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, filename)

    def browse_edit_file(self):
        initial_dir = os.path.join(os.getcwd(), "data")
        if not os.path.exists(initial_dir): os.makedirs(initial_dir)
        filename = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Data Files", "*.yaml *.yml *.json")])
        if filename:
            self.entry_edit_path.delete(0, tk.END)
            self.entry_edit_path.insert(0, filename)

    def browse_create_template(self):
        initial_dir = os.path.join(os.getcwd(), "templates")
        if not os.path.exists(initial_dir): os.makedirs(initial_dir)
        filename = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Word Documents", "*.docx")])
        if filename:
            self.entry_create_template.delete(0, tk.END)
            self.entry_create_template.insert(0, filename)

    def open_editor(self):
        file_path = self.entry_edit_path.get()
        if not file_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier à éditer.")
            return
        if not os.path.exists(file_path):
             messagebox.showerror("Erreur", "Le fichier n'existe pas.")
             return
        DataEditor(self, file_path)

    def create_config_from_template(self):
        template_path = self.entry_create_template.get()
        if not template_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un template.")
            return
        
        try:
            keys = get_identifiers_from_template(template_path)
            if not keys:
                messagebox.showinfo("Info", "Aucune variable trouvée.")
                return

            output_file = filedialog.asksaveasfilename(
                defaultextension=".yaml",
                filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json")],
                title="Enregistrer le fichier de configuration"
            )
            
            if not output_file:
                return 

            data = {key: "" for key in keys}
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.endswith('.json'):
                    json.dump(data, f, indent=4, ensure_ascii=False)
                else:
                    yaml.dump(data, f, allow_unicode=True)
            
            self.log_message(f"Configuration créée : {output_file}")
            
            # Auto-load into editor input
            self.entry_edit_path.delete(0, tk.END)
            self.entry_edit_path.insert(0, output_file)
            
            if messagebox.askyesno("Succès", "Fichier créé ! L'ouvrir dans l'éditeur ?"):
                self.open_editor()

        except Exception as e:
            self.log_message(f"Erreur : {e}")
            messagebox.showerror("Erreur", str(e))

    def log_message(self, message):
        self.textbox_logs.insert(tk.END, message + "\n")
        self.textbox_logs.see(tk.END)

    def start_generation(self):
        template_path = self.entry_template.get()
        data_path = self.entry_data.get()
        output_dir = self.entry_output.get()

        if not template_path or not data_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner Template et Données.")
            return

        self.btn_generate.configure(state="disabled")
        self.log_message("Génération...")
        thread = threading.Thread(target=self.run_generation, args=(template_path, data_path, output_dir))
        thread.start()

    def run_generation(self, template_path, data_path, output_path_input):
        try:
            # Determine true output path
            if not output_path_input:
                # Case 1: Empty input -> Default to output/ dir with auto name
                output_dir = "output"
                if not os.path.exists(output_dir): os.makedirs(output_dir)
                base_name = os.path.splitext(os.path.basename(template_path))[0]
                final_output_path = os.path.join(output_dir, f"{base_name}_generated.docx")
            
            elif os.path.isdir(output_path_input):
                # Case 2: Input is a directory -> Save there with auto name
                base_name = os.path.splitext(os.path.basename(template_path))[0]
                final_output_path = os.path.join(output_path_input, f"{base_name}_generated.docx")
            
            else:
                # Case 3: Input is a file path (or doesn't exist yet, assumed file)
                if not output_path_input.lower().endswith(".docx"):
                    output_path_input += ".docx"
                final_output_path = output_path_input
                
                # Ensure parent dir exists
                parent_dir = os.path.dirname(final_output_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)

            generate_document(template_path, data_path, final_output_path)
            
            self.log_message(f"Succès ! -> {final_output_path}")
            # Success popup removed as requested
            
        except Exception as e:
            self.log_message(f"Erreur : {str(e)}")
            messagebox.showerror("Erreur", str(e))
        finally:
            self.btn_generate.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
