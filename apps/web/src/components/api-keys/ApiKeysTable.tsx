import type { ApiKey } from "../../services/apiKeys";
import { RevokeApiKeyAlertDialog } from "./RevokeApiKeyAlertDialog";

type ApiKeysTableProps = {
  apiKeys: ApiKey[];
};

export function ApiKeysTable({ apiKeys }: ApiKeysTableProps) {
  return (
    <table className="w-full text-left text-sm">
      <thead className="text-text-subtle">
        <tr>
          <th className="pb-2 font-medium">Name</th>
          <th className="pb-2 font-medium">Key</th>
          <th className="pb-2 font-medium">Created</th>
          <th className="pb-2 font-medium">Last used</th>
          <th className="pb-2 font-medium">Status</th>
          <th className="pb-2 font-medium" />
        </tr>
      </thead>
      <tbody className="divide-y divide-divider">
        {apiKeys.map((apiKey) => (
          <tr key={apiKey.id}>
            <td className="py-2.5 font-heading text-[15px]">{apiKey.name}</td>
            <td className="py-2.5 font-mono text-xs text-text-muted">{apiKey.keyPrefix}…</td>
            <td className="py-2.5 text-xs text-text-muted">
              {new Date(apiKey.createdAt).toLocaleDateString()}
            </td>
            <td className="py-2.5 text-xs text-text-muted">
              {apiKey.lastUsedAt ? new Date(apiKey.lastUsedAt).toLocaleDateString() : "Never"}
            </td>
            <td className="py-2.5 text-xs">
              {apiKey.revokedAt ? (
                <span className="text-red-600">Revoked</span>
              ) : (
                <span className="text-text-muted">Active</span>
              )}
            </td>
            <td className="py-2.5 text-right">
              {!apiKey.revokedAt && (
                <RevokeApiKeyAlertDialog keyId={apiKey.id} keyName={apiKey.name} />
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
