export interface Member {
  id: string;
  name: string;
  role: string;
  email: string;
  avatar: string;
}

export interface Attachment {
  id: string;
  name: string;
  size: string;
  type: string;
  url: string;
}

export interface TaskComment {
  id: string;
  author: Member;
  content: string;
  timestamp: string;
}

export interface TaskHistory {
  id: string;
  user: string;
  action: string;
  details: string;
  timestamp: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'inProgress' | 'completed' | 'onHold' | 'overdue' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assignedTo?: Member;
  assignedBy?: Member;
  startDate?: string;
  dueDate?: string;
  tags?: string[];
  attachments?: Attachment[];
  relatedModule?: string;
  createdDate?: string;
  archived?: boolean;
  comments?: TaskComment[];
  history?: TaskHistory[];
}

export interface Notification {
  id: string;
  type: 'assigned' | 'overdue' | 'mention' | 'reminder';
  taskTitle: string;
  taskId: string;
  sender: string;
  timestamp: string;
  read: boolean;
  message: string;
}


