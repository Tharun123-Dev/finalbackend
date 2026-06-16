import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { integrationApi } from '@/services/integrationApi';

const ZoomSuccessPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [message, setMessage] = useState("Connecting to Zoom...");

  useEffect(() => {
    const code = searchParams.get('code');

    if (code) {
      integrationApi.zoomCallback(code)
        .then(async (res) => {
          if (!res.ok) throw new Error("Failed");
          setMessage("✅ Zoom Connected Successfully!");
          setTimeout(() => navigate('/integrations'), 1500);
        })
        .catch(() => {
          setMessage("❌ Zoom Connection Failed. Please try again.");
          setTimeout(() => navigate('/integrations'), 3000);
        });
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMessage("❌ No authorization code found.");
      setTimeout(() => navigate('/integrations'), 3000);
    }
  }, [searchParams, navigate]);

  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <div className="bg-card dark:bg-slate-800 p-8 rounded-lg shadow-md max-w-md w-full text-center">
        <h2 className="text-2xl font-bold text-foreground mb-4">{message}</h2>
        <button
          onClick={() => navigate('/integrations')}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition mt-4"
        >
          Return to Integrations
        </button>
      </div>
    </div>
  );
};

export default ZoomSuccessPage;


