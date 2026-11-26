#!/bin/sh
# verify.sh -- re-verifica una cadena de recibos con shasum y jq.
#
#   ./verify.sh [-d DIR] RECIBO [RECIBO ...]
#
# No importa nada de este repositorio: lee los recibos, pasa shasum sobre los
# artefactos que encuentre bajo DIR, suma en awk y publica una linea por acto,
# una por costura y una por el compuesto. Sirve para que un auditor de cliente
# confirme un certificado sin instalar la suite.
#
# Verifica tres cosas por acto y dos por costura:
#
#   acto     dominio == suma(cubetas)              la ecuacion cierra
#   acto     rc declarado                          lo que el productor afirma
#   artefacto sha256(fichero) == sha256_archivo    el fichero es el certificado
#   artefacto lineas - 1 == claves                 el fichero es la imagen entera
#   costura  imagen(i) == dominio(i+1)             cuenta
#   costura  artefacto(i) == entrada(i+1)          bytes
#
# y compone con los mismos numeros que la ley: restos = suma de lo que no es
# imagen, residuo = dominio(1) - (imagen(n) + restos).
#
# RC 0 conservado · 1 hay una colision declarada · 2 algo no se pudo mirar ·
# 4 una costura rota o una ecuacion que no cierra. Precedencia 4 > 1 > 2 > 0.
#
# Necesita: sh (POSIX), jq, y shasum o sha256sum.
set -eu

DIR=""
if [ "${1:-}" = "-d" ]; then
    DIR="${2:?verify.sh: -d exige un directorio}"
    shift 2
fi
if [ "$#" -lt 2 ]; then
    echo "verify.sh: una cadena exige al menos dos actos" >&2
    exit 2
fi

if command -v shasum >/dev/null 2>&1; then
    DESTAJO="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
    DESTAJO="sha256sum"
else
    echo "verify.sh: falta shasum o sha256sum" >&2
    exit 2
fi

roto=0
colision=0
ciego=0

n=0
dominio1=""
imagen_n=""
restos=0
residuo_enlaces=0
prev_img=""
prev_arch=""
prev_sha=""
prev_nombre=""

for r in "$@"; do
    n=$((n + 1))
    nombre=$(basename "$r")

    dom=$(jq -r '.ecuacion.dominio // .entrada.filas // empty' "$r")
    suma=$(jq -r '[.cubetas[]] | add // empty' "$r")
    img=$(jq -r '.cubetas.imagen // empty' "$r")
    declarado=$(jq -r '.rc // empty' "$r")

    if [ -z "$dom" ] || [ -z "$suma" ]; then
        echo "ACTO $n $nombre NO_MEDIDO (el recibo no publica dominio o cubetas)"
        ciego=1
        prev_img=""
        prev_sha=""
        prev_nombre=$nombre
        continue
    fi

    if [ "$dom" = "$suma" ]; then
        estado=ok
    else
        estado="!"
        roto=1
    fi
    echo "ACTO $n $nombre $dom = $suma $estado declarado=${declarado:-?}"

    case "${declarado:-0}" in
        4) roto=1 ;;
        1) colision=1 ;;
        2) ciego=1 ;;
    esac

    # -- el artefacto: el fichero que viaja y el digest que lo certifica -------
    arch=$(jq -r '.salida.archivo // empty' "$r")
    sha=$(jq -r '.salida.sha256_archivo // empty' "$r")
    claves=$(jq -r '.salida.claves // empty' "$r")
    if [ -n "$arch" ] && [ -n "$sha" ]; then
        if [ -n "$DIR" ] && [ -f "$DIR/$arch" ]; then
            real=$($DESTAJO "$DIR/$arch" | awk '{print $1}')
            lineas=$(wc -l <"$DIR/$arch" | tr -d ' ')
            if [ "$real" = "$sha" ]; then
                bytes_ok=ok
            else
                bytes_ok="!"
                roto=1
            fi
            if [ -n "$claves" ] && [ "$lineas" -eq $((claves + 1)) ]; then
                filas_ok="ok ($claves + cabecera)"
            else
                filas_ok="!"
                roto=1
            fi
            echo "ARTEFACTO $arch sha256 $bytes_ok filas $lineas $filas_ok"
        else
            echo "ARTEFACTO $arch NO_MEDIDO (no esta bajo ${DIR:-.}; solo se verifican los digests declarados)"
            ciego=1
        fi
    elif [ -n "$arch" ]; then
        echo "ARTEFACTO $arch NO_MEDIDO (el recibo no digiere el fichero que escribio)"
        ciego=1
    fi

    # -- la costura: dos medidas que responden preguntas distintas -------------
    entrada_sha=$(jq -r '.entrada.sha256 // empty' "$r")
    if [ "$n" -gt 1 ]; then
        if [ -n "$prev_img" ] && [ "$prev_img" = "$dom" ]; then
            cuenta=ok
        else
            cuenta="!"
            roto=1
        fi
        if [ -n "$prev_sha" ] && [ -n "$entrada_sha" ]; then
            if [ "$prev_sha" = "$entrada_sha" ]; then
                bytes=ok
            else
                bytes="!"
                roto=1
            fi
        else
            bytes="?"
            ciego=1
        fi
        echo "COSTURA $((n - 1))->$n $prev_nombre -> $nombre filas ${prev_img:-?} -> $dom $cuenta bytes $bytes"
    fi

    [ -z "$dominio1" ] && dominio1=$dom
    restos=$((restos + suma - ${img:-0}))
    residuo_enlaces=$((residuo_enlaces + dom - suma))
    imagen_n=${img:-}
    prev_img=$img
    prev_arch=$arch
    prev_sha=$sha
    prev_nombre=$nombre
done

# -- el compuesto: el telescopio, con los numeros de arriba -------------------
if [ -z "$dominio1" ] || [ -z "$imagen_n" ]; then
    echo "COMPUESTO NO_MEDIDO (falta el dominio del primer acto o la imagen del ultimo)"
    exit 2
fi

residuo=$((dominio1 - (imagen_n + restos)))
if [ "$residuo" -eq 0 ]; then
    res_estado=ok
else
    res_estado="!"
    roto=1
fi
if [ "$residuo" -eq "$residuo_enlaces" ]; then
    tele=si
else
    tele=NO
    roto=1
fi
echo "COMPUESTO $dominio1 = $imagen_n + $restos residuo $residuo $res_estado telescopia $tele"

if [ "$roto" -eq 1 ]; then
    exit 4
elif [ "$colision" -eq 1 ]; then
    exit 1
elif [ "$ciego" -eq 1 ]; then
    exit 2
fi
exit 0
