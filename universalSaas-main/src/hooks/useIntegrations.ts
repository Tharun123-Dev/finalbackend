// useIntegrations hook – real backend integration
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useToast } from '@/context/ToastContext';
import { startOAuthConnect } from '@/api/integrations';
import {
  listIntegrations,
  getIntegration,
  getIntegrationLogs,
  getSyncHistory,
  toggleIntegration,
  configureIntegration,
  testIntegration,
  disconnectIntegration,
  getZapierLogs
} from '@/api/integrations';
import type {
  IntegrationCardResponse,
  IntegrationDetailsResponse,
  IntegrationLogResponse,
  SyncHistoryResponse,
} from '@/types/integrations-api';

export function useIntegrations() {
  const { success, error: toastError } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [cards, setCards] = useState<IntegrationCardResponse[]>([]);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [details, setDetails] = useState<IntegrationDetailsResponse | null>(null);
  const [logs, setLogs] = useState<IntegrationLogResponse[]>([]);
  const [syncHistory, setSyncHistory] = useState<SyncHistoryResponse[]>([]);
  const [logsPage, setLogsPage] = useState(0);
  const [logsTotalPages, setLogsTotalPages] = useState(0);

  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Load integration cards from backend
  const loadList = useCallback(async () => {
    setLoadingList(true);
    try {
      const data = await listIntegrations();
      // Backend may return an array directly or an object with a `content` field (e.g., SpringPage)
      let cardsArray: any[] = [];
      if (Array.isArray(data)) {
        cardsArray = data;
      } else if (data && Array.isArray((data as any).content)) {
        cardsArray = (data as any).content;
      } else if (data && typeof data === 'object') {
        // Fallback: take values that look like integration objects
        cardsArray = Object.values(data).filter(v => typeof v === 'object');
      }
      setCards(cardsArray);

    } catch (err) {
      toastError('Failed to load integrations', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoadingList(false);
    }
  }, [toastError]);

  // Load integration details, logs and sync history
  const loadDetail = useCallback(async (code: string, logPage = 0) => {
    setLoadingDetail(true);
    try {
      const detail = await getIntegration(code);
      setDetails(detail);
      const logsData = await getIntegrationLogs(code, logPage, 20);
      setLogs(logsData.content);
      setLogsPage(logsData.number);
      setLogsTotalPages(logsData.totalPages);
      const history = await getSyncHistory(code);
      setSyncHistory(history);
    } catch (err) {
      toastError('Failed to load integration details', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoadingDetail(false);
    }
  }, [toastError]);

  const selectIntegration = useCallback((code: string) => {
    setSelectedCode(code);
    loadDetail(code, 0);
  }, [loadDetail]);

  const refreshSelected = useCallback(async () => {
    if (!selectedCode) return;
    await loadDetail(selectedCode, logsPage);
    await loadList();
  }, [selectedCode, logsPage, loadDetail, loadList]);

  const toggleEnabled = useCallback(async (code: string, enabled: boolean) => {
    setActionLoading(`toggle-${code}`);
    try {
      const resp = await toggleIntegration(code, { enabled });
      // Update local card list based on response
      setCards(prev =>
        prev.map(c =>
          c.code === code ? { ...c, enabled, connected: enabled ? c.connected : false, health: enabled ? 'healthy' : 'warning' } : c
        )
      );
      success(enabled ? 'Integration enabled' : 'Integration disabled', resp.name || code);
      if (selectedCode === code) await loadDetail(code, 0);
    } catch (err) {
      toastError('Toggle failed', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setActionLoading(null);
    }
  }, [loadDetail, selectedCode, success, toastError]);

  const configure = useCallback(async (code: string, payload: { apiKey?: string; apiSecret?: string; webhookUrl?: string; environment?: string }) => {
    setActionLoading('configure');
    try {
      await configureIntegration(code, {
        apiKey: payload.apiKey?.trim() ?? '',
        apiSecret: payload.apiSecret?.trim() ?? '',
        environment: (payload.environment || 'PRODUCTION').toUpperCase(),
        webhookUrl: payload.webhookUrl ?? undefined,
        settings: {
          clientId: payload.apiKey?.trim() ?? '',
          clientSecret: payload.apiSecret?.trim() ?? '',
          scopes: 'https://www.googleapis.com/auth/calendar.events'
        }
      });
      success('Configuration saved', `${code} integration configured`);
      await loadDetail(code, 0);
      await loadList();
    } catch (err) {
      toastError('Save failed', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setActionLoading(null);
    }
  }, [loadDetail, loadList, success, toastError]);

  const testConnection = useCallback(async (code: string) => {
    setActionLoading('test');
    try {
      const resp = await testIntegration(code);
      success('Test succeeded', resp.status || `Successfully reached ${code} servers`);
      if (selectedCode === code) await loadDetail(code, 0);
    } catch (err) {
      toastError('Connection test failed', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setActionLoading(null);
    }
  }, [loadDetail, selectedCode, success, toastError]);

  const disconnect = useCallback(async (code: string) => {
    setActionLoading('disconnect');
    try {
      await disconnectIntegration(code);
      success('Disconnected', `${code} integration disconnected`);
      await loadList();
      if (selectedCode === code) await loadDetail(code, 0);
    } catch (err) {
      toastError('Disconnect failed', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setActionLoading(null);
    }
  }, [loadDetail, selectedCode, success, toastError, loadList]);

  const oauthConnect = useCallback(async (code: string) => {
    setActionLoading('oauth');
    try {
      await startOAuthConnect(code);
      // The backend should handle updating connection status; refresh list & details
      await loadList();
      await loadDetail(code, 0);
    } catch (err) {
      toastError('OAuth failed', err instanceof Error ? err.message : 'Failed to initiate OAuth flow');
    } finally {
      setActionLoading(null);
    }
  }, [toastError, loadDetail, loadList]);

// Zapier logs state
  const [zapierLogs, setZapierLogs] = useState<unknown[]>([]);
  const [zapierLogsPage, setZapierLogsPage] = useState(0);
  const [zapierLogsTotalPages, setZapierLogsTotalPages] = useState(0);

  const loadZapierLogs = useCallback(async (page = 0, size = 5) => {
    setActionLoading('zapier-logs');
    try {
      const res = await getZapierLogs(page, size);
      const json = await res.json();
      if (!json.success) throw new Error(json.message);
      setZapierLogs(json.data);
      // Assuming response includes pagination fields if needed
      setZapierLogsPage(page);
      setZapierLogsTotalPages(json.totalPages ?? 0);
    } catch (err) {
      toastError('Failed to load Zapier logs', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setActionLoading(null);
    }
  }, [toastError]);

  // Initial load of integration cards
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadList();
  }, [loadList]);

  // Handle OAuth redirect after successful connection
  useEffect(() => {
    const connected = searchParams.get('connected');
    if (!connected) return;
    const code = connected.toUpperCase();
    success('Integration connected', `${connected} is now connected`);
    setSearchParams({}, { replace: true });
    // Refresh card list and details for the connected integration
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCards(prev =>
      prev.map(c => (c.code === code ? { ...c, connected: true, enabled: true, health: 'healthy', lastSynced: new Date().toISOString() } : c))
    );
    setSelectedCode(code);
    loadDetail(code, 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    cards,
    selectedCode,
    details,
    logs,
    syncHistory,
    logsPage,
    logsTotalPages,
    loadingList,
    loadingDetail,
    actionLoading,
    loadList,
    selectIntegration,
    refreshSelected,
    toggleEnabled,
    configure,
    testConnection,
    disconnect,
    oauthConnect,
    loadZapierLogs,
    zapierLogs,
    zapierLogsPage,
    zapierLogsTotalPages,
  };
}


