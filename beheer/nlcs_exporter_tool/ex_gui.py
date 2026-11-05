"""ex_gui.py - Tkinter-GUI voor de NLCS Exporter (nieuwe opzet).

Twee tabbladen met een gedeeld logvenster:
  * 'NLCS-publicatie': draait de 'publicatie'-queries rechtstreeks tegen een
    Laces SPARQL-endpoint en schrijft <onderwerp>-<versie>.csv (objecten per
    hoofdgroep in objectentabellen/), plus optioneel LIN/PAT.
  * 'BGT-mapping': draait de BGT->NLCS mapping-query (code/bgt-nlcs/
    queryNLCS_BGT.rq) tegen een APART endpoint met EIGEN credentials en een vrij
    in te vullen NLCS named graph; schrijft NLCS-<versie>-BGT.csv.
Inloggegevens worden niet opgeslagen.
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import ex_core


class App(ttk.Frame):
    # mode bepaalt welke tabbladen zichtbaar zijn:
    #   "nlcs"    -> alleen NLCS-publicatie
    #   "mapping" -> BGT-mapping, GWSW-mapping, GWSW (classificatie-RI), Classificatie
    #   "all"     -> alles (ontwikkel/standaard)
    def __init__(self, master, mode="all"):
        super().__init__(master, padding=12)
        self.mode = mode
        self.pack(fill="both", expand=True)
        self._queue = queue.Queue()
        self._busy = False
        self._run_buttons = []
        self._build()
        self.after(120, self._poll)

    def _build(self):
        titel = {"nlcs": "NLCS 5.0 Exporter",
                 "mapping": "Mapping Exporter — BGT · GWSW · classificatie-RI"}\
            .get(self.mode, "NLCS Exporter")
        ttk.Label(self, text=titel, font=("Segoe UI", 13, "bold")
                  ).pack(anchor="w")
        ttk.Label(self, foreground="#555",
                  text="Draait SPARQL-queries rechtstreeks tegen een Laces-endpoint "
                       "en schrijft CSV's. Inloggegevens worden niet opgeslagen."
                  ).pack(anchor="w", pady=(0, 8))

        nb = ttk.Notebook(self)
        nb.pack(fill="x")
        if self.mode in ("nlcs", "all"):
            tab_pub = ttk.Frame(nb, padding=8)
            nb.add(tab_pub, text="NLCS-publicatie")
            self._build_pub(tab_pub)
        if self.mode in ("mapping", "all"):
            tab_bgt = ttk.Frame(nb, padding=8)
            tab_gwsw = ttk.Frame(nb, padding=8)
            tab_gwsw_ri = ttk.Frame(nb, padding=8)
            tab_class = ttk.Frame(nb, padding=8)
            nb.add(tab_bgt, text="BGT-mapping")
            nb.add(tab_gwsw, text="GWSW-mapping")
            nb.add(tab_gwsw_ri, text="GWSW (classificatie-RI)")
            nb.add(tab_class, text="Classificatie (boom)")
            self._build_bgt(tab_bgt)
            self._build_gwsw(tab_gwsw)
            self._build_gwsw_ri(tab_gwsw_ri)
            self._build_class(tab_class)

        # Gedeelde statusregel + logvenster (onder de tabbladen).
        status = ttk.Frame(self)
        status.pack(fill="x", pady=(8, 4))
        self.status_var = tk.StringVar(value="Klaar.")
        ttk.Label(status, textvariable=self.status_var, foreground="#555"
                  ).pack(side="left")

        logframe = ttk.LabelFrame(self, text="Voortgang", padding=6)
        logframe.pack(fill="both", expand=True)
        self.log = tk.Text(logframe, height=14, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        ls = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=ls.set)
        self.log.pack(side="left", fill="both", expand=True)
        ls.pack(side="right", fill="y")

    # -- tab 1: NLCS-publicatie --------------------------------------------
    def _build_pub(self, parent):
        login = ttk.LabelFrame(parent, text="Inloggen (Laces BASIC-token)", padding=8)
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
                        command=lambda: self.pw_entry.configure(
                            show="" if self.show_pw.get() else "*")
                        ).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        endf = ttk.LabelFrame(parent, text="SPARQL-endpoint", padding=8)
        endf.pack(fill="x", pady=(8, 0))
        self.ep_var = tk.StringVar(value="")
        ttk.Entry(endf, textvariable=self.ep_var).pack(fill="x", padx=4)
        ttk.Label(endf, foreground="#777",
                  text="bijv. https://hub.laces.tech/…/nlcs-test/versions/5-2-2/sparql"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        verf = ttk.LabelFrame(parent, text="Versielabel (in bestandsnamen)", padding=8)
        verf.pack(fill="x", pady=(8, 0))
        self.ver_var = tk.StringVar(value=ex_core.DEFAULT_VERSION)
        ttk.Entry(verf, textvariable=self.ver_var, width=12).pack(side="left", padx=4)
        ttk.Label(verf, foreground="#777",
                  text="bijv. 5-2 → symbolen-5-2.csv, objecten-AL-5-2.csv"
                  ).pack(side="left", padx=6)

        paths = ttk.LabelFrame(parent, text="Mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.repo_var = tk.StringVar(value=ex_core.default_repo_root())
        self.out_var = tk.StringVar(value=ex_core.default_repo_root())
        self._path_row(paths, 0, "Repo-map (code/nlcs/publicatie):", self.repo_var)
        self._path_row(paths, 1, "Uitvoermap (CSV's):", self.out_var)
        paths.columnconfigure(1, weight=1)

        opts = ttk.LabelFrame(parent, text="Wat draaien", padding=8)
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

        linpat = ttk.LabelFrame(parent, text="LIN/PAT-bestanden", padding=8)
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

        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(10, 0))
        self.run_btn = ttk.Button(act, text="Exporteren", command=self.on_run)
        self.run_btn.pack(side="left")
        self._run_buttons.append(self.run_btn)

    # -- tab 2: BGT-mapping ------------------------------------------------
    def _build_bgt(self, parent):
        ttk.Label(parent, foreground="#555",
                  text="Draait de BGT→NLCS mapping-query tegen een APART endpoint "
                       "(andere dataset dan NLCS 5.2). De NLCS named graph is vrij "
                       "in te vullen. Uitvoer: NLCS-<versie>-BGT.csv."
                  ).pack(anchor="w", pady=(0, 6))

        login = ttk.LabelFrame(parent, text="Inloggen BGT (eigen Laces-token)", padding=8)
        login.pack(fill="x")
        ttk.Label(login, text="Token-ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.bgt_token_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.bgt_token_var, width=52).grid(
            row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Label(login, text="Wachtwoord:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.bgt_pw_var = tk.StringVar()
        self.bgt_pw_entry = ttk.Entry(login, textvariable=self.bgt_pw_var, width=52, show="*")
        self.bgt_pw_entry.grid(row=1, column=1, sticky="we", padx=4, pady=3)
        self.bgt_show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(login, text="Toon", variable=self.bgt_show_pw,
                        command=lambda: self.bgt_pw_entry.configure(
                            show="" if self.bgt_show_pw.get() else "*")
                        ).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        endf = ttk.LabelFrame(parent, text="BGT SPARQL-endpoint", padding=8)
        endf.pack(fill="x", pady=(8, 0))
        self.bgt_ep_var = tk.StringVar(value="")
        ttk.Entry(endf, textvariable=self.bgt_ep_var).pack(fill="x", padx=4)
        ttk.Label(endf, foreground="#777",
                  text="bijv. https://hub.laces.tech/…/nlcs-bgt/versions/5-0/sparql"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        graphf = ttk.LabelFrame(parent, text="NLCS named graph (vrij in te vullen)", padding=8)
        graphf.pack(fill="x", pady=(8, 0))
        self.bgt_graph_var = tk.StringVar(value=ex_core.DEFAULT_NLCS_GRAPH)
        ttk.Entry(graphf, textvariable=self.bgt_graph_var).pack(fill="x", padx=4)
        ttk.Label(graphf, foreground="#777",
                  text="vervangt de FROM NAMED / GRAPH-URI in de query "
                       "(de NLCS-versie waartegen de BGT-objecten worden gekoppeld)"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        verf = ttk.LabelFrame(parent, text="Versielabels (in bestandsnaam)", padding=8)
        verf.pack(fill="x", pady=(8, 0))
        ttk.Label(verf, text="NLCS:").pack(side="left")
        self.bgt_ver_var = tk.StringVar(value="5-0")
        ttk.Entry(verf, textvariable=self.bgt_ver_var, width=10).pack(side="left", padx=4)
        ttk.Label(verf, text="BGT:").pack(side="left", padx=(12, 0))
        self.bgt_std_var = tk.StringVar(value="")
        ttk.Entry(verf, textvariable=self.bgt_std_var, width=10).pack(side="left", padx=4)
        ttk.Label(verf, foreground="#777",
                  text="bijv. NLCS 5-0 + BGT 1-2 → NLCS-5-0-BGT-1-2.csv (BGT leeg = weglaten)"
                  ).pack(side="left", padx=6)

        paths = ttk.LabelFrame(parent, text="Bestanden/mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.bgt_query_var = tk.StringVar(value="")
        self.bgt_out_var = tk.StringVar(value="")
        ttk.Label(paths, text="BGT-query (.rq):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(paths, textvariable=self.bgt_query_var).grid(row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Button(paths, text="Bladeren…",
                   command=self._browse_query).grid(row=0, column=2, padx=4)
        self._path_row(paths, 1, "Uitvoermap (mappingen):", self.bgt_out_var)
        ttk.Label(paths, foreground="#777",
                  text="query bijv. …/NLCSacc/code/bgt-nlcs/queryNLCS_BGT.rq; "
                       "uitvoer bijv. …/tabellen/publicatie/mappingen/5.0"
                  ).grid(row=2, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 0))
        paths.columnconfigure(1, weight=1)

        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(10, 0))
        self.bgt_run_btn = ttk.Button(act, text="Exporteer BGT-mapping",
                                      command=self.on_run_bgt)
        self.bgt_run_btn.pack(side="left")
        self._run_buttons.append(self.bgt_run_btn)

    # -- tab 3: GWSW-mapping -----------------------------------------------
    def _build_gwsw(self, parent):
        ttk.Label(parent, foreground="#555",
                  text="Draait de GWSW→NLCS mapping-query tegen de publicatie "
                       "nlcs-gwsw. De NLCS-laagnaam/symbool + ID's komen uit de "
                       "NLCS-publicatie, die via default-graph-uri wordt "
                       "meegegeven. Uitvoer: NLCS-<versie>-GWSW.csv."
                  ).pack(anchor="w", pady=(0, 6))

        login = ttk.LabelFrame(parent, text="Inloggen GWSW (eigen Laces-token)", padding=8)
        login.pack(fill="x")
        ttk.Label(login, text="Token-ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.gwsw_token_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.gwsw_token_var, width=52).grid(
            row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Label(login, text="Wachtwoord:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.gwsw_pw_var = tk.StringVar()
        self.gwsw_pw_entry = ttk.Entry(login, textvariable=self.gwsw_pw_var, width=52, show="*")
        self.gwsw_pw_entry.grid(row=1, column=1, sticky="we", padx=4, pady=3)
        self.gwsw_show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(login, text="Toon", variable=self.gwsw_show_pw,
                        command=lambda: self.gwsw_pw_entry.configure(
                            show="" if self.gwsw_show_pw.get() else "*")
                        ).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        endf = ttk.LabelFrame(parent, text="GWSW SPARQL-endpoint", padding=8)
        endf.pack(fill="x", pady=(8, 0))
        self.gwsw_ep_var = tk.StringVar(value="")
        ttk.Entry(endf, textvariable=self.gwsw_ep_var).pack(fill="x", padx=4)
        ttk.Label(endf, foreground="#777",
                  text="bijv. https://hub.laces.tech/…/test/nlcs-gwsw/"
                       "versions/5_0_1/sparql"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        graphf = ttk.LabelFrame(parent, text="NLCS named graph (default-graph-uri)", padding=8)
        graphf.pack(fill="x", pady=(8, 0))
        self.gwsw_graph_var = tk.StringVar(value=ex_core.DEFAULT_NLCS_GRAPH)
        ttk.Entry(graphf, textvariable=self.gwsw_graph_var).pack(fill="x", padx=4)
        ttk.Label(graphf, foreground="#777",
                  text="wordt als ?default-graph-uri aan het endpoint gehangen "
                       "(nodig voor de NLCS-namen van object/symbool)"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        verf = ttk.LabelFrame(parent, text="Versielabels (in bestandsnaam)", padding=8)
        verf.pack(fill="x", pady=(8, 0))
        ttk.Label(verf, text="NLCS:").pack(side="left")
        self.gwsw_ver_var = tk.StringVar(value="5-0")
        ttk.Entry(verf, textvariable=self.gwsw_ver_var, width=10).pack(side="left", padx=4)
        ttk.Label(verf, text="GWSW:").pack(side="left", padx=(12, 0))
        self.gwsw_std_var = tk.StringVar(value="")
        ttk.Entry(verf, textvariable=self.gwsw_std_var, width=10).pack(side="left", padx=4)
        ttk.Label(verf, foreground="#777",
                  text="bijv. NLCS 5-0 + GWSW 1-7 → NLCS-5-0-GWSW-1-7.csv (GWSW leeg = weglaten)"
                  ).pack(side="left", padx=6)

        paths = ttk.LabelFrame(parent, text="Bestanden/mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.gwsw_query_var = tk.StringVar(value=ex_core.default_gwsw_query())
        self.gwsw_out_var = tk.StringVar(value="")
        ttk.Label(paths, text="GWSW-query (.rq):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(paths, textvariable=self.gwsw_query_var).grid(row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Button(paths, text="Bladeren…",
                   command=lambda: self._browse_query_var(self.gwsw_query_var)
                   ).grid(row=0, column=2, padx=4)
        self._path_row(paths, 1, "Uitvoermap (mappingen):", self.gwsw_out_var)
        ttk.Label(paths, foreground="#777",
                  text="query standaard: code/gwsw-nlcs/GWSW-NLCS mapping tabel met "
                       "NLCS-ID.rq; uitvoer bijv. …/tabellen/publicatie/mappingen/5.0"
                  ).grid(row=2, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 0))
        paths.columnconfigure(1, weight=1)

        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(10, 0))
        self.gwsw_run_btn = ttk.Button(act, text="Exporteer GWSW-mapping",
                                       command=self.on_run_gwsw)
        self.gwsw_run_btn.pack(side="left")
        self._run_buttons.append(self.gwsw_run_btn)

    # -- tab 4: GWSW via classificatie-RI (met overerving) -----------------
    def _build_gwsw_ri(self, parent):
        ttk.Label(parent, foreground="#555",
                  text="Draait de GWSW→NLCS mapping-query tegen de publicatie "
                       "nlcs-classificatie-ri---kern, MET overerving: een GWSW-"
                       "koppeling op een hoger concept werkt door naar alle "
                       "onderliggende objecten. Alleen objecten mét een NLCS 5.0-"
                       "relatie. Uitvoer: NLCS-<versie>-GWSW-RI.csv."
                  ).pack(anchor="w", pady=(0, 6))

        login = ttk.LabelFrame(parent, text="Inloggen (eigen Laces-token)", padding=8)
        login.pack(fill="x")
        ttk.Label(login, text="Token-ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.gri_token_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.gri_token_var, width=52).grid(
            row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Label(login, text="Wachtwoord:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.gri_pw_var = tk.StringVar()
        self.gri_pw_entry = ttk.Entry(login, textvariable=self.gri_pw_var, width=52, show="*")
        self.gri_pw_entry.grid(row=1, column=1, sticky="we", padx=4, pady=3)
        self.gri_show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(login, text="Toon", variable=self.gri_show_pw,
                        command=lambda: self.gri_pw_entry.configure(
                            show="" if self.gri_show_pw.get() else "*")
                        ).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        endf = ttk.LabelFrame(parent, text="Classificatie SPARQL-endpoint", padding=8)
        endf.pack(fill="x", pady=(8, 0))
        self.gri_ep_var = tk.StringVar(value="")
        ttk.Entry(endf, textvariable=self.gri_ep_var).pack(fill="x", padx=4)
        ttk.Label(endf, foreground="#777",
                  text="bijv. https://hub.laces.tech/…/test/nlcs-classificatie-ri---kern/"
                       "versions/v0_0_5/sparql"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        graphf = ttk.LabelFrame(parent, text="NLCS named graph (default-graph-uri)", padding=8)
        graphf.pack(fill="x", pady=(8, 0))
        self.gri_graph_var = tk.StringVar(value=ex_core.DEFAULT_NLCS_GRAPH)
        ttk.Entry(graphf, textvariable=self.gri_graph_var).pack(fill="x", padx=4)
        ttk.Label(graphf, foreground="#777",
                  text="wordt als ?default-graph-uri meegegeven (voor NLCS-namen + ID's)"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        verf = ttk.LabelFrame(parent, text="Versielabels (in bestandsnaam)", padding=8)
        verf.pack(fill="x", pady=(8, 0))
        ttk.Label(verf, text="NLCS:").pack(side="left")
        self.gri_ver_var = tk.StringVar(value="5-0")
        ttk.Entry(verf, textvariable=self.gri_ver_var, width=10).pack(side="left", padx=4)
        ttk.Label(verf, text="GWSW:").pack(side="left", padx=(12, 0))
        self.gri_std_var = tk.StringVar(value="")
        ttk.Entry(verf, textvariable=self.gri_std_var, width=10).pack(side="left", padx=4)
        ttk.Label(verf, foreground="#777",
                  text="bijv. NLCS 5-0 + GWSW 1-7 → NLCS-5-0-GWSW-RI-1-7.csv (GWSW leeg = weglaten)"
                  ).pack(side="left", padx=6)

        paths = ttk.LabelFrame(parent, text="Bestanden/mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.gri_query_var = tk.StringVar(value=ex_core.default_gwsw_ri_query())
        self.gri_out_var = tk.StringVar(value="")
        ttk.Label(paths, text="Query (.rq):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(paths, textvariable=self.gri_query_var).grid(row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Button(paths, text="Bladeren…",
                   command=lambda: self._browse_query_var(self.gri_query_var)
                   ).grid(row=0, column=2, padx=4)
        self._path_row(paths, 1, "Uitvoermap (mappingen):", self.gri_out_var)
        ttk.Label(paths, foreground="#777",
                  text="query standaard: code/gwsw-nlcs/GWSW-NLCS mapping via "
                       "classificatie-RI (overerving).rq"
                  ).grid(row=2, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 0))
        paths.columnconfigure(1, weight=1)

        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(10, 0))
        self.gri_run_btn = ttk.Button(act, text="Exporteer GWSW-mapping (classificatie-RI)",
                                      command=self.on_run_gwsw_ri)
        self.gri_run_btn.pack(side="left")
        self._run_buttons.append(self.gri_run_btn)

    # -- tab 5: Classificatie-export (boom + relaties) ---------------------
    def _build_class(self, parent):
        ttk.Label(parent, foreground="#555",
                  text="Exporteert de volledige classificatie-objectboom (subtype-"
                       "of) met per object de relaties: GWSW-type(s), NLCS-objectlaag "
                       "+ ID en één gekozen symbool. Voeding voor de classificatie-"
                       "pagina. Uitvoer: NLCS-<versie>-classificatie.csv."
                  ).pack(anchor="w", pady=(0, 6))

        login = ttk.LabelFrame(parent, text="Inloggen (eigen Laces-token)", padding=8)
        login.pack(fill="x")
        ttk.Label(login, text="Token-ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.cl_token_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.cl_token_var, width=52).grid(
            row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Label(login, text="Wachtwoord:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.cl_pw_var = tk.StringVar()
        self.cl_pw_entry = ttk.Entry(login, textvariable=self.cl_pw_var, width=52, show="*")
        self.cl_pw_entry.grid(row=1, column=1, sticky="we", padx=4, pady=3)
        self.cl_show_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(login, text="Toon", variable=self.cl_show_pw,
                        command=lambda: self.cl_pw_entry.configure(
                            show="" if self.cl_show_pw.get() else "*")
                        ).grid(row=1, column=2, padx=4)
        login.columnconfigure(1, weight=1)

        endf = ttk.LabelFrame(parent, text="Classificatie SPARQL-endpoint", padding=8)
        endf.pack(fill="x", pady=(8, 0))
        self.cl_ep_var = tk.StringVar(value="")
        ttk.Entry(endf, textvariable=self.cl_ep_var).pack(fill="x", padx=4)
        ttk.Label(endf, foreground="#777",
                  text="bijv. https://hub.laces.tech/…/test/nlcs-classificatie-ri---kern/"
                       "versions/v0_0_5/sparql"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        graphf = ttk.LabelFrame(parent, text="NLCS named graph (default-graph-uri)", padding=8)
        graphf.pack(fill="x", pady=(8, 0))
        self.cl_graph_var = tk.StringVar(value=ex_core.DEFAULT_NLCS_GRAPH)
        ttk.Entry(graphf, textvariable=self.cl_graph_var).pack(fill="x", padx=4)
        ttk.Label(graphf, foreground="#777",
                  text="voor NLCS-namen, ID's en symbolen"
                  ).pack(anchor="w", padx=4, pady=(2, 0))

        verf = ttk.LabelFrame(parent, text="Versielabel (in bestandsnaam)", padding=8)
        verf.pack(fill="x", pady=(8, 0))
        self.cl_ver_var = tk.StringVar(value="5-0")
        ttk.Entry(verf, textvariable=self.cl_ver_var, width=12).pack(side="left", padx=4)
        ttk.Label(verf, foreground="#777",
                  text="bijv. 5-0 → NLCS-5-0-classificatie.csv").pack(side="left", padx=6)

        paths = ttk.LabelFrame(parent, text="Bestanden/mappen", padding=8)
        paths.pack(fill="x", pady=(8, 0))
        self.cl_query_var = tk.StringVar(value=ex_core.default_classificatie_query())
        self.cl_out_var = tk.StringVar(value="")
        ttk.Label(paths, text="Query (.rq):").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(paths, textvariable=self.cl_query_var).grid(row=0, column=1, sticky="we", padx=4, pady=3)
        ttk.Button(paths, text="Bladeren…",
                   command=lambda: self._browse_query_var(self.cl_query_var)
                   ).grid(row=0, column=2, padx=4)
        self._path_row(paths, 1, "Uitvoermap:", self.cl_out_var)
        ttk.Label(paths, foreground="#777",
                  text="query standaard: code/gwsw-nlcs/classificatie-export.rq"
                  ).grid(row=2, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 0))
        paths.columnconfigure(1, weight=1)

        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(10, 0))
        self.cl_run_btn = ttk.Button(act, text="Exporteer classificatie",
                                     command=self.on_run_class)
        self.cl_run_btn.pack(side="left")
        self._run_buttons.append(self.cl_run_btn)

    # -- gedeelde helpers --------------------------------------------------
    def _path_row(self, parent, row, label, var):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="we", padx=4, pady=3)
        ttk.Button(parent, text="Bladeren…",
                   command=lambda: self._browse_dir(var)).grid(row=row, column=2, padx=4)

    def _browse_dir(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or os.getcwd())
        if d:
            var.set(d)

    def _browse_query(self):
        self._browse_query_var(self.bgt_query_var)

    def _browse_query_var(self, var):
        init = os.path.dirname(var.get()) or os.getcwd()
        f = filedialog.askopenfilename(
            initialdir=init, title="Kies de query (.rq)",
            filetypes=[("SPARQL-query", "*.rq"), ("Alle bestanden", "*.*")])
        if f:
            var.set(f)

    def _logmsg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _start(self, worker, args):
        self._busy = True
        for b in self._run_buttons:
            b.configure(state="disabled")
        self._clear_log()
        self.status_var.set("Bezig…")
        threading.Thread(target=worker, args=args, daemon=True).start()

    # -- tab 1: draaien ----------------------------------------------------
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
        self._start(self._worker,
                    (endpoint, token, pw, version, repo, out, do_subjects,
                     do_objects, hg_filter, do_lin, do_pat))

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

    # -- tab 2: draaien ----------------------------------------------------
    def on_run_bgt(self):
        if self._busy:
            return
        token = self.bgt_token_var.get().strip()
        pw = self.bgt_pw_var.get().strip()
        if not token or not pw:
            messagebox.showwarning("Inloggen", "Vul token-id én wachtwoord in "
                                   "voor de BGT-publicatie.")
            return
        endpoint = self.bgt_ep_var.get().strip()
        if not endpoint:
            messagebox.showwarning("Endpoint", "Vul het BGT SPARQL-endpoint in.")
            return
        query = self.bgt_query_var.get().strip()
        if not os.path.isfile(query):
            messagebox.showwarning("BGT-query", "Kies het .rq-bestand met de "
                                   "BGT-query (queryNLCS_BGT.rq).")
            return
        out = self.bgt_out_var.get().strip()
        if not out:
            messagebox.showwarning("Uitvoermap", "Kies een uitvoermap voor de "
                                   "mapping-CSV.")
            return
        graph = self.bgt_graph_var.get().strip() or ex_core.DEFAULT_NLCS_GRAPH
        version = self.bgt_ver_var.get().strip() or "5-0"
        std = self.bgt_std_var.get().strip()
        self._start(self._worker_bgt,
                    (endpoint, token, pw, graph, version, query, out, std))

    def _worker_bgt(self, endpoint, token, pw, graph, version, query, out, std):
        def log(msg=""):
            self._queue.put(("log", str(msg)))
        try:
            ex_core.run_bgt_mapping_export(endpoint, token, pw, graph, version,
                                           query, out, std_version=std, log=log)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    # -- tab 3: draaien ----------------------------------------------------
    def on_run_gwsw(self):
        if self._busy:
            return
        token = self.gwsw_token_var.get().strip()
        pw = self.gwsw_pw_var.get().strip()
        if not token or not pw:
            messagebox.showwarning("Inloggen", "Vul token-id én wachtwoord in "
                                   "voor de GWSW-publicatie.")
            return
        endpoint = self.gwsw_ep_var.get().strip()
        if not endpoint:
            messagebox.showwarning("Endpoint", "Vul het GWSW SPARQL-endpoint in.")
            return
        query = self.gwsw_query_var.get().strip()
        if not os.path.isfile(query):
            messagebox.showwarning("GWSW-query", "Kies het .rq-bestand met de "
                                   "GWSW-mapping-query.")
            return
        out = self.gwsw_out_var.get().strip()
        if not out:
            messagebox.showwarning("Uitvoermap", "Kies een uitvoermap voor de "
                                   "mapping-CSV.")
            return
        graph = self.gwsw_graph_var.get().strip() or ex_core.DEFAULT_NLCS_GRAPH
        version = self.gwsw_ver_var.get().strip() or "5-0"
        std = self.gwsw_std_var.get().strip()
        self._start(self._worker_gwsw,
                    (endpoint, token, pw, graph, version, query, out, std))

    def _worker_gwsw(self, endpoint, token, pw, graph, version, query, out, std):
        def log(msg=""):
            self._queue.put(("log", str(msg)))
        try:
            ex_core.run_gwsw_mapping_export(endpoint, token, pw, graph, version,
                                            query, out, std_version=std, log=log)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    # -- tab 4: draaien ----------------------------------------------------
    def on_run_gwsw_ri(self):
        if self._busy:
            return
        token = self.gri_token_var.get().strip()
        pw = self.gri_pw_var.get().strip()
        if not token or not pw:
            messagebox.showwarning("Inloggen", "Vul token-id én wachtwoord in.")
            return
        endpoint = self.gri_ep_var.get().strip()
        if not endpoint:
            messagebox.showwarning("Endpoint", "Vul het classificatie SPARQL-"
                                   "endpoint in.")
            return
        query = self.gri_query_var.get().strip()
        if not os.path.isfile(query):
            messagebox.showwarning("Query", "Kies het .rq-bestand met de "
                                   "classificatie-RI mapping-query.")
            return
        out = self.gri_out_var.get().strip()
        if not out:
            messagebox.showwarning("Uitvoermap", "Kies een uitvoermap.")
            return
        graph = self.gri_graph_var.get().strip() or ex_core.DEFAULT_NLCS_GRAPH
        version = self.gri_ver_var.get().strip() or "5-0"
        std = self.gri_std_var.get().strip()
        self._start(self._worker_gwsw_ri,
                    (endpoint, token, pw, graph, version, query, out, std))

    def _worker_gwsw_ri(self, endpoint, token, pw, graph, version, query, out, std):
        def log(msg=""):
            self._queue.put(("log", str(msg)))
        try:
            ex_core.run_gwsw_ri_mapping_export(endpoint, token, pw, graph,
                                               version, query, out,
                                               out_name="GWSW-RI",
                                               std_version=std, log=log)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    # -- tab 5: draaien ----------------------------------------------------
    def on_run_class(self):
        if self._busy:
            return
        token = self.cl_token_var.get().strip()
        pw = self.cl_pw_var.get().strip()
        if not token or not pw:
            messagebox.showwarning("Inloggen", "Vul token-id én wachtwoord in.")
            return
        endpoint = self.cl_ep_var.get().strip()
        if not endpoint:
            messagebox.showwarning("Endpoint", "Vul het classificatie SPARQL-"
                                   "endpoint in.")
            return
        query = self.cl_query_var.get().strip()
        if not os.path.isfile(query):
            messagebox.showwarning("Query", "Kies het .rq-bestand met de "
                                   "classificatie-export-query.")
            return
        out = self.cl_out_var.get().strip()
        if not out:
            messagebox.showwarning("Uitvoermap", "Kies een uitvoermap.")
            return
        graph = self.cl_graph_var.get().strip() or ex_core.DEFAULT_NLCS_GRAPH
        version = self.cl_ver_var.get().strip() or "5-0"
        self._start(self._worker_class,
                    (endpoint, token, pw, graph, version, query, out))

    def _worker_class(self, endpoint, token, pw, graph, version, query, out):
        def log(msg=""):
            self._queue.put(("log", str(msg)))
        try:
            ex_core.run_classificatie_export(endpoint, token, pw, graph,
                                             version, query, out, log=log)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    # -- poll --------------------------------------------------------------
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
        for b in self._run_buttons:
            b.configure(state="normal")


def main(mode="all", title="NLCS Exporter", icon="groen.ico"):
    root = tk.Tk()
    root.title(title)
    root.geometry("860x820")
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(here, icon)
        if os.path.isfile(ico):
            root.iconbitmap(ico)
    except Exception:
        pass
    App(root, mode=mode)
    root.mainloop()


if __name__ == "__main__":
    main()
