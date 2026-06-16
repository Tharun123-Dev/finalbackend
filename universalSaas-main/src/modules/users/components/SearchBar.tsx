// src/modules/users/components/SearchBar.tsx
import React, { useState } from 'react';

interface SearchBarProps {
  placeholder?: string;
  onSearch: (value: string) => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({ placeholder = 'Search...', onSearch }) => {
  const [value, setValue] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearch(value);
    }
  };

  return (
    <div className="flex items-center mb-4">
      <input
        type="text"
        className="flex-1 rounded-md border border-gray-300 dark:border-gray-600 bg-card dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        type="button"
        className="ml-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 text-sm"
        onClick={() => onSearch(value)}
      >
        Search
      </button>
    </div>
  );
};

export default SearchBar;


