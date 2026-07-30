import { ApiError, http } from "../lib/api/http";
import type { Role } from "../lib/permissions";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

export type CurrentUser = {
  id: string;
  email: string;
  orgId: string;
  role: Role;
  displayName: string | null;
};

type UserReadResponse = {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  org_id: string;
  role: Role;
  display_name: string | null;
};

function toCurrentUser(body: UserReadResponse): CurrentUser {
  return {
    id: body.id,
    email: body.email,
    orgId: body.org_id,
    role: body.role,
    displayName: body.display_name,
  };
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  return toCurrentUser(await http.get<UserReadResponse>("/users/me"));
}

export async function signup(input: {
  email: string;
  password: string;
  organizationName: string;
}): Promise<CurrentUser> {
  const body = await http.post<UserReadResponse>("/auth/register", {
    email: input.email,
    password: input.password,
    organization_name: input.organizationName,
  });
  return toCurrentUser(body);
}

/**
 * Not `http.post` — fastapi-users' login route expects
 * `application/x-www-form-urlencoded` (OAuth2PasswordRequestForm), not
 * JSON, unlike every other Afridock endpoint.
 */
export async function login(input: { email: string; password: string }): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/cookie/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include",
    body: new URLSearchParams({ username: input.email, password: input.password }),
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(response.status, body || response.statusText);
  }
}

export async function logout(): Promise<void> {
  await http.post<void>("/auth/cookie/logout");
}

/**
 * Local-dev-only convenience (see api/routes/auth.py's dev_verification_token
 * — 404s outside API_ENV=local): mints a verification token directly instead
 * of requiring log access to the API server. Returns null on 404 so callers
 * can fall back to the "check your email" copy for any real deployment.
 */
export async function requestDevVerificationToken(email: string): Promise<string | null> {
  try {
    const body = await http.post<{ token: string }>("/auth/dev/verification-token", { email });
    return body.token;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function verifyEmail(token: string): Promise<void> {
  await http.post<void>("/auth/verify", { token });
}
