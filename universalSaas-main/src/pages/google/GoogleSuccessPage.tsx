import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const GoogleSuccessPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'connecting' | 'success' | 'failed'>('connecting');

  useEffect(() => {
    const error = searchParams.get('error');

    if (error) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStatus('failed');
      return;
    }

    // Since backend already handled the callback and redirected here,
    // we just show success and refresh integration status
    setStatus('success');

    // Optional: You can call a status API to confirm
    const timer = setTimeout(() => {
      navigate('/integrations');
    }, 1800);
    
    return () => clearTimeout(timer);
  }, [searchParams, navigate]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center bg-gray-50 dark:bg-slate-900 rounded-lg">
      <div className="text-center p-10 bg-card dark:bg-slate-800 rounded-2xl shadow-xl">
        {status === 'connecting' && <h2 className="text-2xl text-foreground">Connecting Google Account...</h2>}
        {status === 'success' && (
          <>
            <h2 className="text-3xl text-green-600 mb-4">✅ Successfully Connected!</h2>
            <p className="text-gray-600 dark:text-gray-300">Google Calendar is now linked.</p>
          </>
        )}
        {status === 'failed' && <h2 className="text-3xl text-red-600">❌ Connection Failed</h2>}
      </div>
    </div>
  );
};

export default GoogleSuccessPage;


