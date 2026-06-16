import React from 'react';
import { useNavigate } from 'react-router-dom';

const GoogleErrorPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[60vh] flex items-center justify-center bg-gray-50 dark:bg-slate-900 rounded-lg">
      <div className="text-center p-10 bg-card dark:bg-slate-800 rounded-2xl shadow-xl">
        <h2 className="text-3xl text-red-600 mb-4">❌ Connection Failed</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6">Failed to connect to Google Calendar.</p>
        <button
          onClick={() => navigate('/integrations')}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          Return to Integrations
        </button>
      </div>
    </div>
  );
};

export default GoogleErrorPage;


