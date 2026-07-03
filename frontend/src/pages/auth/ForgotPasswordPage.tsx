import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { zodResolver } from '@/lib/zodResolver';
import { AlertCircle, ArrowLeft, CheckCircle, Loader2 } from 'lucide-react';

const forgotPasswordSchema = z.object({
  email: z.string().min(1, 'Email address is required').email('Please enter a valid email address'),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const { forgotPassword, error, clearError } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormValues) => {
    setLoading(true);
    clearError();
    try {
      const result = await forgotPassword(data.email);
      setSuccess(true);
      if (result.token) {
        setResetToken(result.token);
      }
    } catch (err) {
      // Error is stored globally
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Card className="border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 shadow-lg text-center">
        <CardHeader className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400">
            <CheckCircle className="h-6 w-6" />
          </div>
          <CardTitle className="mt-4">Verify Inbox</CardTitle>
          <CardDescription>
            We have sent password recovery instructions to your email address.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {resetToken && (
            <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4 dark:border-blue-900/30 dark:bg-blue-950/20 text-center animate-in fade-in duration-300">
              <p className="text-xs font-semibold text-blue-600 dark:text-blue-400">
                Local Testing Helper:
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                Since we are in database-free/mock mode, click below to proceed directly to reset password:
              </p>
              <Button asChild className="w-full mt-3 h-9 text-xs" variant="outline">
                <Link to={`/reset-password?token=${resetToken}`}>
                  Simulate Password Reset Link
                </Link>
              </Button>
            </div>
          )}
          
          <Button asChild className="w-full h-11" variant="ghost">
            <Link to="/login" onClick={clearError}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Sign In
            </Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 shadow-lg">
      <CardHeader>
        <CardTitle>Recover Password</CardTitle>
        <CardDescription>
          Enter your registered email address to request a secure password recovery token.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {error && (
            <div className="flex items-start gap-2.5 rounded-xl bg-destructive/10 p-4 text-sm text-destructive dark:bg-destructive/20 animate-in fade-in duration-200">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Request failed</p>
                <p className="text-xs opacity-90 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input
              id="email"
              type="email"
              placeholder="admin@aip.com"
              error={!!errors.email}
              {...register('email')}
              disabled={loading}
              autoComplete="email"
            />
            {errors.email && (
              <p className="text-xs text-destructive font-medium animate-in fade-in duration-150">{errors.email.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full h-11" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending Token...
              </>
            ) : (
              'Send Recovery Link'
            )}
          </Button>

          <Button asChild className="w-full h-11" variant="ghost">
            <Link to="/login" onClick={clearError}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Sign In
            </Link>
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
