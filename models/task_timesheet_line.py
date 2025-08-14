# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TaskTimesheetLine(models.Model):
    _name = 'task.timesheet.line'
    _description = 'Task Time Log Entry'
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Work Description',
        help='Brief description of work done'
    )
    
    task_id = fields.Many2one(
        'task.management',
        string='Task',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Add subtask selection
    subtask_id = fields.Many2one(
        'task.subtask',
        string='Subtask',
        domain="[('parent_task_id', '=', task_id)]",
        help='Select the subtask you worked on'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user
    )
    
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today
    )
    
    unit_amount = fields.Float(
        string='Duration (Hours)',
        required=True,
        default=1.0,
        help='Time spent in hours (e.g., 1.5 for 1 hour 30 minutes)'
    )
    
    # Add computed field for display
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Add hour validation fields
    hours_display = fields.Char(
        string='Time Spent',
        compute='_compute_hours_display',
        help='Time in HH:MM format'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    @api.depends('subtask_id', 'name', 'task_id')
    def _compute_display_name(self):
        for record in self:
            if record.subtask_id:
                record.display_name = record.subtask_id.name
            elif record.name:
                record.display_name = record.name
            else:
                record.display_name = _('Time Log Entry')
    
    @api.depends('unit_amount')
    def _compute_hours_display(self):
        """Convert decimal hours to HH:MM format for display"""
        for record in self:
            hours = int(record.unit_amount)
            minutes = int((record.unit_amount - hours) * 60)
            record.hours_display = f"{hours:02d}:{minutes:02d}"
    
    @api.onchange('subtask_id')
    def _onchange_subtask_id(self):
        """Auto-fill description from subtask"""
        if self.subtask_id:
            self.name = self.subtask_id.name
    
    @api.constrains('unit_amount')
    def _check_unit_amount(self):
        """Validate duration is positive and reasonable"""
        for record in self:
            if record.unit_amount <= 0:
                raise ValidationError(_('Duration must be greater than 0 hours.'))
            if record.unit_amount > 24:
                raise ValidationError(_('Duration cannot exceed 24 hours for a single day.'))
            # Warning for unusual durations
            if record.unit_amount > 12:
                # This is just a soft warning during save
                pass  # The constraint allows it but it's unusual
    
    @api.constrains('date')
    def _check_date(self):
        """Validate date is not in the future"""
        for record in self:
            if record.date > fields.Date.today():
                raise ValidationError(_('You cannot log time for future dates.'))
    
    @api.model
    def create(self, vals):
        """Override create to ensure subtask consistency"""
        if 'subtask_id' in vals and vals.get('subtask_id'):
            subtask = self.env['task.subtask'].browse(vals['subtask_id'])
            if not vals.get('name'):
                vals['name'] = subtask.name
        return super(TaskTimesheetLine, self).create(vals)