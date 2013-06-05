#!/usr/bin/env python

import datetime
import json
import logging
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.db.models import ObjectDoesNotExist
from django.db.models import Q
from django.db import transaction, connection

import core.models as models

logger = logging.getLogger(__name__)

# import pdb; pdb.set_trace()

def to_compra_entity(c):
    # {
    #     "proveedor": "GRUPO NUCLEO S.A.",
    #     "fecha": "2011-07-06",
    #     "destino": "Procuraci\u00f3n Municipal",
    #     "tipo_compra": "CONC",
    #     "orden_compra": "1225",
    #     "observaciones": "Expte. 4570, Dig. 8",
    #     "importe": 6522.0
    # }
    proveedor, proveedor_created = \
            models.Proveedor.objects.get_or_create(nombre=c['proveedor'])
    reparticion, reparticion_created = \
            models.Reparticion.objects.get_or_create(nombre=c['destino'])
    to_datetime = lambda s: datetime.datetime(*map(int, s.split('-')))

    return models.Compra(orden_compra=int(c['orden_compra']),
                           importe=str(c['importe']),
                           fecha=to_datetime(c['fecha']),
                           proveedor=proveedor,
                           destino=reparticion)

def to_compralinea_entity(cl):
    # {
    #    "importe_total": 840.0,
    #    "cantidad": "4",
    #    "unidad_medida": "UNIDAD/ES",
    #    "orden_compra": "2003",
    #    "detalle": "CARTUCHO TONER"
    #    "importe": 210.0
    # }
    if ('importe' not in cl) or ('cantidad' not in cl):
        return None

    cant = re.match(r'(\d+)', cl['cantidad'])
    if cant is None:
        return None

    try:
        compra = models.Compra.objects.get( \
            orden_compra=int(cl['orden_compra']), \
            fecha__year=os.environ.get('ANIO', datetime.datetime.now().year))
    except ObjectDoesNotExist:
#        logger.warning('No compras found related to compralinea: %r', cl)
        return None

    return models.CompraLineaItem(compra=compra,
                                 importe_unitario=str(cl['importe']),
                                 cantidad=int(cant.groups()[0]),
                                 detalle=cl['detalle'])

def import_compras(compras):
    imported_compras = set()
    for i in compras:
        try:
            orden_compra = int(i['orden_compra'])
            if orden_compra in imported_compras:
                continue
            compra = to_compra_entity(i)
            imported_compras.add(orden_compra)
            compra.save()
            transaction.commit_on_success(compra)
        except Exception:
            logger.exception('Failed to import compra: %r', i)
    logger.info('Successfully imported %d CompraItems', len(compras))

def import_compra_lineas(compra_lineas):
    for i in compra_lineas:
        try:
            compralinea = to_compralinea_entity(i)
            if compralinea is None:
                logger.info("compralinea is None, i'm out")
                continue
            compralinea.save()
            transaction.commit_on_success(compralinea)
        except Exception:
            logger.exception('Failed to import compralinea: %r', i)
    logger.info('Successfully imported %d CompraLineaItems', len(compra_lineas))

def import_jsonlines(instream):
    """ Imports jsonlines into database using available models """
    compras = []
    compra_lineas = []

    for line in instream:
        r = json.loads(line)
        if r[0] == 'CompraItem':
            compras.append(r[1])
        elif r[0] == 'CompraLineaItem':
            compra_lineas.append(r[1])
        else:
            logger.warning('Unknown object type in jsonline: %s', line.rstrip())

    import_compras(compras)
    import_compra_lineas(compra_lineas)

def main(program, *filenames):
    if not filenames:
        import_jsonlines(sys.stdin)
    else:
        for filename in filenames:
            with open(filename) as instream:
                import_jsonlines(instream)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    main(*sys.argv)

