export type VerifiedReview = {
  quote: string;
  name: string;
  role: string;
  sourceUrl?: string;
};

// Publish only feedback that can be attributed to a real user and is approved for display.
export const verifiedReviews: VerifiedReview[] = [];
