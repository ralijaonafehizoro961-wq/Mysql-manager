import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector


# ─────────────────────────────────────────────
# FENÊTRE DE CONNEXION
# ─────────────────────────────────────────────
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion MySQL")
        self.root.geometry("500x400")
        self.root.configure(bg="#07070f")
        self.root.resizable(False, False)
        self.build_ui()

    def build_ui(self):
        # Titre
        tk.Label(
            self.root,
            text="MySQL Manager",
            font=("Arial", 18, "bold"),
            bg="#07070f",
            fg="#7c3aed",
        ).pack(pady=(25, 5))

        tk.Label(
            self.root,
            text="Connecte-toi à ton serveur MySQL",
            font=("Arial", 10),
            bg="#07070f",
            fg="#475569",
        ).pack(pady=(0, 20))

        # Formulaire
        form = tk.Frame(self.root, bg="#0f0f1a", padx=20, pady=20)
        form.pack(fill="x", padx=30)

        fields = [
            ("Host :", "127.0.0.1"),
            ("Port :", "3306"),
            ("User :", "root"),
            ("Password :", ""),
        ]

        self.entries = {}
        for i, (label, default) in enumerate(fields):
            tk.Label(
                form, text=label, font=("Arial", 10, "bold"), bg="#0f0f1a", fg="#e2e8f0"
            ).grid(row=i, column=0, sticky="w", pady=5)

            show = "*" if label == "Password :" else ""
            e = tk.Entry(
                form,
                font=("Arial", 11),
                bg="#1a1a2e",
                fg="#e2e8f0",
                insertbackground="white",
                relief="flat",
                width=22,
                show=show,
            )
            e.insert(0, default)
            e.grid(row=i, column=1, padx=10, pady=5)
            self.entries[label] = e

        form.columnconfigure(1, weight=1)

        # Bouton Connecter
        tk.Button(
            self.root,
            text="Connecter",
            font=("Arial", 11, "bold"),
            bg="#7c3aed",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            command=self.connect,
        ).pack(pady=20)

        # Message erreur
        self.label_error = tk.Label(
            self.root, text="", font=("Arial", 9), bg="#07070f", fg="#ef4444"
        )
        self.label_error.pack()

        # Entrée avec Enter
        self.root.bind("<Return>", lambda e: self.connect())

    def connect(self):
        host = self.entries["Host :"].get().strip()
        port = self.entries["Port :"].get().strip()
        user = self.entries["User :"].get().strip()
        password = self.entries["Password :"].get()

        try:
            conn = mysql.connector.connect(
                host=host, port=int(port), user=user, password=password
            )
            # Connexion réussie — ouvre le manager
            self.root.destroy()
            root2 = tk.Tk()
            ManagerWindow(root2, conn, user, host)
            root2.mainloop()

        except mysql.connector.Error as e:
            self.label_error.config(text=f"❌ Erreur : {e.msg}")


# ─────────────────────────────────────────────
# FENÊTRE PRINCIPALE — MANAGER
# ─────────────────────────────────────────────
class ManagerWindow:
    def __init__(self, root, conn, user, host):
        self.root = root
        self.conn = conn
        self.user = user
        self.host = host
        self.current_db = None
        self.current_table = None
        self.columns = []

        self.root.title(f"MySQL Manager — {user}@{host}")
        self.root.geometry("1000x650")
        self.root.configure(bg="#07070f")
        self.root.resizable(True, True)

        self.build_ui()
        self.load_databases()

    def build_ui(self):
        # ── HEADER ──
        header = tk.Frame(self.root, bg="#1a1a2e", pady=10)
        header.pack(fill="x")

        tk.Label(
            header,
            text="MySQL Manager",
            font=("Arial", 14, "bold"),
            bg="#1a1a2e",
            fg="#7c3aed",
        ).pack(side="left", padx=15)

        tk.Label(
            header,
            text=f"Connecté : {self.user}@{self.host}",
            font=("Arial", 10),
            bg="#1a1a2e",
            fg="#06b6d4",
        ).pack(side="left", padx=10)

        tk.Button(
            header,
            text="🔌 Déconnecter",
            font=("Arial", 9),
            bg="#ef4444",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.disconnect,
        ).pack(side="right", padx=15)

        # ── BODY ──
        body = tk.Frame(self.root, bg="#07070f")
        body.pack(fill="both", expand=True)

        # ── SIDEBAR ──
        sidebar = tk.Frame(body, bg="#0f0f1a", width=200)
        sidebar.pack(side="left", fill="y", padx=(10, 0), pady=10)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="📁 Bases de données",
            font=("Arial", 10, "bold"),
            bg="#0f0f1a",
            fg="#06b6d4",
        ).pack(pady=(10, 5), padx=10, anchor="w")

        self.list_db = tk.Listbox(
            sidebar,
            bg="#1a1a2e",
            fg="#e2e8f0",
            selectbackground="#7c3aed",
            font=("Arial", 10),
            relief="flat",
            borderwidth=0,
        )
        self.list_db.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        self.list_db.bind("<<ListboxSelect>>", self.on_db_select)

        tk.Label(
            sidebar,
            text="📋 Tables",
            font=("Arial", 10, "bold"),
            bg="#0f0f1a",
            fg="#06b6d4",
        ).pack(pady=(5, 5), padx=10, anchor="w")

        self.list_tables = tk.Listbox(
            sidebar,
            bg="#1a1a2e",
            fg="#e2e8f0",
            selectbackground="#7c3aed",
            font=("Arial", 10),
            relief="flat",
            borderwidth=0,
        )
        self.list_tables.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        self.list_tables.bind("<<ListboxSelect>>", self.on_table_select)

        # ── ZONE PRINCIPALE ──
        main_area = tk.Frame(body, bg="#07070f")
        main_area.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Titre table courante
        self.label_table = tk.Label(
            main_area,
            text="← Sélectionne une base et une table",
            font=("Arial", 12, "bold"),
            bg="#07070f",
            fg="#475569",
        )
        self.label_table.pack(anchor="w", pady=(0, 8))

        # Barre de recherche
        search_frame = tk.Frame(main_area, bg="#07070f")
        search_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            search_frame, text="🔍", font=("Arial", 12), bg="#07070f", fg="#06b6d4"
        ).pack(side="left")

        self.entry_search = tk.Entry(
            search_frame,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#e2e8f0",
            insertbackground="white",
            relief="flat",
            width=25,
        )
        self.entry_search.pack(side="left", padx=5)
        self.entry_search.bind("<KeyRelease>", self.on_search)

        tk.Button(
            search_frame,
            text="✖",
            font=("Arial", 9),
            bg="#475569",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=6,
            command=self.clear_search,
        ).pack(side="left", padx=3)

        # Tableau
        tree_frame = tk.Frame(main_area, bg="#07070f")
        tree_frame.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(tree_frame)
        scroll_y.pack(side="right", fill="y")
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#0f0f1a",
            foreground="#e2e8f0",
            fieldbackground="#0f0f1a",
            rowheight=28,
            font=("Arial", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#1a1a2e",
            foreground="#06b6d4",
            font=("Arial", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#7c3aed")])

        self.tree = ttk.Treeview(
            tree_frame,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=12,
        )
        self.tree.pack(fill="both", expand=True)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        # Boutons CRUD
        btn_frame = tk.Frame(main_area, bg="#07070f")
        btn_frame.pack(fill="x", pady=8)

        btns = [
            ("➕ Ajouter", "#7c3aed", self.add_row),
            ("✏️ Modifier", "#06b6d4", self.edit_row),
            ("🗑 Supprimer", "#ef4444", self.delete_row),
            ("🔄 Actualiser", "#475569", self.refresh_table),
        ]
        for text, color, cmd in btns:
            tk.Button(
                btn_frame,
                text=text,
                font=("Arial", 10, "bold"),
                bg=color,
                fg="white",
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=5,
                command=cmd,
            ).pack(side="left", padx=4)

        # Barre de statut
        self.status_bar = tk.Label(
            main_area,
            text="Prêt",
            font=("Arial", 9),
            bg="#0f0f1a",
            fg="#475569",
            anchor="w",
            padx=10,
        )
        self.status_bar.pack(fill="x", pady=(5, 0))

    # ─────────────────────────────────────────
    # CHARGEMENT
    # ─────────────────────────────────────────
    def load_databases(self):
        cursor = self.conn.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = [row[0] for row in cursor.fetchall()]
        self.list_db.delete(0, "end")
        for db in dbs:
            self.list_db.insert("end", db)

    def on_db_select(self, event=None):
        sel = self.list_db.curselection()
        if not sel:
            return
        self.current_db = self.list_db.get(sel[0])
        self.conn.database = self.current_db
        self.load_tables()

    def load_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        self.list_tables.delete(0, "end")
        for t in tables:
            self.list_tables.insert("end", t)
        self.status_bar.config(
            text=f"  Base : {self.current_db} — {len(tables)} table(s)"
        )

    def on_table_select(self, event=None):
        sel = self.list_tables.curselection()
        if not sel:
            return
        self.current_table = self.list_tables.get(sel[0])
        self.label_table.config(
            text=f"📋 {self.current_db} → {self.current_table}", fg="#e2e8f0"
        )
        self.refresh_table()

    def refresh_table(self):
        if not self.current_table:
            return
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM `{self.current_table}`")
        rows = cursor.fetchall()
        self.columns = [desc[0] for desc in cursor.description]

        # Mise à jour colonnes
        self.tree["columns"] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")

        # Mise à jour lignes
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=row)

        self.status_bar.config(text=f"  {len(rows)} ligne(s) dans {self.current_table}")

    def on_search(self, event=None):
        keyword = self.entry_search.get().strip()
        if not self.current_table or not keyword:
            self.refresh_table()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM `{self.current_table}`")
        rows = cursor.fetchall()

        filtered = [
            row
            for row in rows
            if any(keyword.lower() in str(val).lower() for val in row)
        ]
        for row in filtered:
            self.tree.insert("", "end", values=row)

        self.status_bar.config(text=f"  {len(filtered)} résultat(s) pour '{keyword}'")

    def clear_search(self):
        self.entry_search.delete(0, "end")
        self.refresh_table()

    # ─────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────
    def add_row(self):
        if not self.current_table:
            messagebox.showwarning("Attention", "Sélectionne une table d'abord !")
            return
        RowDialog(
            self.root,
            self.conn,
            self.current_table,
            self.columns,
            mode="add",
            callback=self.refresh_table,
        )

    def edit_row(self):
        if not self.current_table:
            messagebox.showwarning("Attention", "Sélectionne une table d'abord !")
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionne une ligne d'abord !")
            return
        values = self.tree.item(selected[0])["values"]
        RowDialog(
            self.root,
            self.conn,
            self.current_table,
            self.columns,
            mode="edit",
            values=values,
            callback=self.refresh_table,
        )

    def delete_row(self):
        if not self.current_table:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionne une ligne d'abord !")
            return

        values = self.tree.item(selected[0])["values"]
        pk_col = self.columns[0]
        pk_val = values[0]

        confirm = messagebox.askyesno(
            "Confirmer", f"Supprimer la ligne où {pk_col} = {pk_val} ?"
        )
        if confirm:
            cursor = self.conn.cursor()
            cursor.execute(
                f"DELETE FROM `{self.current_table}` WHERE `{pk_col}` = %s", (pk_val,)
            )
            self.conn.commit()
            self.refresh_table()
            self.status_bar.config(text=f"  🗑 Ligne supprimée.")

    def disconnect(self):
        self.conn.close()
        self.root.destroy()
        root = tk.Tk()
        LoginWindow(root)
        root.mainloop()


# ─────────────────────────────────────────────
# DIALOGUE AJOUTER / MODIFIER UNE LIGNE
# ─────────────────────────────────────────────
class RowDialog:
    def __init__(
        self, parent, conn, table, columns, mode="add", values=None, callback=None
    ):
        self.conn = conn
        self.table = table
        self.columns = columns
        self.mode = mode
        self.values = values
        self.callback = callback

        self.win = tk.Toplevel(parent)
        self.win.title("➕ Ajouter" if mode == "add" else "✏️ Modifier")
        self.win.geometry("400x450")
        self.win.configure(bg="#07070f")
        self.win.resizable(False, False)
        self.win.grab_set()

        self.build_ui()

    def build_ui(self):
        title = "➕ Ajouter une ligne" if self.mode == "add" else "✏️ Modifier la ligne"
        tk.Label(
            self.win, text=title, font=("Arial", 13, "bold"), bg="#07070f", fg="#7c3aed"
        ).pack(pady=(15, 10))

        form = tk.Frame(self.win, bg="#0f0f1a", padx=20, pady=15)
        form.pack(fill="x", padx=20)

        self.entries = {}
        for i, col in enumerate(self.columns):
            tk.Label(
                form,
                text=f"{col} :",
                font=("Arial", 10, "bold"),
                bg="#0f0f1a",
                fg="#e2e8f0",
            ).grid(row=i, column=0, sticky="w", pady=4)

            e = tk.Entry(
                form,
                font=("Arial", 11),
                bg="#1a1a2e",
                fg="#e2e8f0",
                insertbackground="white",
                relief="flat",
                width=25,
            )

            # Pré-remplir en mode edit
            if self.mode == "edit" and self.values:
                e.insert(0, str(self.values[i]) if self.values[i] is not None else "")

            # Désactiver la PK en mode edit
            if self.mode == "edit" and i == 0:
                e.config(state="disabled", fg="#475569")

            e.grid(row=i, column=1, padx=10, pady=4)
            self.entries[col] = e

        form.columnconfigure(1, weight=1)

        tk.Button(
            self.win,
            text="💾 Enregistrer",
            font=("Arial", 11, "bold"),
            bg="#10b981",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            command=self.save,
        ).pack(pady=20)

    def save(self):
        data = {col: self.entries[col].get() for col in self.columns}

        try:
            cursor = self.conn.cursor()

            if self.mode == "add":
                cols = ", ".join(f"`{c}`" for c in self.columns)
                vals = ", ".join(["%s"] * len(self.columns))
                cursor.execute(
                    f"INSERT INTO `{self.table}` ({cols}) VALUES ({vals})",
                    list(data.values()),
                )

            else:
                pk_col = self.columns[0]
                pk_val = self.values[0]
                sets = ", ".join(f"`{c}` = %s" for c in self.columns[1:])
                vals = [data[c] for c in self.columns[1:]]
                cursor.execute(
                    f"UPDATE `{self.table}` SET {sets} WHERE `{pk_col}` = %s",
                    vals + [pk_val],
                )

            self.conn.commit()
            self.win.destroy()
            if self.callback:
                self.callback()

        except mysql.connector.Error as e:
            messagebox.showerror("Erreur MySQL", str(e))


# ─────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
