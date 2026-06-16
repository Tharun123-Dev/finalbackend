import { Member, Task, Notification } from '../types';

export const MEMBERS: Member[] = [
  { id: 'usr-1', name: 'Dr. Aris Thorne', role: 'Academic Registrar', email: 'aris.thorne@edu.com', avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80' },
  { id: 'usr-2', name: 'Sarah Jenkins', role: 'Lead Admissions Counselor', email: 'sarah.j@edu.com', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80' },
  { id: 'usr-3', name: 'Michael Chang', role: 'IT Director & Dev Lead', email: 'm.chang@edu.com', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80' },
  { id: 'usr-4', name: 'Emma Watson', role: 'HR Operations Manager', email: 'emma.w@edu.com', avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&auto=format&fit=crop&q=80' },
  { id: 'usr-5', name: 'Kabir Dev', role: 'Admissions Counselor', email: 'kabir.d@edu.com', avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80' },
  { id: 'usr-6', name: 'Priya Patel', role: 'Admissions Counselor', email: 'priya.p@edu.com', avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80' },
];

export const RELATED_MODULES: string[] = [
  'Lead Intake Form',
  'Counselor Admission Quotas',
  'Student Fee Portal',
  'HR Staff Recruitment',
  'Academic Course Scheduling',
  'Alumni Relations Campaign',
  'Exam Assessment System',
];

export const TAGS: string[] = [
  'Admissions',
  'IT Support',
  'HR Operations',
  'Database',
  'Student Support',
  'Finance',
  'Marketing',
  'Bugs/Fixes',
];

const getRelativeDate = (offsetDays: number): string => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().split('T')[0];
};

export const INITIAL_TASKS: Task[] = [
  {
    id: 'TSK-1001',
    title: 'Fix lead registration 422 validation error',
    description: 'Counselors are facing a 422 Unprocessable Entity error when submitting the dynamic lead intake form. Inspect the Pydantic schema backend validation against the frontend form data structure. This is blocking the summer intake counselors from logging leads.',
    status: 'inProgress',
    priority: 'urgent',
    assignedTo: MEMBERS[2],
    assignedBy: MEMBERS[1],
    startDate: getRelativeDate(-2),
    dueDate: getRelativeDate(0),
    tags: ['Bugs/Fixes', 'IT Support', 'Admissions'],
    attachments: [
      { id: 'att-1', name: 'error_log_screenshot.png', size: '245 KB', type: 'image/png', url: '#' },
      { id: 'att-2', name: 'schema_payload.json', size: '12 KB', type: 'application/json', url: '#' }
    ],
    relatedModule: 'Lead Intake Form',
    createdDate: getRelativeDate(-2),
    archived: false,
    comments: [
      { id: 'c-1', author: MEMBERS[1], content: 'Hi Michael, this is blocking our counselor team from registering new student walk-ins. Can you look at this urgently?', timestamp: getRelativeDate(-1) + ' 10:30 AM' },
      { id: 'c-2', author: MEMBERS[2], content: 'Investigating. I found that the custom fields schema expects integers for dropdown selection but we are sending strings from the react-select widget.', timestamp: getRelativeDate(-1) + ' 02:15 PM' }
    ],
    history: [
      { id: 'h-1', user: 'Sarah Jenkins', action: 'Task Created', details: 'Created task and assigned to Michael Chang', timestamp: getRelativeDate(-2) + ' 09:00 AM' },
      { id: 'h-2', user: 'Michael Chang', action: 'Status Updated', details: 'Changed status from Pending to In Progress', timestamp: getRelativeDate(-1) + ' 02:00 PM' },
      { id: 'h-3', user: 'Michael Chang', action: 'Comment Added', details: 'Added comment detailing custom fields integer conflict', timestamp: getRelativeDate(-1) + ' 02:15 PM' }
    ]
  },
  {
    id: 'TSK-1002',
    title: 'Configure counselor admission quotas for summer intake',
    description: 'We need to allocate target admission numbers for each counselor (Sarah, Kabir, Priya) for the upcoming summer batch. Enter these targets into the system so progress charts calculate counselor ratios correctly.',
    status: 'completed',
    priority: 'high',
    assignedTo: MEMBERS[1],
    assignedBy: MEMBERS[0],
    startDate: getRelativeDate(-5),
    dueDate: getRelativeDate(-1),
    tags: ['Admissions', 'HR Operations'],
    attachments: [{ id: 'att-3', name: 'Summer_Quota_Allocation.xlsx', size: '1.2 MB', type: 'xlsx', url: '#' }],
    relatedModule: 'Counselor Admission Quotas',
    createdDate: getRelativeDate(-5),
    archived: false,
    comments: [
      { id: 'c-3', author: MEMBERS[0], content: 'Completed the board review. Quotas are signed off. Please apply this to the Counselor Performance module.', timestamp: getRelativeDate(-4) + ' 11:15 AM' },
      { id: 'c-4', author: MEMBERS[1], content: 'All numbers entered and counselor weights configured. Ready for review.', timestamp: getRelativeDate(-1) + ' 04:30 PM' }
    ],
    history: [
      { id: 'h-4', user: 'Dr. Aris Thorne', action: 'Task Created', details: 'Created task and assigned to Sarah Jenkins', timestamp: getRelativeDate(-5) + ' 10:00 AM' },
      { id: 'h-5', user: 'Sarah Jenkins', action: 'Status Updated', details: 'Changed status to Completed', timestamp: getRelativeDate(-1) + ' 04:30 PM' }
    ]
  },
  {
    id: 'TSK-1003',
    title: 'Follow up on overdue student tuition payments',
    description: 'Several students from the Spring 2026 Batch have unpaid balances on their Tuition fees. Reach out to them to establish payment plan timelines or record processed transactions.',
    status: 'overdue',
    priority: 'urgent',
    assignedTo: MEMBERS[5],
    assignedBy: MEMBERS[0],
    startDate: getRelativeDate(-10),
    dueDate: getRelativeDate(-3),
    tags: ['Finance', 'Student Support'],
    attachments: [{ id: 'att-4', name: 'Spring_Overdue_List.pdf', size: '340 KB', type: 'pdf', url: '#' }],
    relatedModule: 'Student Fee Portal',
    createdDate: getRelativeDate(-10),
    archived: false,
    comments: [],
    history: [{ id: 'h-6', user: 'Dr. Aris Thorne', action: 'Task Created', details: 'Created task and assigned to Priya Patel', timestamp: getRelativeDate(-10) + ' 09:30 AM' }]
  },
  {
    id: 'TSK-1004',
    title: 'Staff recruitment drive: review counselor CV applications',
    description: 'We need to hire two additional admission counselors for the upcoming regional recruitment. Review candidate CVs forwarded by HR and select top 5 for the round of interviews.',
    status: 'onHold',
    priority: 'medium',
    assignedTo: MEMBERS[3],
    assignedBy: MEMBERS[0],
    startDate: getRelativeDate(-3),
    dueDate: getRelativeDate(2),
    tags: ['HR Operations'],
    attachments: [],
    relatedModule: 'HR Staff Recruitment',
    createdDate: getRelativeDate(-3),
    archived: false,
    comments: [{ id: 'c-5', author: MEMBERS[3], content: 'Placed on hold temporarily as budget clearance is pending from the CFO office.', timestamp: getRelativeDate(-1) + ' 09:00 AM' }],
    history: [
      { id: 'h-7', user: 'Dr. Aris Thorne', action: 'Task Created', details: 'Created task and assigned to Emma Watson', timestamp: getRelativeDate(-3) + ' 11:00 AM' },
      { id: 'h-8', user: 'Emma Watson', action: 'Status Updated', details: 'Changed status to On Hold', timestamp: getRelativeDate(-1) + ' 09:00 AM' }
    ]
  },
  {
    id: 'TSK-1005',
    title: 'Migrate student record system to PostgreSQL database',
    description: 'Complete the database migration script. We are migrating from the SQLite local prototype to PostgreSQL on AWS RDS. Ensure index creation scripts are tested and lead fields mapping functions properly.',
    status: 'inProgress',
    priority: 'high',
    assignedTo: MEMBERS[2],
    assignedBy: MEMBERS[2],
    startDate: getRelativeDate(-6),
    dueDate: getRelativeDate(5),
    tags: ['Database', 'IT Support'],
    attachments: [],
    relatedModule: 'Academic Course Scheduling',
    createdDate: getRelativeDate(-6),
    archived: false,
    comments: [],
    history: [{ id: 'h-9', user: 'Michael Chang', action: 'Task Created', details: 'Self-assigned database migration task', timestamp: getRelativeDate(-6) + ' 08:30 AM' }]
  },
  {
    id: 'TSK-1006',
    title: 'Prepare counselor performance report for board meeting',
    description: 'Gather statistical data on lead conversion ratios, response times, and counseling call durations to compile a report for the upcoming board session.',
    status: 'pending',
    priority: 'high',
    assignedTo: MEMBERS[1],
    assignedBy: MEMBERS[0],
    startDate: getRelativeDate(0),
    dueDate: getRelativeDate(3),
    tags: ['Admissions', 'HR Operations'],
    attachments: [],
    relatedModule: 'Counselor Admission Quotas',
    createdDate: getRelativeDate(0),
    archived: false,
    comments: [],
    history: [{ id: 'h-10', user: 'Dr. Aris Thorne', action: 'Task Created', details: 'Created task and assigned to Sarah Jenkins', timestamp: getRelativeDate(0) + ' 10:00 AM' }]
  },
  {
    id: 'TSK-1007',
    title: 'Counseling student intake review (Q2 batch)',
    description: 'Schedule a call with student intake delegates to review regional complaints and verify the Counselor portal interface.',
    status: 'cancelled',
    priority: 'low',
    assignedTo: MEMBERS[4],
    assignedBy: MEMBERS[1],
    startDate: getRelativeDate(-15),
    dueDate: getRelativeDate(-12),
    tags: ['Student Support', 'Admissions'],
    attachments: [],
    relatedModule: 'Lead Intake Form',
    createdDate: getRelativeDate(-15),
    archived: false,
    comments: [{ id: 'c-6', author: MEMBERS[1], content: 'Cancelled as Q2 intake was combined with Summer enrollment directly.', timestamp: getRelativeDate(-13) + ' 05:00 PM' }],
    history: [
      { id: 'h-11', user: 'Sarah Jenkins', action: 'Task Created', details: 'Created task and assigned to Kabir Dev', timestamp: getRelativeDate(-15) + ' 11:30 AM' },
      { id: 'h-12', user: 'Sarah Jenkins', action: 'Status Updated', details: 'Changed status to Cancelled', timestamp: getRelativeDate(-13) + ' 05:00 PM' }
    ]
  },
  {
    id: 'TSK-1008',
    title: 'Setup campus WiFi network extensions for Exam Hall B',
    description: 'Students require stable network access during online exam evaluations. Setup access points inside building level 2 and verify load balancing controls.',
    status: 'pending',
    priority: 'low',
    assignedTo: MEMBERS[2],
    assignedBy: MEMBERS[3],
    startDate: getRelativeDate(1),
    dueDate: getRelativeDate(4),
    tags: ['IT Support'],
    attachments: [],
    relatedModule: 'Exam Assessment System',
    createdDate: getRelativeDate(-1),
    archived: false,
    comments: [],
    history: [{ id: 'h-13', user: 'Emma Watson', action: 'Task Created', details: 'Created task and assigned to Michael Chang', timestamp: getRelativeDate(-1) + ' 03:00 PM' }]
  },
  {
    id: 'TSK-1009',
    title: 'Review Alumni Campaign outbound email marketing template',
    description: 'Ensure counselor contact details and admission referral links are properly formatted inside the mail newsletter draft.',
    status: 'inProgress',
    priority: 'medium',
    assignedTo: MEMBERS[4],
    assignedBy: MEMBERS[1],
    startDate: getRelativeDate(-1),
    dueDate: getRelativeDate(1),
    tags: ['Marketing', 'Admissions'],
    attachments: [],
    relatedModule: 'Alumni Relations Campaign',
    createdDate: getRelativeDate(-1),
    archived: false,
    comments: [],
    history: [{ id: 'h-14', user: 'Sarah Jenkins', action: 'Task Created', details: 'Created task and assigned to Kabir Dev', timestamp: getRelativeDate(-1) + ' 09:30 AM' }]
  }
];

export const INITIAL_NOTIFICATIONS: Notification[] = [
  { id: 'ntf-1', type: 'assigned', taskTitle: 'Fix lead registration 422 validation error', taskId: 'TSK-1001', sender: 'Sarah Jenkins', timestamp: '2 hours ago', read: false, message: 'assigned you a task: Fix lead registration 422 validation error.' },
  { id: 'ntf-2', type: 'overdue', taskTitle: 'Follow up on overdue student tuition payments', taskId: 'TSK-1003', sender: 'System Monitor', timestamp: '1 day ago', read: false, message: 'Task is overdue! Follow up on overdue student tuition payments was due on ' + getRelativeDate(-3) + '.' },
  { id: 'ntf-3', type: 'mention', taskTitle: 'Configure counselor admission quotas for summer intake', taskId: 'TSK-1500', sender: 'Dr. Aris Thorne', timestamp: '2 days ago', read: true, message: 'mentioned you in a comment: "Please apply this to the Counselor Performance module."' },
  { id: 'ntf-4', type: 'reminder', taskTitle: 'Fix lead registration 422 validation error', taskId: 'TSK-1001', sender: 'Calendar Agent', timestamp: '3 hours ago', read: false, message: 'Task due today: Fix lead registration 422 validation error.' }
];


