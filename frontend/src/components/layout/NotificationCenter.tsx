import React, { useState, useEffect, useRef } from 'react';
import api from '@/services/api';
import { Bell, Check, Trash2, Loader2, Clock, Volume2, Shield } from 'lucide-react';
import { useToastStore } from '@/store/toastStore';

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationCenter() {
  const { addToast } = useToastStore();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);
  
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/notifications/?limit=20');
      if (res.data?.success) {
        setNotifications(res.data.data || []);
      }
    } catch {
      // Fail silently
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll notifications every 30 seconds for live updates
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      const res = await api.post(`/notifications/${id}/read`);
      if (res.data?.success) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
        addToast('Notification marked as read.', 'success');
      }
    } catch {
      addToast('Failed to mark read.', 'error');
    }
  };

  const handleClearAll = async () => {
    try {
      const res = await api.post('/notifications/clear');
      if (res.data?.success) {
        setNotifications([]);
        addToast('All notifications cleared.', 'success');
      }
    } catch {
      addToast('Failed to clear notifications.', 'error');
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* BELL TRIGGER INDICATOR */}
      <button
        onClick={() => { setIsOpen(!isOpen); fetchNotifications(); }}
        className="relative p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-950 dark:hover:bg-slate-850 transition-colors focus:outline-none"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 h-4 w-4 rounded-full bg-red-500 text-[10px] font-black text-white flex items-center justify-center animate-bounce">
            {unreadCount}
          </span>
        )}
      </button>

      {/* FLOATING DROPDOWN LIST CONTAINER */}
      {isOpen && (
        <div className="absolute right-0 mt-2.5 w-80 sm:w-96 rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 z-50 overflow-hidden animate-in fade-in slide-in-from-top-3 duration-250">
          <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-950/20">
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">Notifications</h4>
              <span className="text-[10px] text-slate-400 font-semibold">{unreadCount} unread alerts</span>
            </div>
            {notifications.length > 0 && (
              <button
                onClick={handleClearAll}
                className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1 font-bold"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Clear all
              </button>
            )}
          </div>

          <div className="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
            {loading && notifications.length === 0 ? (
              <div className="flex p-8 justify-center items-center">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-400 space-y-2">
                <Volume2 className="h-8 w-8 mx-auto opacity-30" />
                <p className="text-xs font-semibold">No alerts or logs recorded.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3.5 flex gap-3 transition-colors ${
                    n.is_read ? 'opacity-70 bg-white hover:bg-slate-50/50 dark:bg-slate-900' : 'bg-blue-500/5 hover:bg-blue-500/10 dark:bg-blue-500/5'
                  }`}
                >
                  <div className={`p-1.5 h-7 w-7 rounded-lg shrink-0 flex items-center justify-center ${
                    n.type === 'Attendance' ? 'bg-emerald-100 text-emerald-600' :
                    n.type === 'Session' ? 'bg-blue-100 text-blue-600' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    <Shield className="h-4 w-4" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between gap-1.5">
                      <p className={`text-xs font-bold leading-tight ${n.is_read ? 'text-slate-700 dark:text-slate-350' : 'text-slate-950 dark:text-white'}`}>
                        {n.title}
                      </p>
                      {!n.is_read && (
                        <button
                          onClick={() => handleMarkAsRead(n.id)}
                          className="text-[10px] text-primary hover:text-indigo-800 flex items-center gap-0.5 font-bold"
                          title="Mark as read"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">{n.message}</p>
                    <span className="text-[9px] text-slate-400 font-semibold block pt-1">
                      {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
