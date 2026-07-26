import { SIGNATURE_HTML } from './signature'

interface BrandEmail {
  label: string // "WLTH" / "Mortgage Mart"
  letterName: string // "WLTH Welcome Letter" / "Mortgage Mart Welcome Letter"
  loanDetails: string // "new Home Loan details" / "new Loan details"
  contactShort: string // contact sentence tail for the short body
  contactLong: string // contact sentence tail for the long body
  team: string // sign-off
}

const BRANDS: Record<string, BrandEmail> = {
  wlth: {
    label: 'WLTH',
    letterName: 'WLTH Welcome Letter',
    loanDetails: 'new Home Loan details',
    contactShort: 'on 13WLTH thats 13 95 84, email hello@wlth.com or contact your Mortgage Broker/ Lending Specialist.',
    contactLong: 'on 13WLTH, email hello@wlth.com or contact your Mortgage Broker/ Lending Specialist.',
    team: 'The WLTH Team',
  },
  mma: {
    label: 'Mortgage Mart',
    letterName: 'Mortgage Mart Welcome Letter',
    loanDetails: 'new Loan details',
    contactShort: 'on 1300 650 200, email hello@wlth.com, or contact your Mortgage Broker.',
    contactLong: 'on 1300 650 200, email hello@wlth.com, or contact your Mortgage Broker.',
    team: 'The Mortgage Mart Team',
  },
}

function stripTitle(name: string) {
  return name.replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '')
}

export interface EmailInput {
  brandId: string
  borrowerName: string // recipient of this letter
  offset: 'yes' | 'no' // "Account linked to Offset?" answer
  isTrust: boolean
  trustName: string // entity/trust name (used in subject when isTrust)
  accountNumber: string // loan account number
}

/** Subject + HTML body for the borrower welcome email. */
export function welcomeEmail(input: EmailInput): { subject: string; html: string } {
  const brand = BRANDS[input.brandId] ?? BRANDS.wlth
  const first = stripTitle(input.borrowerName).split(/\s+/)[0]

  const subjectName = input.isTrust ? input.trustName : stripTitle(input.borrowerName)
  const subject = `${brand.label} Welcome Letter: ${subjectName} - ${input.accountNumber}`

  const intro = `
    <p>Hi ${first},</p>
    <p>Congratulations again on your settlement!</p>
    <p>Please find attached your ${brand.letterName}. This includes your repayment information &amp;
       confirmation of your ${brand.loanDetails} including loan account number, loan repayment date and
       direct debit and credit information.</p>`

  // Long body (offset = no): linking the SMSF Cash Management Account.
  const linkingBlock = `
    <p>We note that you have not yet linked your SMSF Cash Management Account to your Offset Account.</p>
    <p>Linking an account enables the Redraw function, allowing you to transfer funds from your offset
       account directly to your linked external account. This is the only way to withdraw funds from your
       SMSF Offset Account other than BPAY, and it's possible to transfer up to $250,000 at a time!</p>
    <p>To link an external account with your offset account, simply complete and return the attached
       Linked Account Nomination Form.</p>
    <p>To increase your Redraw limits past the default, please contact us on 13 95 84. 2 Factor
       Authentication must be enabled to increase your daily limit.</p>
    <p><strong>Redraw Daily Limits:</strong></p>
    <p style="margin:0">Default: $10,000.00<br/>Default with 2FA Enabled: $50,000.00<br/>Maximum: $250,000.00</p>
    <p><strong>Important points when linking your account:</strong></p>
    <ul>
      <li>If you're linking an offset account, please enter your offset account number in the
          'Loan Account No(s)' section of the form.</li>
      <li>All borrowers/guarantors will need to sign the forms. If signing digitally, please include the
          electronic certificate of completion/audit trail.</li>
      <li>Return the completed form/s by replying to this email, along with a bank account statement
          (or bank letter) for your nominated account. This statement must clearly show the SMSF name,
          bank account details, and the bank's logo. It should be no older than six months.</li>
    </ul>`

  const contact = input.offset === 'no' ? brand.contactLong : brand.contactShort
  const body = `
    ${intro}
    ${input.offset === 'no' ? linkingBlock : ''}
    <p>If you have any questions, please reach out to us ${contact}</p>
    <p>Warm regards,<br/>${brand.team}</p>`

  const signature = SIGNATURE_HTML ? `<br/><br/>${SIGNATURE_HTML}` : ''
  const html = `
    <div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1e2430; line-height: 1.5;">
      ${body}
      ${signature}
    </div>`.trim()

  return { subject, html }
}
