# -*- coding: utf-8 -*-
# from odoo import http


# class Taf(http.Controller):
#     @http.route('/taf/taf', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taf/taf/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('taf.listing', {
#             'root': '/taf/taf',
#             'objects': http.request.env['taf.taf'].search([]),
#         })

#     @http.route('/taf/taf/objects/<model("taf.taf"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taf.object', {
#             'object': obj
#         })

