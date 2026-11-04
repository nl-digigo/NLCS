"""Entrypoint: classificatie-RI changelog (blauwe C-familie) - genereert de
interactieve classificatie-pagina uit de export-CSV."""
import ot_gui

if __name__ == "__main__":
    ot_gui.run(mode="ri", title="Classificatie-RI — pagina",
               icon="C-blue.ico")
