import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { Button } from "../components/ui/button";
import { ApiError } from "../lib/api/http";
import { login } from "../services/auth";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Enter your password"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

function friendlyError(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail === "LOGIN_USER_NOT_VERIFIED") {
        return "Your account hasn't been verified yet. Ask an admin to check the API server logs for your verification link (no email provider is configured in local dev).";
      }
      if (parsed.detail === "LOGIN_BAD_CREDENTIALS") {
        return "Incorrect email or password.";
      }
    } catch {
      // fall through to the generic message below
    }
  }
  return "Something went wrong signing in — please try again.";
}

export function LoginPage() {
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await login(values);
      window.location.href = "/chat";
    } catch (error) {
      setFormError(friendlyError(error));
    }
  });

  return (
    <div className="flex h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm rounded-md border border-divider bg-surface p-6 shadow-md">
        <div className="mb-6 text-center">
          <div className="font-heading text-2xl font-semibold">Afridock</div>
          <div className="text-sm text-text-muted">Sign in to your workspace</div>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-1 block text-xs font-medium text-text-muted">
              Email
            </label>
            <input
              id="email"
              type="email"
              {...register("email")}
              className="w-full rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text"
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-xs font-medium text-text-muted">
              Password
            </label>
            <input
              id="password"
              type="password"
              {...register("password")}
              className="w-full rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <Button type="submit" variant="primary" className="w-full" disabled={isSubmitting}>
            Sign in
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-text-muted">
          No account?{" "}
          <Link to="/signup" className="text-accent underline">
            Create a workspace
          </Link>
        </p>
      </div>
    </div>
  );
}
