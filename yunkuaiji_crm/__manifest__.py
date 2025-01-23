# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': '意向客户管理',
    'version': '1.0',
    'summary': '无',
    'sequence': 12,
    'description': """
    无介绍
    """,
    'category': '.....',
    'depends': ['base', 'base_setup', 'mail', 'web', 'portal', 'hr'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/sale_lead.xml',
        'wizard/transfer_salesperson_or_salesteam.xml',
        'data/yunkuaiji_customer_type.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
