#!/usr/bin/env bash
set -e

# Ajusta aquí a la versión del embebido:
PYTAG="${1:-cp310-cp310}"
PYBIN="/opt/python/${PYTAG}/bin"

rm -rf build
mkdir build
cd build

cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DPython3_EXECUTABLE="${PYBIN}/python"

cmake --build . -j

# Minimizar tamaño
strip --strip-unneeded ./*.so || true

# Test rápido import (dentro del contenedor)
"${PYBIN}/python" -c "import leq_levels_oct_weighting_C as m; print('import ok:', m)"
ls -lh ./*.so
