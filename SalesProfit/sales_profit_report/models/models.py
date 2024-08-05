# -- coding: utf-8 --

from odoo import models, fields, api, exceptions


class SalesProfitReportWiz(models.TransientModel):
    _name = 'sales.profit.report.wiz'
    _description = 'sales_profit_report_wiz'

    date_from = fields.Date(
        string='Date_from',
        required=True)

    date_to = fields.Date(
        string='Date_to',
        required=True)

    products_ids = fields.Many2many(
        comodel_name='product.product',
        string='Product')

    categories_ids = fields.Many2many(
        comodel_name='product.category',
        string='Categories')

    def print_report(self):
        if self.products_ids and self.categories_ids:
            raise exceptions.UserError('Choose either products or categories not both')
        elif not self.products_ids and not self.categories_ids:
            # Default to fetching all products if neither is selected
            products_ids = None  # This will trigger fetching all products in the report generation
            categories_ids = None
        else:
            products_ids = self.products_ids.ids
            categories_ids = self.categories_ids.ids

        return self.env.ref('sales_profit_report.sales_profit_xlsx').report_action(self.id,
                                                                                   data={
                                                                                       'date_from': self.date_from,
                                                                                       'date_to': self.date_to,
                                                                                       'products_ids': products_ids,
                                                                                       'categories_ids': categories_ids,
                                                                                   })



class SalesXlsx(models.AbstractModel):
    _name = 'report.sales_profit_report.sales_profit_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        products_ids = data.get('products_ids')
        categories_ids = data.get('categories_ids')

        # Fetch all products if products_ids is None
        if products_ids is None:
            products_ids = self.env['product.product'].search([]).ids

        so = self.env['sale.order'].search(
            [('date_order', '>=', date_from), ('date_order', '<=', date_to), ('state', '=', 'sale')])
        so_lines = so.mapped('order_line').filtered(
            lambda l: l.product_id.id in products_ids or (l.product_id.categ_id.id in categories_ids))

        pos_orders = self.env['pos.order'].search(
            [('date_order', '>=', date_from), ('date_order', '<=', date_to), ('state', '=', 'done')])
        pos_lines = pos_orders.mapped('lines').filtered(
            lambda l: l.product_id.id in products_ids or (l.product_id.categ_id.id in categories_ids))

        # Unify so_lines and pos_lines fields
        all_lines = []
        for line in so_lines:
            all_lines.append({
                'product_id': line.product_id.id,
                'categ_id': line.product_id.categ_id.id,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'standard_price': line.product_id.standard_price,
                'type': 'sale',
            })
        for line in pos_lines:
            all_lines.append({
                'product_id': line.product_id.id,
                'categ_id': line.product_id.categ_id.id,
                'product_uom_qty': line.qty,
                'price_unit': line.price_unit,
                'standard_price':  line.price_unit,
                'type': 'pos',
            })

        sheet = workbook.add_worksheet('Sales Profit')
        header = workbook.add_format({'bold': True, 'border': True, 'align': 'center'})
        cell = workbook.add_format({'bold': True, 'border': True, 'align': 'center'})

        grouped_lines = self.group_and_sum_order_lines(all_lines)
        sheet.set_column('A:A', 20)  # Sets column A width to 20 characters
        sheet.set_column('B:B', 50)  # Sets column B width to 10 characters
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('G:G', 15)

        sheet.merge_range("A1:B1", 'التاريخ من', header)
        sheet.write(0, 2, date_from, header)

        sheet.merge_range("E1:F1", 'التاريخ إلى', header)
        sheet.write(0, 6, date_to, header)

        sheet.merge_range("A2:F2", 'التقرير  يشمل إجمالي المبيعات ونقاط البيع', header)

        sheet.write(3, 0, 'الفئه', header)
        sheet.write(3, 1, 'اسم الصنف', header)
        sheet.write(3, 2, 'الكمية المباعة', header)
        sheet.write(3, 3, 'قيمة الكمية المباعة', header)
        sheet.write(3, 4, 'تكلفة الكمية المباعة', header)
        sheet.write(3, 5, 'صافي الربح', header)

        row = 3
        for line in grouped_lines:
            row += 1
            sheet.write(row, 0, line['type'], cell)  # Write the "type" value for each row
            sheet.write(row, 1, line['product'], cell)
            sheet.write(row, 2, line['product_uom_qty'], cell)
            sheet.write(row, 3, line['price_unit'], cell)
            sheet.write(row, 4, line['standard_price'], cell)
            sheet.write(row, 5, line['price_unit'] - line['standard_price'], cell)

    def group_and_sum_order_lines(self, order_lines):
        grouped_data = {}

        for line in order_lines:
            product_id = line['product_id']
            categ_id = line['categ_id']
            source_type = line['type']

            if product_id in grouped_data:
                grouped_data[product_id]['product_uom_qty'] += line['product_uom_qty']
                grouped_data[product_id]['standard_price'] += line['standard_price'] * line['product_uom_qty']
                grouped_data[product_id]['price_unit'] += line['price_unit']
                grouped_data[product_id]['type'] = f'{source_type}_المنتج'
            else:
                grouped_data[product_id] = {
                    'product_id': product_id,
                    'product_uom_qty': line['product_uom_qty'],
                    'standard_price': line['standard_price'] * line['product_uom_qty'],
                    'price_unit': line['price_unit'],
                    'type': f'{source_type}_المنتج',
                }

            if categ_id and categ_id not in [entry['product_id'] for entry in grouped_data.values()]:
                if categ_id in grouped_data:
                    grouped_data[categ_id]['product_uom_qty'] += line['product_uom_qty']
                    grouped_data[categ_id]['standard_price'] += line['standard_price'] * line['product_uom_qty']
                    grouped_data[categ_id]['price_unit'] += line['price_unit']
                    grouped_data[categ_id]['type'] = f'{source_type}_فئه'
                else:
                    grouped_data[categ_id] = {
                        'product_id': categ_id,
                        'product_uom_qty': line['product_uom_qty'],
                        'standard_price': line['standard_price'] * line['product_uom_qty'],
                        'price_unit': line['price_unit'],
                        'type': f'{source_type}_فئه',
                    }

        result_records = []
        for product_id, data in grouped_data.items():
            result_records.append({
                'product': self.env['product.product'].browse(product_id).name if product_id != categ_id else None,
                'product_uom_qty': data['product_uom_qty'],
                'standard_price': data['standard_price'],
                'price_unit': data['price_unit'],
                'type': data['type'],
            })

        return result_records

