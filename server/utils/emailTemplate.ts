import { SIGNATURE_HTML } from './signature'

interface BrandEmail {
  name: string
  phone: string
}

const BRANDS: Record<string, BrandEmail> = {
  wlth: { name: 'WLTH', phone: '13 WLTH' },
  mma: { name: 'Mortgage Mart', phone: '1300 650 200' },
}

/** Subject + HTML body for the borrower welcome email. */
export function welcomeEmail(
  brandId: string,
  recipientName: string,
  template: 'Offset' | 'Standard',
): { subject: string; html: string } {
  const brand = BRANDS[brandId] ?? BRANDS.wlth
  const first = recipientName.replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '').split(/\s+/)[0]

  const offsetLine =
    template === 'Offset'
      ? `<p>Your loan is linked to an offset account. Any funds you keep in that account reduce the
         interest charged on your loan — your offset account details are in the attached letter.</p>`
      : ''

  const signature = SIGNATURE_HTML ? `<br/><br/>${SIGNATURE_HTML}` : ''
  const html = `
    <div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1e2430; line-height: 1.5;">
      <p>Dear ${first},</p>
      <p>Welcome, and congratulations on the settlement of your new home loan with ${brand.name}.</p>
      <p>Please find your welcome letter attached. It contains your loan account details and everything
         you need to get started, including how to access your account online.</p>
      ${offsetLine}
      <p>If you have any questions, simply reply to this email or call us on ${brand.phone}.</p>
      <p>Kind regards,<br/>The ${brand.name} Team</p>
      ${signature}
    </div>`.trim()

  return {
    subject: `Welcome to your new home loan with ${brand.name}`,
    html,
  }
}
