# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class TaskSubtask(models.Model):
    _name = 'task.subtask'
    _description = 'Task Subtask'
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(string='Subtask', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    parent_task_id = fields.Many2one(
        'task.management',
        string='Parent Task',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Assigned to',
        domain="[('share', '=', False), ('active', '=', True)]"
    )
    
    is_done = fields.Boolean(
        string='Done',
        default=False
    )
    
    deadline = fields.Date(string='Deadline')
    
    description = fields.Text(string='Description')
    
    # Add parent task deadline for reference
    parent_deadline = fields.Datetime(
        related='parent_task_id.date_deadline',
        string='Task Deadline',
        readonly=True,
        store=True
    )
    
    @api.constrains('deadline', 'parent_task_id')
    def _check_subtask_deadline(self):
        """Validate that subtask deadline doesn't exceed parent task deadline"""
        for subtask in self:
            if subtask.deadline and subtask.parent_task_id.date_deadline:
                # Convert parent deadline to date for comparison
                if isinstance(subtask.parent_task_id.date_deadline, datetime):
                    parent_deadline_date = subtask.parent_task_id.date_deadline.date()
                else:
                    parent_deadline_date = subtask.parent_task_id.date_deadline
                
                # Ensure subtask deadline is also a date object for comparison
                if isinstance(subtask.deadline, datetime):
                    subtask_deadline = subtask.deadline.date()
                else:
                    subtask_deadline = subtask.deadline
                    
                if subtask_deadline > parent_deadline_date:
                    raise ValidationError(_(
                        'Subtask deadline cannot exceed the main task deadline (%s). '
                        'Please select a date before or on %s.'
                    ) % (subtask.name, parent_deadline_date.strftime('%m/%d/%Y')))
    
    @api.onchange('deadline')
    def _onchange_deadline(self):
        """Check deadline when changed"""
        if self.deadline and self.parent_task_id.date_deadline:
            # Convert parent deadline to date for comparison
            if isinstance(self.parent_task_id.date_deadline, datetime):
                parent_deadline_date = self.parent_task_id.date_deadline.date()
            else:
                parent_deadline_date = self.parent_task_id.date_deadline
            
            # Ensure self.deadline is also a date object for comparison
            if isinstance(self.deadline, datetime):
                subtask_deadline = self.deadline.date()
            else:
                subtask_deadline = self.deadline
                
            if subtask_deadline > parent_deadline_date:
                return {
                    'warning': {
                        'title': _('Invalid Deadline'),
                        'message': _(
                            'Subtask deadline cannot exceed the main task deadline (%s). '
                            'Please select an earlier date.'
                        ) % parent_deadline_date.strftime('%m/%d/%Y')
                    }
                }
    
    @api.onchange('is_done')
    def _onchange_is_done(self):
        if self.is_done and self.parent_task_id:
            # Update parent task progress
            total_subtasks = len(self.parent_task_id.subtask_ids)
            if total_subtasks > 0:
                done_subtasks = len(self.parent_task_id.subtask_ids.filtered('is_done'))
                self.parent_task_id.progress = (done_subtasks / total_subtasks) * 100