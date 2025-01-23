from odoo import fields, models, api

from datetime import date
from odoo.exceptions import UserError  # 导入 UserError 异常


class SaleLead(models.Model):
    _name = 'yunkuaiji.sale.lead'
    _description = '销售线索'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'partner_id'
    _order = "create_date desc"

    opportunities = fields.Char(string="商机", required=True)
    # registration_date = fields.Date(string="登记时间", default=date.today())
    stage = fields.Selection([
        ('new', '新'),
        ('demand_exploration', '挖'),
        ('objection_resolution', '异'),
        ('invitation', '约'),
        ('in_person_interview', '访'),
        ('signed_and_paid', '签'),
        ('lost', '失')
    ], string="阶段", default='new', track_visibility='onchange')
    # 归档功能，当值为True时，该记录会归档，
    # 在tree视图的动作中自动生成 归档 选项，选择记录后可以点击 归档
    # 归档后，在筛选中会自动多出 已归档 选项，选择已归档选项，勾选记录后动作 中会有 取消归档 选项
    active = fields.Boolean(default=True, track_visibility='onchange')

    # 组一
    partner_id = fields.Many2one('res.partner', string=u'客户名称', ondelete='restrict',
                                 domain=[('parent_id', '=', False)], required=True)
    establishment_date = fields.Date(string="成立时间", required=True)
    contact_name = fields.Char(string="联系人姓名", required=True)
    contact_phone = fields.Char(string="联系电话", required=True)
    is_kp = fields.Boolean(string="KP？", required=True)  # 是否关键客户

    # 组二
    company_type = fields.Selection([
        ('small_scale', '小规模'),
        ('general_taxpayer', '一般人'),
        ('individual', '个体户')
    ], string="公司类型", required=True)
    source = fields.Selection([
        ('telemarketing', '电销'),
        ('boss_other_company', '老板其它公司'),
        ('referral', '转介绍'),
        ('street_marketing', '地推'),
        ('douyin', '抖音'),
        ('xiaohongshu', '小红书'),
        ('other', '其他')
    ], string="来源", required=True)
    customer_type = fields.Many2many('yunkuaiji.sale.customer.type', string='客户类型', required=True)
    financial_status = fields.Selection([
        ('new_register', '新注册'),
        ('full_time', '有专职'),
        ('same_industry', '同行在做'),
        ('family_or_friend', '亲朋好友在做')
    ], string="财务现状", required=True)

    # 组三
    salesperson_id = fields.Many2one(
        'res.users', string="销售/顾问", required=True,
        track_visibility='onchange', default=lambda self: self.env.user.id)
    sales_team_id = fields.Many2one(
        'hr.department', string="团队",
        store=True,  # 确保计算结果存储到数据库
        track_visibility='onchange', required=True)

    # 组四
    intent_assessment = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C'), ],
        string="意向判断", required=True, track_visibility='onchange')
    expected_closing_cycle = fields.Integer(string="预计成交周期（月）", required=True, track_visibility='onchange')
    expected_end_date = fields.Date(string="预期结束", required=True, track_visibility='onchange')
    wechat_verified = fields.Boolean(string="已加微信？", required=True)

    # 组五
    expected_revenue = fields.Integer(string="预期收益", required=True)
    closing_probability = fields.Integer(string="成交概率", required=True)
    supervisor_evaluation = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C')],
        string="主管评价", track_visibility='onchange')
    success_or_lost_cause = fields.Text(string='签约或丢单原因', track_visibility='onchange')
    success_or_lost_cause_date = fields.Date(string='签约或丢单时间')

    # 展示在form视图 notebook
    contact_ids = fields.One2many('yunkuaiji.sale.lead.contact', 'lead_id', string="回访记录")  # 与回访记录关联
    annex_ids = fields.One2many('yunkuaiji.sale.lead.annex', 'lead_ids', string="录音附件")  # 与附件关联

    # 关联字段：获取相关的最新跟进记录（展示在tree视图）
    latest_contact_visit_time = fields.Date(string="最新跟进时间", compute="_compute_latest_contact", store=True)
    latest_contact_visit_content = fields.Text(string="最新跟进内容", compute="_compute_latest_contact", store=True)
    latest_contact_next_visit_time = fields.Date(string="下次跟进时间", compute="_compute_latest_contact", store=True)


    @api.depends('contact_ids.visit_time')  # 监听 sale_lead_contact_ids 的 visit_time 字段变化
    def _compute_latest_contact(self):
        for lead in self:
            # 获取与当前销售线索相关的所有联系记录
            latest_contact = self.env['yunkuaiji.sale.lead.contact'].search(
                [('lead_id', '=', lead.id)],  # 仅选择当前销售线索的相关联系记录
                order='visit_time desc',  # 按 visit_time 降序排序
                limit=1  # 只返回最晚的记录
            )
            if latest_contact:
                lead.latest_contact_visit_time = latest_contact.visit_time
                lead.latest_contact_visit_content = latest_contact.visit_content
                lead.latest_contact_next_visit_time = latest_contact.next_visit_time
            else:
                lead.latest_contact_visit_time = False
                lead.latest_contact_visit_content = False
                lead.latest_contact_next_visit_time = False

    @api.multi
    def write(self, vals):
        """重写 write 方法来检查当 stage 为 'signed_and_paid' 或 'lost' 时，success_or_lost_cause 是否已填写"""
        if vals.get('stage') == 'signed_and_paid' or vals.get('stage') == 'lost':
            # self.success_or_lost_cause: 原本的值
            # vals.get('success_or_lost_cause')：当前输入框的值
            if not vals.get('success_or_lost_cause') and not self.success_or_lost_cause:
                raise UserError('签约或丢失原因不能为空！请进入编辑模式切换--赢、失--后输入原因！')
        # 当从：“失” 变为其它阶段时，清空：签约或丢单原因
        if self.stage == 'lost' and not vals.get('stage') == 'lost':
            vals['success_or_lost_cause'] = False
        return super(SaleLead, self).write(vals)



    @api.onchange('success_or_lost_cause_date', 'stage')
    def _onchange_successor_lost_stage(self):
        """当 success_or_lost_cause_date 字段或 stage 字段变化且不为空时，更新 update_date"""
        if self.stage in ['signed_and_paid', 'lost'] and not self.success_or_lost_cause_date:
            # 如果 stage 是 'signed_and_paid' 或 'lost'，并且 success_or_lost_cause_date 不为空
            self.success_or_lost_cause_date = fields.date.today()  # 设置当前日期时间

class SaleContact(models.Model):
    _name = 'yunkuaiji.sale.lead.contact'
    _description = '跟进记录'
    _order = 'visit_time desc'  # 按 visit_time 字段倒序排序

    name = fields.Char(string="跟进记录标题")
    visit_time = fields.Date(string="跟进时间", required=True, default=date.today())
    visit_content = fields.Text(string="跟进内容", required=True)
    next_visit_time = fields.Date(string="下次跟进时间")
    lead_id = fields.Many2one('yunkuaiji.sale.lead', string="销售线索", required=True,
                              default=lambda self: self._context.get('active_id'))

class SaleAnnex(models.Model):
    _name = 'yunkuaiji.sale.lead.annex'
    _description = '附件'

    upload_time = fields.Date(string="上传时间", default=date.today())
    remarks = fields.Char(string="备注")
    lead_ids = fields.Many2one('yunkuaiji.sale.lead', string="录音附件", required=True,
                               default=lambda self: self._context.get('active_id'))
    attachments = fields.Many2many('ir.attachment', string="上传录音", copy=False)  # 录音附件

class YunkuaijiCustomerType(models.Model):
    _name = 'yunkuaiji.sale.customer.type'
    _description = '客户类型：询价、在意服务、注重价值、看着品牌、其他'
    _order = "sequence"

    sequence = fields.Integer('Sequence')
    name = fields.Char('类型')