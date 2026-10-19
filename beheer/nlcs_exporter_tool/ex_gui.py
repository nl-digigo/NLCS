"""ex_gui.py - Tkinter-GUI voor de NLCS Exporter (nieuwe opzet).

Draait de 'publicatie'-queries rechtstreeks tegen een Laces SPARQL-endpoint en
schrijft <onderwerp>-<versie>.csv (objecten per hoofdgroep in objectentabellen/).
Login + endpoint + versielabel + repo-map (waar code/nlcs/publicatie staat) +
uitvoermap. Geen nlcs_exporter.py.
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import ex_core


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.pack(fill="both", expand=True)
        self._queue = queue.Queue()
        self._busy = False
        self._build()
        self.after(120, self._poll)

    def _build(self):
        ttk.Label(self, text="NLCS Exporter", font=("Segoe UI", 13, "bold")
                  ).pack(anchor="w")
        ttk.Label(self, foreground="#555",
                  text="Draait de 'publicatie'-queries rechtstreeks tegen het "
                       "SPARQL-endpoint en schrijft <onderwerp>-<versie>.csv "
                       "(objecten per hoofdgroep). Inloggegevens worden niet "
                       "opgeslagen.").pack(anchor="w", pady=(0, 10))

        login = ttk.LabelFrame(self, text="Inloggen (Laces BASIC-token)", padding=8)
        login.pack(fill="x")
        ttk.Label(login, text="Token-ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.token_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.token_var, width=52).grid(
            row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Label(login, text="Wachtwoord:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.pw_var = tk.StringVar()
        self.pw_entry = ttk.Entry(login, textvariable=self.pw_var, width=52, show="*")
        self.pw_entry.grid(row=1, column=1, sticky="we", padx=4, pady=3)
        self.show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(login, text="Toon", variable=self.show_pw,
                        command=self._toggle_pw).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        endf = ttk.LabelFrame(self, text="SPARQL-endpoint", padding=8)
        endf.pack(fill="x", pady=(8, 0))
        self.ep_var = tk.StringVar(value="")
        ttk.Entry(endf, textvariable=self.ep_var).pack(fill="x", padx=4)
        ttk.Label(endf, foreground="#777",
                  text="bijv. https://hub.laces.tech/…/nlcs-test/versions/5-2-2/sparql"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        verf = ttk.LabelFrame(self, text="Versielabel (in bestandsnamen)", padding=8)
        verf.pack(fill="x", pady=(8, 0))
        self.ver_var = tk.StringVar(value=ex_core.DEFAULT_VERSION)
        ttk.Entry(verf, textvariable=self.ver_var, width=12).pack(side="left", padx=4)
        ttk.Label(verf, foreground="#777",
                  text="bijv. 5-2 → symbolen-5-2.csv, objecten-AL-5-2.csv"
                  ).pack(side="left", padx=6)

        paths = ttk.LabelFrame(self, text="Mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.repo_var = tk.StringVar(value=ex_core.default_repo_root())
        self.out_var = tk.StringVar(value=ex_core.default_repo_root())
        self._path_row(paths, 0, "Repo-map (code/nlcs/publicatie):", self.repo_var)
        self._path_row(paths, 1, "Uitvoermap (CSV's):", self.out_var)
        paths.columnconfigure(1, weight=1)

        opts = ttk.LabelFrame(self, text="Wat draaien", padding=8)
        opts.pack(fill="x", pady=(8, 0))
        self.do_subjects = tk.BooleanVar(value=True)
        self.do_objects = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Onderwerp-tabellen (symbolen, arceringen, "
                        "lijntypes, bewerkingen, …)",
                        variable=self.do_subjects).pack(anchor="w")
        ttk.Checkbutton(opts, text="Objectentabellen per hoofdgroep "
                        "(objectentabellen/objecten-<HG>-<versie>.csv)",
                        variable=self.do_objects).pack(anchor="w")
        hgf = ttk.Frame(opts)
        hgf.pack(fill="x", pady=(4, 0))
        ttk.Label(hgf, text="Hoofdgroepen (leeg = alle):").pack(side="left", padx=(0, 6))
        self.hg_var = tk.StringVar(value="")
        ttk.Entry(hgf, textvariable=self.hg_var).pack(side="left", fill="x", expand=True)
        ttk.Label(opts, foreground="#777",
                  text="bijv. AL, VH, SB — gescheiden door komma of spatie"
                  ).pack(anchor="w", pady=(2, 0))

        linpat = ttk.LabelFrame(self, text="LIN/PAT-bestanden", padding=8)
        linpat.pack(fill="x", pady=(8, 0))
        self.do_lin = tk.BooleanVar(value=False)
        self.do_pat = tk.BooleanVar(value=False)
        ttk.Checkbutton(linpat, text="Lijntypes → .lin",
                        variable=self.do_lin).pack(anchor="w")
        ttk.Checkbutton(linpat, text="Arceringen → .pat (+ los per arcering in "
                        "arceringen/)", variable=self.do_pat).pack(anchor="w")
        ttk.Label(linpat, foreground="#777",
                  text="vereist een versioned endpoint (…/versions/<versie>/sparql). "
                       "Zet de tabel-vinkjes uit om alléén LIN/PAT te draaien."
                  ).pack(anchor="w", pady=(2, 0))

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(10, 4))
        self.run_btn = ttk.Button(actions, text="Exporteren", command=self.on_run)
        self.run_btn.pack(side="left")
        self.status_var = tk.StringVar(value="Klaar.")
        ttk.Label(actions, textvariable=self.status_var, foreground="#555"
                  ).pack(side="left", padx=10)

        logframe = ttk.LabelFrame(self, text="Voortgang", padding=6)
        logframe.pack(fill="both", expand=True)
        self.log = tk.Text(logframe, height=14, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        ls = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=ls.set)
        self.log.pack(side="left", fill="both", expand=True)
        ls.pack(side="right", fill="y")

    def _path_row(self, parent, row, label, var):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="we", padx=4, pady=3)
        ttk.Button(parent, text="Bladeren…",
                   command=lambda: self._browse_dir(var)).grid(row=row, column=2, padx=4)

    def _toggle_pw(self):
        self.pw_entry.configure(show="" if self.show_pw.get() else "*")

    def _browse_dir(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or os.getcwd())
        if d:
            var.set(d)

    def _logmsg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def on_run(self):
        if self._busy:
            return
        token = self.token_var.get().strip()
        pw = self.pw_var.get().strip()
        if not token or not pw:
            messagebox.showwarning("Inloggen", "Vul token-id én wachtwoord in.")
            return
        endpoint = self.ep_var.get().strip()
        if not endpoint:
            messagebox.showwarning("Endpoint", "Vul een SPARQL-endpoint in.")
            return
        repo = self.repo_var.get().strip()
        if not os.path.isdir(os.path.join(repo, "code", "nlcs", "publicatie")):
            if not messagebox.askyesno(
                    "Repo-map", "In de repo-map is geen 'code\\nlcs\\publicatie' "
                    "gevonden. Toch doorgaan?"):
                return
        out = self.out_var.get().strip() or repo
        version = self.ver_var.get().strip() or ex_core.DEFAULT_VERSION
        do_subjects = self.do_subjects.get()
        do_objects = self.do_objects.get()
        do_lin = self.do_lin.get()
        do_pat = self.do_pat.get()
        if not (do_subjects or do_objects or do_lin or do_pat):
            messagebox.showwarning(
                "Niets geselecteerd",
                "Vink minstens één onderdeel aan (tabellen en/of LIN/PAT).")
            return
        hg_raw = self.hg_var.get().strip()
        hg_filter = [h for h in __import__("re").split(r"[\s,]+", hg_raw) if h] \
            if hg_raw else None

        self._busy = True
        self.run_btn.configure(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status_var.set("Bezig…")
        threading.Thread(
            target=self._worker,
            args=(endpoint, token, pw, version, repo, out, do_subjects,
                  do_objects, hg_filter, do_lin, do_pat),
            daemon=True).start()

    def _worker(self, endpoint, token, pw, version, repo, out, do_subjects,
                do_objects, hg_filter, do_lin, do_pat):
        def log(msg=""):
            self._queue.put(("log", str(msg)))
        try:
            if do_subjects or do_objects:
                ex_core.run_export(endpoint, token, pw, version, repo, out,
                                   do_subjects=do_subjects, do_objects=do_objects,
                                   hoofdgroep_filter=hg_filter, log=log)
            if do_lin or do_pat:
                if do_subjects or do_objects:
                    log("")
                ex_core.generate_lin_pat(endpoint, token, pw, repo, out,
                                         do_lin=do_lin, do_pat=do_pat,
                                         version_fallback=version, log=log)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._logmsg(payload)
                elif kind == "done":
                    self.status_var.set("Klaar.")
                    self._set_idle()
                elif kind == "error":
                    self._logmsg("FOUT: " + payload)
                    self.status_var.set("Fout.")
                    self._set_idle()
                    messagebox.showerror("Fout", payload)
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def _set_idle(self):
        self._busy = False
        self.run_btn.configure(state="normal")


def main():
    root = tk.Tk()
    root.title("NLCS Exporter")
    root.geometry("820x760")
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(here, "groen.ico")
        if os.path.isfile(ico):
            root.iconbitmap(ico)
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
