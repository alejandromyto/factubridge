#!/bin/bash
# Script para ejecutar si cambian los xsd (app/infrastructure/aeat/xsd) oficiales.
# generate_models.sh - Genera modelos xsdata + establece enums a str,Enum para uso
# directo en models.
#

set -e

echo "🧹 Limpiando..."
rm -rf app/infrastructure/aeat/models/*

echo "⚙️  Generando..."
xsdata generate app/infrastructure/aeat/xsd # este comando usa .xsdata.xml


echo "🔧 Post-procesando..."
python3 fix_enums.py # script postprocesado para hacer que los Enum hereden de str

echo "📁 ls -la:"
ls -la app/infrastructure/aeat/models/ | head -10
