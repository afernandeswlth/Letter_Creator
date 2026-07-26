import type { Brand, BrandId } from '~/types'

export const BRANDS: Record<BrandId, Brand> = {
  'mortgage-mart': {
    id: 'mortgage-mart',
    name: 'Mortgage Mart',
    logo: '/logos/mortgage-mart.png',
    fromEmail: 'welcome@mortgagemart.com',
    driveFolder: 'Welcome Letters / Mortgage Mart',
    accent: '#2563eb',
  },
  wlth: {
    id: 'wlth',
    name: 'WLTH',
    logo: '/logos/wlth.png',
    fromEmail: 'welcome@wlth.com',
    driveFolder: 'Welcome Letters / WLTH',
    accent: '#0f766e',
  },
}

export const BRAND_LIST: Brand[] = Object.values(BRANDS)
