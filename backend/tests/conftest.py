"""Configuración común de las pruebas.

Las pruebas unitarias y de API usan los repositorios en memoria. Debe
definirse antes de importar la aplicación, porque los proveedores eligen el
repositorio al importarse.
"""

import os

os.environ["TAIA_STORAGE"] = "memory"
