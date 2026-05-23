import { describe, expect, it } from 'vitest';

import { reducedMotionTransition, sidebarLayoutTransition } from '../../design-system/motion';

describe('motion reduced accessibility', () => {
  it('uses instant transition when reduced motion preferred', () => {
    expect(sidebarLayoutTransition(true)).toEqual(reducedMotionTransition);
  });

  it('uses spring transition when motion allowed', () => {
    expect(sidebarLayoutTransition(false)).toHaveProperty('type', 'spring');
  });
});
