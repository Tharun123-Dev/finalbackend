import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboardActions } from '@/context/DashboardActionContext'
import { useToast } from '@/context/ToastContext'
import { quickActionMap, type QuickActionId } from '@/config/quick-actions'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const dialogTitles: Record<QuickActionId, string> = {
  'add-user': 'Add User',
  'add-lead': 'Add Lead',
  'create-task': 'Create Task',
  payroll: 'Generate Payroll',
  ticket: 'Create Support Ticket',
  report: 'Generate Report',
  announce: 'Send Announcement',
  followup: 'Create Followup',
}

const selectClass = cn(
  'flex h-10 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]'
)

export function QuickActionDialogs() {
  const { activeAction, closeAction } = useDashboardActions()
  const { success } = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!activeAction) return
    setLoading(true)
    await new Promise((r) => setTimeout(r, 500))

    const form = new FormData(e.currentTarget)

    switch (activeAction) {
      case 'add-user':
        success('User created', `${form.get('name')} added as ${form.get('role')}`)
        navigate('/users')
        break
      case 'add-lead':
        success('Lead added', `${form.get('name')} from ${form.get('company')} saved to pipeline`)
        navigate('/leads')
        break
      case 'create-task':
        success('Task created', `"${form.get('title')}" assigned to ${form.get('assignee')}`)
        navigate('/tasks')
        break
      case 'ticket':
        success('Ticket created', `#TK-${Date.now().toString().slice(-4)} — ${form.get('subject')}`)
        navigate('/tickets')
        break
      case 'announce':
        success('Announcement sent', `Broadcast "${form.get('title')}" to all channels`)
        navigate('/messages')
        break
      case 'followup':
        success('Followup scheduled', `Follow-up with ${form.get('lead')} on ${form.get('date')}`)
        navigate('/followups')
        break
    }

    setLoading(false)
    closeAction()
  }

  if (!activeAction || !quickActionMap[activeAction]?.hasDialog) return null

  return (
    <Dialog open={!!activeAction} onOpenChange={(open) => !open && closeAction()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{dialogTitles[activeAction]}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {activeAction === 'add-user' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Full name</label>
                <Input name="name" required placeholder="Raj Patel" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input name="email" type="email" required placeholder="raj@company.com" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Role</label>
                <select name="role" className={selectClass} defaultValue="Employee">
                  <option value="Admin">Admin</option>
                  <option value="Manager">Manager</option>
                  <option value="Employee">Employee</option>
                  <option value="Viewer">Viewer</option>
                </select>
              </div>
            </>
          )}

          {activeAction === 'add-lead' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Contact name</label>
                <Input name="name" required placeholder="Jane Smith" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Company</label>
                <Input name="company" required placeholder="Acme Corp" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Phone</label>
                <Input name="phone" placeholder="+91 98765 43210" />
              </div>
            </>
          )}

          {activeAction === 'create-task' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Task title</label>
                <Input name="title" required placeholder="Review Q2 proposal" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Assignee</label>
                <Input name="assignee" required placeholder="Sarah Chen" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Due date</label>
                <Input name="dueDate" type="date" required />
              </div>
            </>
          )}

          {activeAction === 'ticket' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Subject</label>
                <Input name="subject" required placeholder="Describe the issue" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Priority</label>
                <select name="priority" className={selectClass} defaultValue="Medium">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Input name="description" placeholder="Additional details" />
              </div>
            </>
          )}

          {activeAction === 'announce' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Title</label>
                <Input name="title" required placeholder="Company update" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Message</label>
                <Input name="message" required placeholder="Announcement body" />
              </div>
            </>
          )}

          {activeAction === 'followup' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Lead / Contact</label>
                <Input name="lead" required placeholder="Acme Corp — Jane Smith" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Follow-up date</label>
                <Input name="date" type="date" required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Notes</label>
                <Input name="notes" placeholder="Call regarding enterprise plan" />
              </div>
            </>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={closeAction} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving…' : 'Submit'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}


