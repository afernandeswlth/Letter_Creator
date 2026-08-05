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

const FORM_LABELS: Record<string, string> = { approval: 'Formal Approval', commencement: 'Commencement' }

/** Subject + HTML body for a form-driven letter (e.g. Formal Approval). */
export function formEmail(
  letterType: string,
  brandId: string,
  values: Record<string, string>,
): { subject: string; html: string } {
  const brand = BRANDS[brandId] ?? BRANDS.wlth
  const label = FORM_LABELS[letterType] ?? 'Letter'
  // For a commencement letter the "borrower" in the subject is the customer(s),
  // not the builder (the builder is only greeted in the body).
  const who = letterType === 'commencement'
    ? (values.customerNames || '')
    : (values.borrowers || values.recipientName || '')
  const first = stripTitle(who).split(/\s+/)[0] || 'there'
  const acct = values.loanAccountNumber || values.applicationNumber || ''
  let subject = `${brand.label} ${label} Letter`
  if (who) subject += `: ${stripTitle(who)}`
  if (acct) subject += ` - ${acct}`

  let body: string
  if (letterType === 'commencement') {
    const builder = (values.builderName || '').trim() || 'there'
    body = `
    <p>Hi ${builder},</p>
    <p>Welcome to the ${brand.label} Construction Journey!</p>
    <p>We want to let you know that we can start releasing progress payments for our mutual customers.
       You can find the Commencement Letter for the above clients attached to this email for your
       attention and action. This means you can now commence the construction or renovations.</p>
    <p>Also attached are our Progress Payment Guidelines, which outline the requirements for a drawdown
       request. All invoices must be signed by all borrowers; digital signatures are accepted. Kindly
       send all construction drawdown requests and supporting documents to
       <a href="mailto:construction@wlth.com">construction@wlth.com</a></p>
    <p>Please note, we require a progress valuation at every stage of the construction. These reports
       can take up to 5 business days to be compiled by the valuation firm. We encourage you to take
       this into consideration when submitting a request.</p>
    <p>Once we have all the supporting documents, payment is usually posted within 2-3 business days.</p>
    <p>If you have any questions or concerns along the way, please do not hesitate to reach out.</p>
    <p>Kind regards,<br/>${brand.label}</p>`
  } else {
    body = `
    <p>Hi ${first},</p>
    <p>Please find attached your ${brand.label} ${label} letter.</p>
    <p>If you have any questions, please reach out to us ${brand.contactShort}</p>
    <p>Warm regards,<br/>${brand.team}</p>`
  }
  const signature = SIGNATURE_HTML ? `<br/><br/>${SIGNATURE_HTML}` : ''
  const html = `<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1e2430; line-height: 1.5;">${body}${signature}</div>`.trim()
  return { subject, html }
}
