# coding: utf-8
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from scrapy.xlib.pydispatch import dispatcher
from scrapy.http import Request
from scrapy import log
from pergaminoscraper.items import CompraItem, CompraLineaItem, ProveedorItem, parse_money
from pergaminoweb.core import models

from twisted.internet import defer, threads

from django.db import transaction, connection


class ComprasPersisterPipeline(object):

    def process_item(self, spider, item):
        if isinstance(item, CompraItem):
            self._persistCompraItem(item)

        return item

    @transaction.commit_on_success
    def _persistCompraItem(self, compra_item):

        if models.Compra.objects.filter(orden_compra=int(compra_item['orden_compra']), fecha=compra_item['fecha']).exists():
            return

        proveedor, proveedor_created = models.Proveedor.objects.get_or_create(nombre_fantasia=compra_item['proveedor'], nombre=compra_item['proveedor'])
        reparticion, reparticion_created = models.Reparticion.objects.get_or_create_by_canonical_name(compra_item['destino'])

        compra = models.Compra(orden_compra=int(compra_item['orden_compra']),
                               importe=parse_money(compra_item['importe']),
                               fecha=compra_item['fecha'],
#                               suministro=compra_item['suministro'],
                               proveedor=proveedor,
                               destino=reparticion)

        print compra


        compra.save()


        # persistir lineas
        for cli in compra_item['compra_linea_items']:
            cli_obj = models.CompraLineaItem(compra=compra,
                                             importe_unitario=parse_money(cli['importe']),
                                             cantidad=cli['cantidad'],
                                             detalle=cli['detalle'],
#                                             unidad_medida=cli['unidad_medida']
            )
            cli_obj.save()
