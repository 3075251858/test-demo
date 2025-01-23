from odoo import fields, models, api

class UpdateSalespersonAndSalesTeam(models.TransientModel):
    _name = 'yunkuaiji.sales.transfers'
    _description = '批量转移记录到指定 销售员/顾问 或 团队'

    lead_ids = fields.Many2many('yunkuaiji.sale.lead', string='销售线索')
    salesperson_id = fields.Many2one('res.users', string="销售/顾问：",)
    sales_team_id = fields.Many2one('hr.department', string="团队：")

    @api.one
    def update_sales_person_or_sales_team(self):
        if self.lead_ids and (self.salesperson_id or self.sales_team_id):
            for lead in self.lead_ids:
                if self.salesperson_id: lead.update({'salesperson_id': self.salesperson_id})
                if self.sales_team_id: lead.update({'sales_team_id': self.sales_team_id})

    @api.model
    def default_get(self, fields):
        result = {}
        lead_obj = self.env['yunkuaiji.sale.lead']
        result['lead_ids'] = lead_obj.search([('id', '=', self.env.context.get('active_ids'))]).ids
        return result
