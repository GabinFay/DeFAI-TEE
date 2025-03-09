import { Chain, flare } from 'wagmi/chains';

// Create a custom Flare chain by extending the existing one
export const flareWithIcon = {
  ...flare,
  // Add the icon URL - using a relative path to a local asset
  // This assumes you'll add the icon to your public folder
  iconUrl: '/flare-icon.png',
} as const; 