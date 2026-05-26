'use client';

import * as React from 'react';
import * as ReactHookForm from 'react-hook-form';
import type { ZodType } from 'zod';

import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface FormFieldProps {
  name: string;
  label: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

interface FormProps<T extends ReactHookForm.FieldValues> {
  form: ReactHookForm.UseFormReturn<T>;
  onSubmit: (data: T) => void;
  className?: string;
  children?: React.ReactNode;
}

export function useForm<T extends ReactHookForm.FieldValues>(schema: ZodType<T>) {
  return ReactHookForm.useForm<T>({
    resolver: (values) => {
      const result = schema.safeParse(values);
      if (result.success) {
        return { values: result.data, errors: {} };
      }
      const errors: Record<string, { message: string }> = {};
      result.error.errors.forEach((err) => {
        const path = err.path.join('.');
        errors[path] = { message: err.message };
      });
      return { values: {} as T, errors };
    },
    defaultValues: {} as T,
  });
}

export function FormField<T extends ReactHookForm.FieldValues>({
  form,
  name,
  label,
  placeholder,
  type = 'text',
  disabled,
  required,
  className,
}: FormFieldProps & { form: ReactHookForm.UseFormReturn<T> }) {
  const { register, formState: { errors } } = form;
  const error = errors[name]?.message as string | undefined;

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name}>
        {label}
        {required && <span className="text-destructive"> *</span>}
      </Label>
      <Input
        id={name}
        type={type}
        placeholder={placeholder}
        disabled={disabled}
        {...register(name)}
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}

export function Form<T extends ReactHookForm.FieldValues>({
  form,
  onSubmit,
  className,
  children,
}: FormProps<T>) {
  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className={className}>
      {children}
    </form>
  );
}