import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { Button } from "../components/ui/button";
import { ApiError } from "../lib/api/http";
import { signup } from "../services/auth";

const signupSchema = z.object({
  organizationName: z.string().min(1, "Enter your organization's name"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(12, "Password must be at least 12 characters"),
});

type SignupFormValues = z.infer<typeof signupSchema>;

function friendlyError(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as {
        detail?: string | { code?: string; reason?: string };
      };
      if (parsed.detail === "REGISTER_USER_ALREADY_EXISTS") {
        return "An account with that email already exists.";
      }
      if (typeof parsed.detail === "object" && parsed.detail?.reason) {
        return parsed.detail.reason;
      }
    } catch {
      // fall through to the generic message below
    }
  }
  return "Something went wrong creating your account — please try again.";
}

/**
 * Public signup always creates a brand-new Organization with this user as
 * its Admin (see the backend's UserManager.create) — joining an existing
 * org happens via the Team page's invite flow instead, not here.
 */
export function SignupPage() {
  const [formError, setFormError] = useState<string | null>(null);
  const [signedUp, setSignedUp] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({ resolver: zodResolver(signupSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await signup(values);
      setSignedUp(true);
    } catch (error) {
      setFormError(friendlyError(error));
    }
  });

  if (signedUp) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg px-4">
        <div className="w-full max-w-sm rounded-md border border-divider bg-surface p-6 text-center shadow-md">
          <div className="font-heading text-xl font-semibold">Check your verification link</div>
          <p className="mt-2 text-sm text-text-muted">
            Your workspace was created. No email provider is configured in local dev yet, so ask
            whoever runs the API server to check its logs for your verification link
            (<code>auth.verification_link</code>) before you can sign in.
          </p>
          <Link to="/login" className="mt-4 inline-block text-sm text-accent underline">
            Go to sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm rounded-md border border-divider bg-surface p-6 shadow-md">
        <div className="mb-6 text-center">
          <div className="font-heading text-2xl font-semibold">Afridock</div>
          <div className="text-sm text-text-muted">Create your workspace</div>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="organizationName"
              className="mb-1 block text-xs font-medium text-text-muted"
            >
              Organization name
            </label>
            <input
              id="organizationName"
              {...register("organizationName")}
              className="w-full rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text"
            />
            {errors.organizationName && (
              <p className="mt-1 text-xs text-red-600">{errors.organizationName.message}</p>
            )}
          </div>
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
            Create workspace
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-text-muted">
          Already have an account?{" "}
          <Link to="/login" className="text-accent underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
