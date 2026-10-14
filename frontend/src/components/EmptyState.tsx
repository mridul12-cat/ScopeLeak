import React from 'react';

interface Props {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<Props> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-zinc-950 rounded-xl border border-dashed border-zinc-800">
      {icon && <div className="p-3 mb-4 text-zinc-400 bg-zinc-900 border border-zinc-800 rounded-full">{icon}</div>}
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <p className="max-w-md mt-1 text-sm text-zinc-400">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-5 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
