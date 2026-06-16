import rolesApi from '@/services/rolesApi';
import { Task, Member, Notification } from '../types';

export const tasksService = {
  getTasks: () => rolesApi.get<Task[]>('/tasks/'),
  createTask: (data: Partial<Task>) => rolesApi.post<Task>('/tasks/', data),
  updateTask: (id: string, data: Partial<Task>) => rolesApi.patch<Task>(`/tasks/${id}/`, data),
  deleteTask: (id: string) => rolesApi.delete<unknown>(`/tasks/${id}/`),
  archiveTask: (id: string) => rolesApi.post<Task>(`/tasks/${id}/archive/`),
  addComment: (id: string, content: string) => rolesApi.post<Task>(`/tasks/${id}/comment/`, { content }),
  getMembers: () => rolesApi.get<Member[] | { content?: Member[]; data?: Member[]; results?: Member[] }>('/users'),
  getNotifications: () => rolesApi.get<Notification[]>('/tasks/notifications/'),
  markNotificationsRead: () => rolesApi.post<unknown>('/tasks/mark_notifications_read/'),
};


