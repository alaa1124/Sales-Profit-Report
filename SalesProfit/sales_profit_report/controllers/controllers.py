# -*- coding: utf-8 -*-
# from odoo import http


# class SalesProfitReport(http.Controller):
#     @http.route('/sales_profit_report/sales_profit_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_profit_report/sales_profit_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_profit_report.listing', {
#             'root': '/sales_profit_report/sales_profit_report',
#             'objects': http.request.env['sales_profit_report.sales_profit_report'].search([]),
#         })

#     @http.route('/sales_profit_report/sales_profit_report/objects/<model("sales_profit_report.sales_profit_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_profit_report.object', {
#             'object': obj
#         })

