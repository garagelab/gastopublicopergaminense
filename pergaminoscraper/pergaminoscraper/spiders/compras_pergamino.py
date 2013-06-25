from datetime import datetime
import re
import simplejson
import urllib

from scrapy.conf import settings
from scrapy.http import Request, FormRequest
from scrapy.spider import BaseSpider

from pergaminoscraper.items import CompraItem, CompraLineaItem

BASE_URL = 'http://compras.pergamino.gob.ar/compras_getdata.php'
OC_DETAIL_BASE_URL = 'http://compras.pergamino.gob.ar/compras_getdetail.php?'

class ComprasPergaminoSpider(BaseSpider):

    name = 'compras'
    allowed_domains = ['compras.pergamino.gob.ar']

    ejercicio = settings.get('EJERCICIO', datetime.now().year)

    def start_requests(self):
        return [FormRequest(BASE_URL,
                            formdata={
                                'ejercicio': str(self.ejercicio),
                                'page': '1',
                                'rows': '10'
                            },
                            meta={'page': 1},
                            callback=self.getPageOfOCs
                        )]

    def getPageOfOCs(self, response):
        ocs = simplejson.loads(response.body)

        for row in ocs['rows']:
            req = Request(OC_DETAIL_BASE_URL + urllib.urlencode({
                                  'ejercicio': row['EJERCICIO'],
                                  'oc': row['NRO_OC']
                              }),
                              callback=self.getOCDetalle)

            item = CompraItem()
            item['orden_compra'] = row['NRO_OC']
            item['fecha'] = datetime.strptime(row['3'],
                                              '%d-%m-%Y 00:00:00').strftime('%Y-%m-%d')
            item['importe'] = row['IMPORTE_TOT']
            item['proveedor'] = row['RAZON_SOCIAL']
            item['destino'] = 'Municipalidad de Pergamino'

            item['anio'] = row['EJERCICIO']
            # item['tipo'] = tipo
            # item['suministro'] = suministro

            item['compra_linea_items'] = []

            req.meta['compra'] = item

            yield req

        if len(ocs['rows']) > 0:
            yield FormRequest(BASE_URL,
                              formdata={
                                  'ejercicio': str(self.ejercicio),
                                  'page': str(response.request.meta['page'] + 1),
                                  'rows': '10'
                              },
                              meta={'page': response.request.meta['page'] + 1},
                              callback=self.getPageOfOCs)

        yield None


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

SPIDER = ComprasPergaminoSpider()
