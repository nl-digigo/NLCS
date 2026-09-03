"""
rn_gui.py - tkinter-venster voor de release notes tool.

Flow:
  1. Token + owner/repo/states invoeren -> knop 'Ophalen' haalt alle issues op.
  2. Milestones aanvinken (filter bij ophalen) + te-tonen-labels aanvinken
     (alleen voor de HTML) + tag + vinkje 'alleen issues met release note'.
  3. Knop 'Genereer HTML' schrijft het bestand en opent het (optioneel).

Instellingen (behalve het token) worden onthouden via rn_config.
"""

import os
import queue
import threading
import webbrowser

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import rn_auth
import rn_config
import rn_extract
import rn_fetch
import rn_html


# ---------------------------------------------------------------------------
# Herbruikbaar: scrollbare lijst met aanvinkvakjes
# ---------------------------------------------------------------------------
class ScrollableChecklist(ttk.Frame):
    """Een aanvinklijst met scrollbalk en 'Alles'/'Niets'-knoppen."""

    def __init__(self, master, title: str, height: int = 170):
        super().__init__(master)

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text=title, font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Button(header, text="Niets", width=6,
                   command=lambda: self.set_all(False)).pack(side="right")
        ttk.Button(header, text="Alles", width=6,
                   command=lambda: self.set_all(True)).pack(side="right")

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, height=height, highlightthickness=1,
                                highlightbackground="#c8ccd0")
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Muiswiel alleen als de cursor boven de lijst is
        self.canvas.bind("<Enter>",
                         lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>",
                         lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.vars: dict[str, tk.BooleanVar] = {}

    def _wheel(self, event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def set_items(self, items: list[str], checked=None) -> None:
        """Vul de lijst; items in `checked` worden aangevinkt."""
        checked = set(checked or [])
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.vars = {}
        for item in items:
            var = tk.BooleanVar(value=(item in checked))
            ttk.Checkbutton(self.inner, text=item, variable=var).pack(anchor="w")
            self.vars[item] = var

    def checked(self) -> list[str]:
        return [name for name, var in self.vars.items() if var.get()]

    def set_all(self, value: bool) -> None:
        for var in self.vars.values():
            var.set(value)


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill="both", expand=True)

        self.issues: list[dict] = []
        self.milestones_meta: list[dict] = []   # [{"number":int,"title":str}]
        self.labels_all: list[str] = []
        self.cfg = rn_config.load()
        self._queue: queue.Queue = queue.Queue()
        self._login_cancel = False

        self._build_connection()
        self._build_selection()
        self._build_output()
        self._apply_config()

        master.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- opbouw ------------------------------------------------------------
    def _build_connection(self) -> None:
        frame = ttk.LabelFrame(self, text="1. Verbinding", padding=8)
        frame.pack(fill="x")

        # Interne variabelen (geen invoervelden meer in de interface):
        # de client-id zit vast in de tool (rn_auth.DEFAULT_CLIENT_ID) en het
        # token wordt automatisch verkregen via de browser-login.
        self.client_id_var = tk.StringVar()
        self.token_var = tk.StringVar()

        # -- Inloggen via GitHub (browser / OAuth Device Flow) -------------
        ttk.Label(frame, text="Inloggen:").grid(row=0, column=0, sticky="w")
        self.login_btn = ttk.Button(frame, text="Inloggen via GitHub",
                                     command=self.on_login)
        self.login_btn.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        self.login_state_var = tk.StringVar(value="niet ingelogd")
        ttk.Label(frame, textvariable=self.login_state_var, foreground="#555"
                  ).grid(row=0, column=2, columnspan=2, sticky="w")

        ttk.Label(frame, text="Owner:").grid(row=1, column=0, sticky="w")
        self.owner_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.owner_var, width=20
                  ).grid(row=1, column=1, sticky="w", padx=4, pady=2)

        ttk.Label(frame, text="Repo:").grid(row=1, column=2, sticky="e")
        self.repo_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.repo_var, width=20
                  ).grid(row=1, column=3, sticky="w", padx=4, pady=2)

        ttk.Label(frame, text="States:").grid(row=2, column=0, sticky="w")
        states_frame = ttk.Frame(frame)
        states_frame.grid(row=2, column=1, sticky="w")
        self.open_var = tk.BooleanVar(value=True)
        self.closed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(states_frame, text="OPEN", variable=self.open_var
                        ).pack(side="left")
        ttk.Checkbutton(states_frame, text="CLOSED", variable=self.closed_var
                        ).pack(side="left", padx=(8, 0))

        self.connect_btn = ttk.Button(frame, text="Verbinden", command=self.on_connect)
        self.connect_btn.grid(row=2, column=2, columnspan=2, sticky="e", padx=4)

        self.status_var = tk.StringVar(
            value="Klik 'Inloggen via GitHub' en daarna 'Verbinden'.")
        ttk.Label(frame, textvariable=self.status_var, foreground="#555"
                  ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

        frame.columnconfigure(1, weight=1)

    def _build_selection(self) -> None:
        frame = ttk.LabelFrame(self, text="2. Selectie", padding=8)
        frame.pack(fill="both", expand=True, pady=8)

        # Ophalen filtert alleen op milestones; de labellijst bepaalt puur
        # wat er in de HTML getóónd wordt (leeg = alle labels tonen).
        lists = ttk.Frame(frame)
        lists.pack(fill="both", expand=True)
        self.ms_list = ScrollableChecklist(lists, "Milestones (filter bij ophalen)")
        self.ms_list.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.showlabel_list = ScrollableChecklist(lists, "Toon deze labels in HTML (leeg = alle)")
        self.showlabel_list.pack(side="left", fill="both", expand=True, padx=(6, 0))

        options = ttk.Frame(frame)
        options.pack(fill="x", pady=(8, 0))
        ttk.Label(options, text="Tag:").pack(side="left")
        self.tag_var = tk.StringVar()
        ttk.Entry(options, textvariable=self.tag_var, width=24
                  ).pack(side="left", padx=(4, 16))
        self.require_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text="alleen issues met release note",
                        variable=self.require_var).pack(side="left")

        # Ophalen sluit sectie 2 af: eerst selecteren, dan ophalen, dan uitvoer.
        self.fetch_btn = ttk.Button(options, text="Ophalen", command=self.on_fetch,
                                    state="disabled")
        self.fetch_btn.pack(side="right")

    def _build_output(self) -> None:
        frame = ttk.LabelFrame(self, text="3. Uitvoer", padding=8)
        frame.pack(fill="x")

        ttk.Label(frame, text="Titel:").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.title_var, width=40
                  ).grid(row=0, column=1, columnspan=2, sticky="we", padx=4, pady=2)

        ttk.Label(frame, text="HTML-bestand:").grid(row=1, column=0, sticky="w")
        self.output_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.output_var, width=40
                  ).grid(row=1, column=1, sticky="we", padx=4, pady=2)
        ttk.Button(frame, text="Bladeren...", command=self._browse_output
                   ).grid(row=1, column=2, sticky="w", padx=4)

        self.open_after_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="openen na genereren",
                        variable=self.open_after_var
                        ).grid(row=2, column=1, sticky="w", pady=2)

        self.gen_btn = ttk.Button(frame, text="Genereer HTML",
                                  command=self.on_generate, state="disabled")
        self.gen_btn.grid(row=2, column=2, sticky="e", padx=4)

        frame.columnconfigure(1, weight=1)

    # -- config toepassen/opslaan -----------------------------------------
    def _apply_config(self) -> None:
        c = self.cfg
        self.owner_var.set(c["owner"])
        self.repo_var.set(c["repo"])
        self.client_id_var.set(c.get("oauth_client_id") or rn_auth.DEFAULT_CLIENT_ID)
        self.open_var.set("OPEN" in c["states"])
        self.closed_var.set("CLOSED" in c["states"])
        self.tag_var.set(c["tag"])
        self.require_var.set(bool(c["require_tag"]))
        self.title_var.set(c["title"])
        self.open_after_var.set(bool(c["open_after"]))
        default_out = c["output"] or os.path.join(rn_config.base_dir(),
                                                   "releasenotes.html")
        self.output_var.set(default_out)

    def _collect_config(self) -> dict:
        return {
            "owner": self.owner_var.get().strip(),
            "repo": self.repo_var.get().strip(),
            "oauth_client_id": self.client_id_var.get().strip(),
            "states": self._states(),
            "tag": self.tag_var.get(),
            "require_tag": self.require_var.get(),
            "milestones": self.ms_list.checked(),
            "show_labels": self.showlabel_list.checked(),
            "title": self.title_var.get(),
            "output": self.output_var.get(),
            "open_after": self.open_after_var.get(),
        }

    def _on_close(self) -> None:
        rn_config.save(self._collect_config())
        self.master.destroy()

    # -- helpers -----------------------------------------------------------
    def _states(self) -> list[str]:
        states = []
        if self.open_var.get():
            states.append("OPEN")
        if self.closed_var.get():
            states.append("CLOSED")
        return states

    def _browse_output(self) -> None:
        # Open de dialoog in de map van het huidige pad, zodat een eerder gekozen
        # locatie (bijv. docs/changelog/releasenotes) meteen in beeld is.
        current = self.output_var.get().strip()
        initial_dir = os.path.dirname(current) if current else rn_config.base_dir()
        if not os.path.isdir(initial_dir):
            initial_dir = rn_config.base_dir()
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Alle bestanden", "*.*")],
            initialdir=initial_dir,
            initialfile=os.path.basename(current or "releasenotes.html"))
        if path:
            self.output_var.set(path)

    # -- inloggen via GitHub (OAuth Device Flow, in aparte thread) --------
    def on_login(self) -> None:
        client_id = self.client_id_var.get().strip() or rn_auth.DEFAULT_CLIENT_ID
        if not client_id:
            messagebox.showerror(
                "Geen OAuth-app ingesteld",
                "Er is geen Client ID in de tool ingebouwd. Neem contact op "
                "met de beheerder van deze tool.")
            return
        self.client_id_var.set(client_id)

        self._login_cancel = False
        self.login_btn.config(state="disabled")
        self.login_state_var.set("bezig met inloggen...")
        self.status_var.set("Inlogcode aanvragen bij GitHub...")

        def worker():
            try:
                dev = rn_auth.request_device_code(client_id)
                self._queue.put(("device_code", dev))
                token = rn_auth.poll_for_token(
                    client_id, dev["device_code"],
                    interval=dev.get("interval", 5),
                    expires_in=dev.get("expires_in", 900),
                    on_wait=lambda m: self._queue.put(("progress", m)),
                    should_cancel=lambda: self._login_cancel)
                self._queue.put(("token", token))
            except Exception as exc:  # noqa: BLE001 - tonen in de GUI
                self._queue.put(("error_login", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_queue)

    # -- verbinden: milestones + labels laden (in aparte thread) ----------
    def on_connect(self) -> None:
        token = self.token_var.get().strip()
        if not token:
            # Nog geen token: als er een client-id is, log dan eerst in via de
            # browser (bij succes wordt on_connect automatisch opnieuw gestart).
            if self.client_id_var.get().strip():
                self.on_login()
            else:
                messagebox.showwarning(
                    "Nog niet ingelogd",
                    "Klik 'Inloggen via GitHub' (of plak een token) en "
                    "probeer opnieuw.")
            return
        owner = self.owner_var.get().strip()
        repo = self.repo_var.get().strip()
        self.connect_btn.config(state="disabled")
        self.status_var.set("Verbinden...")

        def worker():
            try:
                milestones, labels = rn_fetch.fetch_repo_lists(
                    token, owner, repo,
                    progress=lambda m: self._queue.put(("progress", m)))
                self._queue.put(("lists", (milestones, labels)))
            except Exception as exc:  # noqa: BLE001 - tonen in de GUI
                self._queue.put(("error_connect", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_queue)

    # -- ophalen (gefilterd, in aparte thread) ----------------------------
    def on_fetch(self) -> None:
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("Token ontbreekt",
                                   "Vul eerst je GitHub-token in.")
            return
        states = self._states()
        if not states:
            messagebox.showwarning("Geen states", "Kies OPEN en/of CLOSED.")
            return

        owner = self.owner_var.get().strip()
        repo = self.repo_var.get().strip()

        # Aangevinkte milestone-titels omzetten naar milestone-nummers
        chosen_titles = set(self.ms_list.checked())
        milestone_numbers = [m["number"] for m in self.milestones_meta
                             if m["title"] in chosen_titles] or None

        self.fetch_btn.config(state="disabled")
        self.status_var.set("Ophalen...")

        def worker():
            try:
                # Bewust geen label-filter: we halen alle issues van de gekozen
                # milestones op en bepalen pas in de HTML welke labels we tonen.
                issues = rn_fetch.fetch_issues(
                    token, owner, repo, states,
                    milestone_numbers=milestone_numbers,
                    label_names=None,
                    progress=lambda m: self._queue.put(("progress", m)))
                self._queue.put(("done", issues))
            except Exception as exc:  # noqa: BLE001 - tonen in de GUI
                self._queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_queue)

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "progress":
                    self.status_var.set(payload)
                elif kind == "device_code":
                    self._show_device_code(payload)
                    # blijf pollen: het worker-token komt later binnen
                elif kind == "token":
                    self.token_var.set(payload)
                    self.login_state_var.set("ingelogd ✓")
                    self.login_btn.config(state="normal")
                    self.status_var.set("Ingelogd. Milestones en labels laden...")
                    self.on_connect()   # meteen doorpakken
                    return
                elif kind == "error_login":
                    messagebox.showerror("Fout bij inloggen", payload)
                    self.login_state_var.set("niet ingelogd")
                    self.status_var.set("Inloggen mislukt.")
                    self.login_btn.config(state="normal")
                    return
                elif kind == "lists":
                    milestones, labels = payload
                    self.milestones_meta = milestones
                    self.labels_all = labels
                    self._populate_lists()
                    self.status_var.set(
                        f"{len(milestones)} milestones, {len(labels)} labels geladen. "
                        "Kies een selectie en klik 'Ophalen'.")
                    self.connect_btn.config(state="normal")
                    self.fetch_btn.config(state="normal")
                    return
                elif kind == "done":
                    self.issues = payload
                    self.status_var.set(f"{len(payload)} issues opgehaald.")
                    self.fetch_btn.config(state="normal")
                    self.gen_btn.config(
                        state=("normal" if payload else "disabled"))
                    if not payload:
                        messagebox.showinfo(
                            "Niets gevonden",
                            "Geen issues gevonden voor deze selectie.")
                    return
                elif kind == "error":
                    messagebox.showerror("Fout bij ophalen", payload)
                    self.status_var.set("Ophalen mislukt.")
                    self.fetch_btn.config(state="normal")
                    return
                elif kind == "error_connect":
                    messagebox.showerror("Fout bij verbinden", payload)
                    self.status_var.set("Verbinden mislukt.")
                    self.connect_btn.config(state="normal")
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _show_device_code(self, dev: dict) -> None:
        """Toon de inlogcode, kopieer hem en open de GitHub-verificatiepagina."""
        code = dev.get("user_code", "")
        url = dev.get("verification_uri", "https://github.com/login/device")
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
        except tk.TclError:
            pass
        self.login_state_var.set(f"code: {code}")
        webbrowser.open(url)
        messagebox.showinfo(
            "Inloggen via GitHub",
            f"Je browser opent nu {url}\n\n"
            f"Typ (of plak) deze code:\n\n        {code}\n\n"
            "De code staat al op je klembord. Log in met je GitHub-account "
            "en geef toegang. Daarna gaat dit programma vanzelf verder.")
        self.status_var.set("Wachten op goedkeuring in de browser...")

    def _populate_lists(self) -> None:
        """Vul de aanvinklijsten uit de repo-lijsten (met vorige keuzes)."""
        titles = [m["title"] for m in self.milestones_meta]
        self.ms_list.set_items(titles, checked=self.cfg.get("milestones"))
        self.showlabel_list.set_items(self.labels_all,
                                      checked=self.cfg.get("show_labels"))

    # -- genereren ---------------------------------------------------------
    def on_generate(self) -> None:
        if not self.issues:
            messagebox.showwarning("Geen data", "Haal eerst issues op.")
            return
        output = self.output_var.get().strip()
        if not output:
            messagebox.showwarning("Geen bestand", "Kies een HTML-bestand.")
            return

        tag = self.tag_var.get()
        milestones = self.ms_list.checked() or None
        show_labels = self.showlabel_list.checked() or None  # None = alle tonen

        # Geen label-filter meer op de selectie; labels bepalen alleen wat
        # er in de HTML zichtbaar is (show_labels).
        selection = rn_extract.filter_issues(
            self.issues, milestones=milestones, labels=None,
            tag=tag, require_tag=self.require_var.get())

        if not selection:
            messagebox.showinfo("Niets gevonden",
                                "Geen issues voldoen aan de selectie.")
            return

        try:
            rn_html.save_html(selection, output, tag=tag,
                              show_labels=show_labels,
                              title=self.title_var.get() or "Release Notes")
        except OSError as exc:
            messagebox.showerror("Fout bij opslaan", str(exc))
            return

        rn_config.save(self._collect_config())
        self.status_var.set(f"{len(selection)} issues -> {output}")

        if self.open_after_var.get():
            webbrowser.open(os.path.abspath(output))
        else:
            messagebox.showinfo("Klaar", f"{len(selection)} issues opgeslagen in:\n{output}")


def run() -> None:
    root = tk.Tk()
    root.title("NLCS Release Notes")
    root.geometry("920x680")
    root.minsize(760, 560)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    run()
