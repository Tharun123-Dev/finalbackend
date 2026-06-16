export interface AffiliateProfile {
  id: string;
  name: string;
  email: string;
  avatar: string;
  phone?: string;
  address?: string;
  upiId?: string;
  bankDetails?: {
    holderName: string;
    bankName: string;
    accountNumber: string;
    payoutMethod: string;
  };
  earnings: {
    total: number;
    pending: number;
    paid: number;
    thisMonth: number;
  };
  referralCode?: string;
  tier?: string;
}

export interface Referral {
  id: string;
  name: string;
  email: string;
  plan: string;
  status: 'pending' | 'converted' | 'cancelled';
  joinedDate: string;
  commission: number;
  totalSpent: number;
  tier: string;
  avatar: string;
}

export interface ReferralLink {
  id: string;
  name: string;
  url: string;
  clicks: number;
  signups: number;
  conversions: number;
  conversionRate: string;
  earnings: number;
  status: 'active' | 'archived';
}

export interface CommissionRecord {
  id: string;
  referrer: string;
  type: string;
  rate: string;
  amount: number;
  date: string;
  status: 'paid' | 'pending' | 'failed';
}

export interface PayoutTransaction {
  id: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  date: string;
  method: string;
  invoiceNumber: string;
  description: string;
}

export interface PerformanceTrend {
  month: string;
  commission: number;
  clicks: number;
}

export interface AffiliateNotification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
  read: boolean;
  date: string;
}


