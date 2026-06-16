/**
 * Utility to parse and store UTM parameters and marketing sources.
 */

export const getUTMParams = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const params = {
        source: urlParams.get('source') || urlParams.get('utm_source') || undefined,
        utmSource: urlParams.get('utm_source') || undefined,
        utmMedium: urlParams.get('utm_medium') || undefined,
        utmCampaign: urlParams.get('utm_campaign') || undefined,
    };

    // Store in local storage if source is present
    if (params.source) {
        localStorage.setItem('marketing_source', params.source);
        if (params.utmSource) localStorage.setItem('utm_source', params.utmSource);
        if (params.utmMedium) localStorage.setItem('utm_medium', params.utmMedium);
        if (params.utmCampaign) localStorage.setItem('utm_campaign', params.utmCampaign);
    }

    return params;
};

export const getStoredMarketingData = () => {
    return {
        source: localStorage.getItem('marketing_source') || 'DIRECT',
        utmSource: localStorage.getItem('utm_source') || undefined,
        utmMedium: localStorage.getItem('utm_medium') || undefined,
        utmCampaign: localStorage.getItem('utm_campaign') || undefined,
    };
};

export const generateSessionId = (): string => {
    let sessionId = sessionStorage.getItem('tracking_session_id');
    if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).substring(2, 11);
        sessionStorage.setItem('tracking_session_id', sessionId);
    }
    return sessionId;
};
