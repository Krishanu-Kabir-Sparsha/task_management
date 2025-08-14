# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TaskTeam(models.Model):
    _name = 'task.team'
    _description = 'Task Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'
    
    name = fields.Char(string='Team Name', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color Index', default=0)
    
    # Manager
    manager_id = fields.Many2one(
        'res.users',
        string='Team Manager',
        required=True,
        tracking=True,
        domain="[('share', '=', False)]"
    )
    
    # Team Members
    member_ids = fields.Many2many(
        'res.users',
        'task_team_members_rel',
        'team_id',
        'user_id',
        string='Team Members',
        domain="[('share', '=', False)]"
    )
    
    # Parent/Child Teams
    parent_team_id = fields.Many2one(
        'task.team',
        string='Parent Team',
        ondelete='cascade'
    )
    
    child_team_ids = fields.One2many(
        'task.team',
        'parent_team_id',
        string='Child Teams'
    )
    
    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # Description
    description = fields.Html(string='Team Description')
    
    # Tasks
    task_ids = fields.One2many(
        'task.management',
        'team_id',
        string='Team Tasks'
    )
    
    task_count = fields.Integer(
        string='Task Count',
        compute='_compute_task_count',
        store=True
    )
    
    @api.depends('task_ids')
    def _compute_task_count(self):
        for team in self:
            team.task_count = len(team.task_ids)
    
    def action_create_task(self):
        """Create a new task for this team"""
        self.ensure_one()
        return {
            'name': _('New Team Task'),
            'type': 'ir.actions.act_window',
            'res_model': 'task.management',
            'view_mode': 'form',
            'context': {
                'default_team_id': self.id,
                'default_task_type': 'team',
            }
        }
    
    def action_view_tasks(self):
        """View all tasks for this team"""
        self.ensure_one()
        return {
            'name': _('Team Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'task.management',
            'view_mode': 'list,kanban,form',
            'domain': [('team_id', '=', self.id)],
            'context': {
                'default_team_id': self.id,
                'default_task_type': 'team',
            }
        }