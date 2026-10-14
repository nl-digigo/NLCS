"""ex_gui.py - Tkinter-GUI voor de NLCS Exporter.

Login (Laces token-id + wachtwoord; NIET opgeslagen), een instelbaar SPARQL-
endpoint, een REPO-map (waar ./code/nlcs/... staat) en een UITVOER-map (waar
tabellen/ en html/ komen), plus aanvinkbare stappen. De logica komt uit
nlcs_exporter.py (via ex_core); dat bestand wordt niet aangepast.
"""
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import ex_core


class _QueueWriter:
    """Vangt print()-uitvoer op en stuurt per regel naar de GUI-queue."""

    def __init__(self, q):
        self.q = q
        self._buf = ""

    def write(self, s):
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self.q.put(("log", line))

    def flush(self):
        if self._buf:
            self.q.put(("log", self._buf))
            self._buf = ""


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.pack(fill="both", expand=True)
        self._queue = queue.Queue()
        self._busy = False
        self.step_vars = {}
        self._build()
        self.after(120, self._poll)

    def _build(self):
        ttk.Label(self, text="NLCS Exporter", font=("Segoe UI", 13, "bold")
                  ).pack(anchor="w")
        ttk.Label(self, foreground="#555",
                  text="Log in met je Laces token-id + wachtwoord, kies het "
                       "SPARQL-endpoint, de repo-map en de uitvoermap, vink de "
                       "stappen aan en klik 'Exporteren'. Inloggegevens worden "
                       "niet opgeslagen.").pack(anchor="w", pady=(0, 10))

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
        self.ep_var = tk.StringVar(value=ex_core.DEFAULT_ENDPOINT)
        ttk.Entry(endf, textvariable=self.ep_var).pack(fill="x", padx=4)

        paths = ttk.LabelFrame(self, text="Mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.repo_var = tk.StringVar(value=ex_core.default_repo_root())
        self.out_var = tk.StringVar(value=ex_core.default_repo_root())
        self._path_row(paths, 0, "Repo-map (queries):", self.repo_var)
        self._path_row(paths, 1, "Uitvoermap (export):", self.out_var)
        paths.columnconfigure(1, weight=1)

        steps = ttk.LabelFrame(self, text="Stappen", padding=8)
        steps.pack(fill="x", pady=(8, 0))
        for key, label in ex_core.STEPS:
            v = tk.BooleanVar(value=True)
            self.step_vars[key] = v
            ttk.Checkbutton(steps, text=label, variable=v).pack(anchor="w")

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
        if not os.path.isdir(os.path.join(repo, "code", "nlcs")):
            if not messagebox.askyesno(
                    "Repo-map",
                    "In de repo-map is geen 'code\\nlcs' gevonden. De queries "
                    "worden daaruit gelezen. Toch doorgaan?"):
                return
        out = self.out_var.get().strip() or repo
        steps = {k: v.get() for k, v in self.step_vars.items()}
        if not any(steps.values()):
            messagebox.showwarning("Stappen", "Vink minstens één stap aan.")
            return

        self._busy = True
        self.run_btn.configure(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status_var.set("Bezig…")
        t = threading.Thread(target=self._worker,
                             args=(endpoint, token, pw, steps, repo, out),
                             daemon=True)
        t.start()

    def _worker(self, endpoint, token, pw, steps, repo, out):
        old_out, old_err = sys.stdout, sys.stderr
        writer = _QueueWriter(self._queue)
        sys.stdout = writer
        sys.stderr = writer
        try:
            ex_core.run_export(endpoint, token, pw, steps, repo, out)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))
        finally:
            writer.flush()
            sys.stdout, sys.stderr = old_out, old_err

    def _poll(self):
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._logmsg(payload)
                elif kind == "done":
                    self.status_var.set("Klaar.")
                    self._busy = False
                    self.run_btn.configure(state="normal")
                elif kind == "error":
                    self._logmsg("FOUT: " + payload)
                    self.status_var.set("Fout.")
                    self._busy = False
                    self.run_btn.configure(state="normal")
                    messagebox.showerror("Fout bij exporteren", payload)
        except queue.Empty:
            pass
        self.after(120, self._poll)


def main():
    root = tk.Tk()
    root.title("NLCS Exporter")
    root.geometry("780x720")
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("groen.ico",):
            ico = os.path.join(here, name)
            if os.path.isfile(ico):
                root.iconbitmap(ico)
                break
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
