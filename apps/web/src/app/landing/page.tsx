'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { LandingPage } from '@/components/landing/landing-page';

export default function Landing() {
  return <LandingPage />;
}