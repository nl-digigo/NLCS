"""
pm_gui.py - Tkinter-GUI voor het samenvoegen van de NLCS-publicaties.

Laat de gebruiker inloggen (Laces token-id + wachtwoord; NIET opgeslagen), een
BASIS-URL kiezen (bijv. .../nlcs/live of .../nlcs/test) en daaronder aangeven
WELKE publicaties (op naam) worden opgenomen. De volledige publicatie-URL wordt
opgebouwd als <basis-URL>/<publicatienaam>. De eigenlijke merge-logica komt uit
publication_merger.py (via pm_core).
"""

import logging
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pm_core


class QueueLogHandler(logging.Handler):
    """Stuurt logregels (van publication_merger) naar de GUI-queue."""

    def __init__(self, q: "queue.Queue"):
        super().__init__(level=logging.INFO)
        self.q = q

    def emit(self, record):
        try:
            self.q.put(("log", self.format(record)))
        except Exception:
            pass


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.pack(fill="both", expand=True)
        self._queue: "queue.Queue" = queue.Queue()
        self._busy = False
        self.names: list[str] = []
        self._build()
        self.after(120, self._poll)

    # -- opbouw ------------------------------------------------------------
    def _build(self) -> None:
        ttk.Label(self, text="NLCS publicaties samenvoegen",
                  font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(self, foreground="#555",
                  text="Log in met je Laces token-id + wachtwoord, kies de "
                       "basis-URL en de op te nemen publicaties, en klik "
                       "'Samenvoegen'. Inloggegevens worden niet opgeslagen."
                  ).pack(anchor="w", pady=(0, 10))

        # Inloggen
        login = ttk.LabelFrame(self, text="Inloggen (Laces)", padding=8)
        login.pack(fill="x")
        ttk.Label(login, text="Token-ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.token_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.token_var, width=48).grid(
            row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Label(login, text="Wachtwoord:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.pw_var = tk.StringVar()
        self.pw_entry = ttk.Entry(login, textvariable=self.pw_var, width=48, show="*")
        self.pw_entry.grid(row=1, column=1, sticky="we", padx=4, pady=3)
        self.show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(login, text="Toon", variable=self.show_pw,
                        command=self._toggle_pw).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        # Basis-URL
        basef = ttk.LabelFrame(self, text="Basis-URL van de publicaties", padding=8)
        basef.pack(fill="x", pady=(8, 0))
        self.base_var = tk.StringVar(value=self._default_base())
        ttk.Entry(basef, textvariable=self.base_var).pack(
            side="left", fill="x", expand=True, padx=(4, 6))
        ttk.Label(basef, text="bijv. …/nlcs/live  of  …/nlcs/test",
                  foreground="#777").pack(side="right")

        # Publicaties
        pubs = ttk.LabelFrame(self, text="Publicaties (naam onder de basis-URL)",
                              padding=8)
        pubs.pack(fill="both", expand=True, pady=8)
        topbar = ttk.Frame(pubs)
        topbar.pack(fill="x")
        ttk.Button(topbar, text="Alles", width=8,
                   command=lambda: self._select_all(True)).pack(side="left")
        ttk.Button(topbar, text="Niets", width=8,
                   command=lambda: self._select_all(False)).pack(side="left", padx=4)
        ttk.Button(topbar, text="Standaard", width=10,
                   command=self._reset_names).pack(side="left", padx=4)
        self.count_var = tk.StringVar(value="")
        ttk.Label(topbar, textvariable=self.count_var, foreground="#555"
                  ).pack(side="right")

        listwrap = ttk.Frame(pubs)
        listwrap.pack(fill="both", expand=True, pady=(6, 0))
        self.listbox = tk.Listbox(listwrap, selectmode="extended", height=11,
                                  activestyle="none", exportselection=False)
        sb = ttk.Scrollbar(listwrap, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._update_count())

        addbar = ttk.Frame(pubs)
        addbar.pack(fill="x", pady=(6, 0))
        self.add_var = tk.StringVar()
        e = ttk.Entry(addbar, textvariable=self.add_var)
        e.pack(side="left", fill="x", expand=True, padx=(0, 6))
        e.bind("<Return>", lambda ev: self._add_name())
        ttk.Button(addbar, text="Toevoegen", command=self._add_name).pack(side="left")
        ttk.Button(addbar, text="Verwijder selectie",
                   command=self._remove_names).pack(side="left", padx=4)

        self._set_names(self._default_names())

        # Uitvoer
        out = ttk.LabelFrame(self, text="Uitvoer (Turtle)", padding=8)
        out.pack(fill="x")
        self.out_var = tk.StringVar(value=self._default_output())
        ttk.Entry(out, textvariable=self.out_var).pack(
            side="left", fill="x", expand=True, padx=(4, 6))
        ttk.Button(out, text="Bladeren…", command=self._browse).pack(side="right")

        # Actie + voortgang
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(10, 4))
        self.run_btn = ttk.Button(actions, text="Samenvoegen", command=self.on_run)
        self.run_btn.pack(side="left")
        self.status_var = tk.StringVar(value="Klaar.")
        ttk.Label(actions, textvariable=self.status_var, foreground="#555"
                  ).pack(side="left", padx=10)

        logframe = ttk.LabelFrame(self, text="Voortgang", padding=6)
        logframe.pack(fill="both", expand=True)
        self.log = tk.Text(logframe, height=9, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        ls = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=ls.set)
        self.log.pack(side="left", fill="both", expand=True)
        ls.pack(side="right", fill="y")

    # -- helpers -----------------------------------------------------------
    def _toggle_pw(self) -> None:
        self.pw_entry.configure(show="" if self.show_pw.get() else "*")

    def _default_base(self) -> str:
        urls = pm_core.PUBLICATIONS
        if urls:
            return urls[0].rstrip("/").rsplit("/", 1)[0]
        return "https://hub.laces.tech/digitalbuildingdata/nlcs/live"

    def _default_names(self) -> list[str]:
        return [u.rstrip("/").rsplit("/", 1)[-1] for u in pm_core.PUBLICATIONS]

    def _set_names(self, names) -> None:
        self.names = list(names)
        self.listbox.delete(0, "end")
        for n in self.names:
            self.listbox.insert("end", n)
        self._select_all(True)

    def _reset_names(self) -> None:
        self.base_var.set(self._default_base())
        self._set_names(self._default_names())

    def _add_name(self) -> None:
        n = self.add_var.get().strip()
        if "/" in n:                     # hele URL geplakt -> laatste segment
            n = n.rstrip("/").rsplit("/", 1)[-1]
        if n and n not in self.names:
            self.names.append(n)
            self.listbox.insert("end", n)
            self.listbox.select_set("end")
        self.add_var.set("")
        self._update_count()

    def _remove_names(self) -> None:
        for i in reversed(self.listbox.curselection()):
            del self.names[i]
            self.listbox.delete(i)
        self._update_count()

    def _default_output(self) -> str:
        p = pm_core.DEFAULT_OUTPUT
        if not os.path.isabs(p):
            here = os.path.dirname(os.path.abspath(__file__))
            root = os.path.abspath(os.path.join(here, "..", ".."))
            p = os.path.normpath(os.path.join(root, p))
        return p

    def _select_all(self, state: bool) -> None:
        if state:
            self.listbox.select_set(0, "end")
        else:
            self.listbox.select_clear(0, "end")
        self._update_count()

    def _update_count(self) -> None:
        self.count_var.set(f"{len(self.listbox.curselection())} van "
                           f"{len(self.names)} geselecteerd")

    def _browse(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Opslaan als", defaultextension=".ttl",
            initialfile=os.path.basename(self.out_var.get() or "merged.ttl"),
            filetypes=[("Turtle", "*.ttl"), ("Alle bestanden", "*.*")])
        if path:
            self.out_var.set(path)

    def _logmsg(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # -- uitvoeren ---------------------------------------------------------
    def on_run(self) -> None:
        if self._busy:
            return
        token = self.token_var.get().strip()
        pw = self.pw_var.get()
        if not token or not pw:
            messagebox.showwarning("Inloggen", "Vul token-id én wachtwoord in.")
            return
        base = self.base_var.get().strip().rstrip("/")
        if not base:
            messagebox.showwarning("Basis-URL", "Vul een basis-URL in.")
            return
        sel_names = [self.names[i] for i in self.listbox.curselection()]
        if not sel_names:
            messagebox.showwarning("Publicaties", "Selecteer minstens één publicatie.")
            return
        output = self.out_var.get().strip()
        if not output:
            messagebox.showwarning("Uitvoer", "Kies een uitvoerbestand.")
            return
        sel = [f"{base}/{n}" for n in sel_names]

        self._busy = True
        self.run_btn.configure(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status_var.set("Bezig…")
        self._logmsg(f"{len(sel)} publicatie(s) samenvoegen → {output}")

        t = threading.Thread(target=self._worker, args=(sel, token, pw, output),
                             daemon=True)
        t.start()

    def _worker(self, sel, token, pw, output) -> None:
        handler = QueueLogHandler(self._queue)
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            graph = pm_core.merge_publications(sel, token, pw)
            pm_core.save_graph(graph, output)
            self._queue.put(("done", (len(graph), output)))
        except Exception as exc:  # noqa: BLE001 - alles netjes naar de GUI
            self._queue.put(("error", str(exc)))
        finally:
            root_logger.removeHandler(handler)

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._logmsg(payload)
                elif kind == "done":
                    n, output = payload
                    self._logmsg(f"Klaar: {n} triples opgeslagen in {output}")
                    self.status_var.set(f"Klaar — {n} triples.")
                    self._busy = False
                    self.run_btn.configure(state="normal")
                elif kind == "error":
                    self._logmsg("FOUT: " + payload)
                    self.status_var.set("Fout.")
                    self._busy = False
                    self.run_btn.configure(state="normal")
                    messagebox.showerror("Fout bij samenvoegen", payload)
        except queue.Empty:
            pass
        self.after(120, self._poll)


def main() -> None:
    root = tk.Tk()
    root.title("NLCS Publicatie-Merger")
    root.geometry("760x760")
    try:
        ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digigo.ico")
        if os.path.isfile(ico):
            root.iconbitmap(ico)
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
