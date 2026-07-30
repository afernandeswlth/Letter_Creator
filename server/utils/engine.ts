import { execFile } from 'node:child_process'
import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const ENGINE = join(process.cwd(), 'engine', 'cli.py')

export interface Party {
  name: string
  role: 'Entity' | 'Member'
  customerNumber: string | null
  isEntity: boolean
  loanFacilityNumber?: string
  text?: string
}

export interface EngineResult {
  loanType: string
  smsfNumber?: string | null
  parties: Party[]
}

interface UploadedFile {
  filename: string
  data: Buffer
}

/**
 * Run the Python letter engine against a set of uploaded funder .docx files.
 * `command` is "parse" (structure only) or "render" (full letter text).
 */
async function withFiles<T>(
  files: UploadedFile[],
  fn: (paths: string[]) => Promise<T>,
): Promise<T> {
  const dir = await mkdtemp(join(tmpdir(), 'wlg-'))
  try {
    const paths: string[] = []
    for (const [i, f] of files.entries()) {
      const p = join(dir, `funder_${i}_${f.filename.replace(/[^\w.-]/g, '_')}`)
      await writeFile(p, f.data)
      paths.push(p)
    }
    return await fn(paths)
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

const CWD = () => join(process.cwd(), 'engine')

export async function runEngine(
  command: 'parse' | 'render',
  files: UploadedFile[],
  opts: { brand?: string; ddBsb?: string; ddAccount?: string } = {},
): Promise<EngineResult> {
  return withFiles(files, (paths) => {
    const args = [ENGINE, command]
    if (command === 'render') args.push(opts.brand ?? 'wlth', opts.ddBsb ?? '', opts.ddAccount ?? '')
    args.push(...paths)
    return new Promise<EngineResult>((resolve, reject) => {
      execFile('python3', args, { cwd: CWD() }, (err, out, errOut) => {
        if (err) reject(new Error(errOut || err.message))
        else resolve(JSON.parse(out) as EngineResult)
      })
    })
  })
}

/** Rasterise one party's PDF to page images (data URLs) for on-screen preview. */
export async function runEnginePreview(
  files: UploadedFile[],
  opts: { brand: string; ddBsb: string; ddAccount: string; partyIndex: number },
): Promise<{ pages: string[] }> {
  return withFiles(files, (paths) => {
    const args = [ENGINE, 'preview', opts.brand, opts.ddBsb, opts.ddAccount, String(opts.partyIndex), ...paths]
    return new Promise<{ pages: string[] }>((resolve, reject) => {
      execFile(
        'python3', args,
        { cwd: CWD(), maxBuffer: 64 * 1024 * 1024 },
        (err, out, errOut) => {
          if (err) reject(new Error(errOut || err.message))
          else resolve(JSON.parse(out) as { pages: string[] })
        },
      )
    })
  })
}

/** Render one party's branded PDF; returns the raw PDF bytes. */
export async function runEnginePdf(
  files: UploadedFile[],
  opts: { brand: string; ddBsb: string; ddAccount: string; partyIndex: number },
): Promise<Buffer> {
  return withFiles(files, (paths) => {
    const args = [ENGINE, 'pdf', opts.brand, opts.ddBsb, opts.ddAccount, String(opts.partyIndex), ...paths]
    return new Promise<Buffer>((resolve, reject) => {
      execFile(
        'python3', args,
        { cwd: CWD(), encoding: 'buffer', maxBuffer: 32 * 1024 * 1024 },
        (err, out, errOut) => {
          if (err) reject(new Error(errOut?.toString() || err.message))
          else resolve(out as Buffer)
        },
      )
    })
  })
}

/** Extract field values from an uploaded source doc (e.g. a Schedule 4). */
export async function runEngineFormParse(
  letterType: string,
  brand: string,
  file: UploadedFile,
): Promise<{ values: Record<string, string> }> {
  return withFiles([file], (paths) => {
    const args = [ENGINE, 'form-parse', letterType, brand, paths[0]]
    return new Promise<{ values: Record<string, string> }>((resolve, reject) => {
      execFile('python3', args, { cwd: CWD(), maxBuffer: 16 * 1024 * 1024 }, (err, out, errOut) => {
        if (err) reject(new Error(errOut || err.message))
        else resolve(JSON.parse(out) as { values: Record<string, string> })
      })
    })
  })
}

/** Render a form-driven letter type (e.g. Formal Approval) to PDF bytes. */
export async function runEngineFormPdf(
  letterType: string,
  brand: string,
  values: Record<string, unknown>,
): Promise<Buffer> {
  const args = [ENGINE, 'form-pdf', letterType, brand, JSON.stringify(values)]
  return new Promise<Buffer>((resolve, reject) => {
    execFile(
      'python3', args,
      { cwd: CWD(), encoding: 'buffer', maxBuffer: 32 * 1024 * 1024 },
      (err, out, errOut) => {
        if (err) reject(new Error(errOut?.toString() || err.message))
        else resolve(out as Buffer)
      },
    )
  })
}

/** Rasterise a form-driven letter to page images (data URLs) for preview. */
export async function runEngineFormPreview(
  letterType: string,
  brand: string,
  values: Record<string, unknown>,
): Promise<{ pages: string[] }> {
  const args = [ENGINE, 'form-preview', letterType, brand, JSON.stringify(values)]
  return new Promise<{ pages: string[] }>((resolve, reject) => {
    execFile(
      'python3', args,
      { cwd: CWD(), maxBuffer: 64 * 1024 * 1024 },
      (err, out, errOut) => {
        if (err) reject(new Error(errOut || err.message))
        else resolve(JSON.parse(out) as { pages: string[] })
      },
    )
  })
}

/** Build a ZIP of every party's branded PDF; returns the ZIP bytes. */
export async function runEngineZip(
  files: UploadedFile[],
  opts: { brand: string; ddBsb: string; ddAccount: string },
): Promise<Buffer> {
  return withFiles(files, (paths) => {
    const args = [ENGINE, 'zip', opts.brand, opts.ddBsb, opts.ddAccount, ...paths]
    return new Promise<Buffer>((resolve, reject) => {
      execFile(
        'python3', args,
        { cwd: CWD(), encoding: 'buffer', maxBuffer: 64 * 1024 * 1024 },
        (err, out, errOut) => {
          if (err) reject(new Error(errOut?.toString() || err.message))
          else resolve(out as Buffer)
        },
      )
    })
  })
}
