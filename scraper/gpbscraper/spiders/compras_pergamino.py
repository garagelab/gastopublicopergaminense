import urllib
from datetime import datetime
import re
import simplejson

from scrapy.conf import settings
from scrapy.http import Request
from scrapy.spider import BaseSpider

from gpbscraper.items import CompraItem, CompraLineaItem


BASE_URL = 'http://compras.pergamino.gob.ar/compras_getdata.php'
OC_DETAIL_BASE_URL = 'http://compras.pergamino.gob.ar/compras_getdetail.php' # '?ejercicio=2011&oc=3032'

class ComprasPergamino(BaseSpider):

    name = 'compras_pergamino'
    allowed_domains = ['compras.pergamino.gob.ar']

    ejercicio = settings.get('EJERCICIO', datetime.now().year)

    def start_requests(self):
        return [FormRequest(BASE_URL,
                            formdata={
                                'ejercicio': ejercicio,
                                'page': 1,
                                'rows': 10
                            },
                            callback=self.getOCs
                        )]

    def getOCs(self, response):
        ocs = simplejson.loads(response.body)

        for row in ocs['rows']:
            req = FormRequest(OC_DETAIL_BASE_URL,
                              formdata={
                                  'ejercicio': row['EJERCICIO'],
                                  'oc': row['NRO_OC']
                              },
                              callback=self.getOCDetalle)

            item = CompraItem()
            item['orden_compra'] = row['NRO_OC']
            item['fecha'] = datetime.strptime(row['3'], '%d-%m-%Y 00:00:00').strftime('%Y-%m-%d')
            item['importe'] = row['IMPORTE_TOT']
            item['proveedor'] = row['RAZON_SOCIAL']
            item['destino'] = 'Municipalidad de Pergamino'

            tipo, suministro, anio = re.search("(.+) (\d+)/(\d+)", cr.find('EXPEDIENTE').text).groups()
            # item['anio'] = row['EJERCICIO']
            # item['tipo'] = tipo
            # item['suministro'] = suministro

            item['compra_linea_items'] = []

            req.meta['compra'] = item

            yield req


    def getOCDetalle(self, response):

        lineas = simplejson.loads(response.body)

        orden_compra = response.request.meta['compra']

        for oc_detalle in lineas:
            l = CompraLineaItem()
            l['cantidad'] = oc_detalle['CANTIDAD']
#            l['unidad_medida'] = oc_detalle.find('UNIDADMEDIDA').text
            l['detalle'] = oc_detalle['DESCRIPCION']
            l['importe'] = oc_detalle['IMP_UNITARIO']

            orden_compra['compra_linea_items'].append(l)

            yield orden_compra

SPIDER = ComprasPergamino()
