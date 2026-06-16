import React from 'react';
import { useToast } from '@/hooks/use-toast';
import { integrationApi } from '@/services/integrationApi';

const ZoomConnectButton: React.FC = () => {
  const { toast } = useToast();

  const handleConnect = async () => {
    try {
      const res = await integrationApi.connectZoom();
      if (res.ok) {
        const data = await res.json();
        window.location.href = data.authUrl;
      } else {
        const err = await res.text();
        throw new Error(err || 'Failed to connect');
      }
    } catch (err) {
      toast({
        title: 'Zoom connection failed',
        description: (err as Error).message,
        variant: 'destructive',
      });
    }
  };

  return (
    <button
      className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition"
      onClick={handleConnect}
    >
      Connect Zoom
    </button>
  );
};

export default ZoomConnectButton;


