// src/modules/users/components/ConfirmDialog.tsx
import React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ open, title, message, onConfirm, onCancel }) => {
  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onCancel(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-1/2 left-1/2 w-96 max-w-full -translate-x-1/2 -translate-y-1/2 rounded-lg bg-card dark:bg-gray-800 p-6 shadow-lg outline-none">
          <Dialog.Title className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
            {title}
          </Dialog.Title>
          <Dialog.Description className="text-sm text-gray-600 dark:text-gray-300 mb-6">
            {message}
          </Dialog.Description>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onConfirm}
              className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white"
            >
              Confirm
            </button>
          </div>
          <Dialog.Close asChild>
            <button className="absolute top-3 right-3 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
              <XMarkIcon className="h-5 w-5" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default ConfirmDialog;


