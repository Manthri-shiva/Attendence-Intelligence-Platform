import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { zodResolver } from '@/lib/zodResolver';
import { AlertCircle, ArrowLeft, CheckCircle, Loader2 } from 'lucide-react';

const resetPasswordSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters long'),
    confirmPassword: z.string().min(8, 'Confirm password must be at least 8 characters long'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const { resetPassword, error, clearError } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormValues) => {
    if (!token) return;
    setLoading(true);
    clearError();
    try {
      await resetPassword(token, data.password);
      setSuccess(true);
    } catch (err) {
      // Error is caught globally
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <Card className="border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 shadow-lg text-center">
        <CardHeader className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive dark:bg-destructive/20">
            <AlertCircle className="h-6 w-6" />
          </div>
          <CardTitle className="mt-4">Invalid Recovery Link</CardTitle>
          <CardDescription>
            The security recovery token is missing from the URL. Please verify your recovery link.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full h-11" variant="ghost">
            <Link to="/forgot-password" onClick={clearError}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Request New Link
            </Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (success) {
    return (
      <Card className="border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 shadow-lg text-center">
        <CardHeader className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400">
            <CheckCircle className="h-6 w-6" />
          </div>
          <CardTitle className="mt-4">Reset Complete</CardTitle>
          <CardDescription>
            Your account password has been successfully updated.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full h-11">
            <Link to="/login" onClick={clearError}>
              Proceed to Sign In
            </Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 shadow-lg">
      <CardHeader>
        <CardTitle>Define New Password</CardTitle>
        <CardDescription>
          Choose a secure, complex password of at least 8 characters.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {error && (
            <div className="flex items-start gap-2.5 rounded-xl bg-destructive/10 p-4 text-sm text-destructive dark:bg-destructive/20 animate-in fade-in duration-200">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Reset failed</p>
                <p className="text-xs opacity-90 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              error={!!errors.password}
              {...register('password')}
              disabled={loading}
              autoComplete="new-password"
            />
            {errors.password && (
              <p className="text-xs text-destructive font-medium animate-in fade-in duration-150">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              error={!!errors.confirmPassword}
              {...register('confirmPassword')}
              disabled={loading}
              autoComplete="new-password"
            />
            {errors.confirmPassword && (
              <p className="text-xs text-destructive font-medium animate-in fade-in duration-150">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full h-11" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating Password...
              </>
            ) : (
              'Update Password'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
