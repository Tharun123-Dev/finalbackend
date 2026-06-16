import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/auth/AuthContext';
import { affiliateService } from '../services/affiliateService';
import { 
  AffiliateProfile, Referral, ReferralLink, CommissionRecord, 
  PayoutTransaction, PerformanceTrend, AffiliateNotification 
} from '../types';

export interface AffiliateStats {
  total: number;
  pending: number;
  paid: number;
  thisMonth: number;
  conversionRate: number;
  totalClicks: number;
  totalReferrals: number;
  activeCampaigns: number;
}

interface AffiliateContextProps {
  profile: AffiliateProfile | null;
  referrals: Referral[];
  links: ReferralLink[];
  transactions: PayoutTransaction[];
  commissions: CommissionRecord[];
  notifications: AffiliateNotification[];
  trends: PerformanceTrend[];
  stats: AffiliateStats | null;
  loading: boolean;
  refreshData: () => Promise<void>;
  createLink: (name: string) => Promise<void>;
  updateProfileDetails: (details: Partial<AffiliateProfile>) => Promise<void>;
  requestPayoutRelease: (amount: number) => Promise<PayoutTransaction>;
  markNotificationRead: (id: string) => Promise<void>;
  markAllNotificationsRead: () => Promise<void>;
}

const AffiliateContext = createContext<AffiliateContextProps | undefined>(undefined);

export const AffiliateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user: authUser } = useAuth();
  const [profile, setProfile] = useState<AffiliateProfile | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [links, setLinks] = useState<ReferralLink[]>([]);
  const [transactions, setTransactions] = useState<PayoutTransaction[]>([]);
  const [commissions, setCommissions] = useState<CommissionRecord[]>([]);
  const [notifications, setNotifications] = useState<AffiliateNotification[]>([]);
  const [trends, setTrends] = useState<PerformanceTrend[]>([]);
  const [stats, setStats] = useState<AffiliateStats | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshData = useCallback(async () => {
    setLoading(true);
    try {
      let userProf: AffiliateProfile | null = null;
      try {
        userProf = await affiliateService.getCurrentUser();
      } catch (err) {
        console.error('Failed to get current user:', err);
      }

      const [
        allRefsRes,
        allLinksRes,
        allTxsRes,
        allCommsRes,
        allNotifsRes,
        allTrendsRes,
        allStatsRes
      ] = await Promise.allSettled([
        affiliateService.getReferrals(),
        affiliateService.getReferralLinks(),
        affiliateService.getPaymentHistory(),
        affiliateService.getCommissionHistory(),
        affiliateService.getNotifications(),
        affiliateService.getPerformanceTrends(),
        affiliateService.getEarningsSummary()
      ]);

      const allRefs = allRefsRes.status === 'fulfilled' ? allRefsRes.value : [];
      const allLinks = allLinksRes.status === 'fulfilled' ? allLinksRes.value : [];
      const allTxs = allTxsRes.status === 'fulfilled' ? allTxsRes.value : [];
      const allComms = allCommsRes.status === 'fulfilled' ? allCommsRes.value : [];
      const allNotifs = allNotifsRes.status === 'fulfilled' ? allNotifsRes.value : [];
      const allTrends = allTrendsRes.status === 'fulfilled' ? allTrendsRes.value : [];
      const allStats = allStatsRes.status === 'fulfilled' ? allStatsRes.value : {
        total: 0,
        pending: 0,
        paid: 0,
        thisMonth: 0,
        conversionRate: 0,
        totalClicks: 0,
        totalReferrals: 0,
        activeCampaigns: 0
      };

      // Override with active logged-in user details if available
      if (authUser && userProf) {
        userProf.name = localStorage.getItem('name') || authUser.email.split('@')[0] || userProf.name;
        userProf.email = authUser.email || userProf.email;
      }

      setProfile(userProf);
      setReferrals(allRefs);
      setLinks(allLinks);
      setTransactions(allTxs);
      setCommissions(allComms);
      setNotifications(allNotifs);
      setTrends(allTrends);
      setStats(allStats);
    } catch (error) {
      console.error('Failed to load affiliate data:', error);
    } finally {
      setLoading(false);
    }
  }, [authUser]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshData();
  }, [refreshData]);

  const createLink = async (name: string) => {
    try {
      await affiliateService.createReferralLink(name);
      const updatedLinks = await affiliateService.getReferralLinks();
      setLinks(updatedLinks);
    } catch (error) {
      console.error('Failed to generate referral link:', error);
      throw error;
    }
  };

  const updateProfileDetails = async (details: Partial<AffiliateProfile>) => {
    try {
      const updated = await affiliateService.updateProfile(details);
      setProfile(updated);
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  };

  const requestPayoutRelease = async (amount: number) => {
    try {
      const tx = await affiliateService.requestPayout(amount);
      const updatedTxs = await affiliateService.getPaymentHistory();
      setTransactions(updatedTxs);
      
      // Update local profile pending/paid state
      if (profile) {
        setProfile({
          ...profile,
          earnings: {
            ...profile.earnings,
            pending: Math.max(0, profile.earnings.pending - amount),
          }
        });
      }
      return tx;
    } catch (error) {
      console.error('Failed to request payout:', error);
      throw error;
    }
  };

  const markNotificationRead = async (id: string) => {
    try {
      await affiliateService.markAsRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    } catch (error) {
      console.error('Failed to mark notification read:', error);
    }
  };

  const markAllNotificationsRead = async () => {
    try {
      await affiliateService.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark all notifications read:', error);
    }
  };

  return (
    <AffiliateContext.Provider
      value={{
        profile,
        referrals,
        links,
        transactions,
        commissions,
        notifications,
        trends,
        stats,
        loading,
        refreshData,
        createLink,
        updateProfileDetails,
        requestPayoutRelease,
        markNotificationRead,
        markAllNotificationsRead,
      }}
    >
      {children}
    </AffiliateContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAffiliate = () => {
  const context = useContext(AffiliateContext);
  if (context === undefined) {
    throw new Error('useAffiliate must be used within an AffiliateProvider');
  }
  return context;
};


